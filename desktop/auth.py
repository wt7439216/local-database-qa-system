"""Pairing/token authentication and Host-header policy (P1 extraction)."""
from __future__ import annotations

import hmac
import ipaddress
import logging
import secrets
import socket
import threading
import time

from core import config

TOKEN_LIFETIME_SECONDS = config.SETTINGS.token_lifetime_seconds
AUTH_FAILURE_LIMIT = config.SETTINGS.auth_failure_limit
AUTH_BLOCK_SECONDS = config.SETTINGS.auth_block_seconds
AUTH_FAILURE_RETENTION_SECONDS = config.SETTINGS.auth_failure_retention_seconds
LOOPBACK_BIND = {"127.0.0.1", "localhost", "::1"}


def create_pairing_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def discover_lan_addresses() -> list[str]:
    """Enumerate private local IPv4 addresses without contacting external hosts."""
    candidates: list[str] = []
    try:
        candidates.extend(
            str(info[4][0])
            for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET)
        )
    except OSError as exc:
        logging.getLogger(__name__).debug("local address discovery failed: %s", exc)
    addresses: list[str] = []
    for candidate in candidates:
        try:
            address = ipaddress.ip_address(candidate)
        except ValueError:
            continue
        if (isinstance(address, ipaddress.IPv4Address) and address.is_private
                and not address.is_loopback and not address.is_link_local
                and candidate not in addresses):
            addresses.append(candidate)
    return addresses


class AuthManager:
    """Owns tokens and per-IP pairing failure state."""

    def __init__(self, pairing_code: str) -> None:
        if len(pairing_code) != 6 or not pairing_code.isdigit():
            raise ValueError("配对码必须是 6 位数字。")
        self.pairing_code = pairing_code
        self.tokens: dict[str, float] = {}
        self.failures: dict[str, tuple[int, float, float]] = {}
        self.lock = threading.Lock()

    def pair(self, code: str, client_ip: str) -> tuple[str | None, int]:
        valid, retry_after = self.check_pairing_code(code, client_ip)
        if not valid:
            return None, retry_after
        token = secrets.token_urlsafe(32)
        with self.lock:
            self.tokens[token] = time.time() + TOKEN_LIFETIME_SECONDS
        return token, 0

    def authorized(self, authorization: str) -> bool:
        if not authorization.startswith("Bearer "):
            return False
        token = authorization[7:].strip()
        now = time.time()
        with self.lock:
            for key in [key for key, expiry in self.tokens.items() if expiry <= now]:
                self.tokens.pop(key, None)
            expiry = self.tokens.get(token, 0)
        return expiry > now

    def check_pairing_code(self, code: str, client_ip: str) -> tuple[bool, int]:
        now = time.time()
        with self.lock:
            stale = [
                key for key, value in self.failures.items()
                if value[2] < now - AUTH_FAILURE_RETENTION_SECONDS
            ]
            for key in stale:
                self.failures.pop(key, None)
            failures, blocked_until, _updated = self.failures.get(client_ip, (0, 0.0, 0.0))
            if blocked_until > now:
                return False, max(1, int(blocked_until - now + 0.999))
            if hmac.compare_digest(self.pairing_code, str(code or "")):
                self.failures.pop(client_ip, None)
                return True, 0
            failures = 1 if blocked_until else failures + 1
            blocked_until = now + AUTH_BLOCK_SECONDS if failures >= AUTH_FAILURE_LIMIT else 0.0
            self.failures[client_ip] = (failures, blocked_until, now)
            return False, AUTH_BLOCK_SECONDS if blocked_until else 0


class HostPolicy:
    """DNS-rebinding defence: only accept known local Host header values."""

    def __init__(self) -> None:
        self._cache: tuple[float, set[str]] = (0.0, set())

    def allowed(self, bind_host: str, port: int) -> set[str]:
        computed_at, cached = self._cache
        now = time.time()
        if cached and now - computed_at < 10:
            return cached
        hostname = socket.gethostname().lower()
        names = {"127.0.0.1", "localhost", "[::1]", hostname}
        if bind_host not in LOOPBACK_BIND:
            names.update(discover_lan_addresses())
        hosts = names | {f"{name}:{port}" for name in names}
        self._cache = (now, hosts)
        return hosts
