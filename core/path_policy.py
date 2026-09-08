"""Import path policy (Phase D security closure).

Web-triggered path-based imports must not grant unrestricted read access to
the server's file system.  A client-supplied path is only accepted when its
CANONICAL location (``Path.resolve()``: absolute, dot/separator-normalized,
symlinks/junctions followed where the platform can resolve them) is inside
one of the explicitly configured import roots.

Containment uses ``os.path.commonpath`` over ``os.path.normcase``d canonical
strings, so case-spelling variants (Windows) and different drives are handled
correctly.  Raw prefix checks against client input are never used — ``..``,
mixed separators, relative paths and link escapes are all resolved away
BEFORE the containment decision.

Trust boundary (deliberate):
- CLI  (``scripts/import_document.py``) runs as the local user and keeps
  unrestricted paths: no policy attached.
- Web  (``desktop/web_server.py`` → ``LibraryService``) attaches a policy;
  with no ``LIBRARY_IMPORT_ROOTS`` configured the policy denies everything,
  i.e. web path import is DISABLED by default.
"""

from __future__ import annotations

from pathlib import Path
import os
from typing import Iterable


class ImportPathPolicyError(ValueError):
    """Client-supplied path rejected by the import-root policy."""


def canonical_source_path(source: Path | str) -> Path:
    """Canonical client path: absolute, normalized, links followed."""
    return Path(str(source)).expanduser().resolve()


def _norm(value: Path) -> str:
    return os.path.normcase(str(value))


def _contained(resolved: Path, root: Path) -> bool:
    child = _norm(resolved)
    base = _norm(root)
    if child == base:
        return True
    try:
        return os.path.commonpath([child, base]) == base
    except ValueError:  # different drives, mixed abs/rel — never contained
        return False


class ImportPathPolicy:
    """Containment policy over canonical import roots."""

    def __init__(self, roots: Iterable[Path | str] = ()):
        canonical: list[Path] = []
        for root in roots or ():
            candidate = canonical_source_path(root)
            if candidate not in canonical:
                canonical.append(candidate)
        self.roots: tuple[Path, ...] = tuple(canonical)

    def __len__(self) -> int:
        return len(self.roots)

    def check(self, source: Path | str, *, purpose: str = "import") -> Path:
        """Return the canonical path when allowed; raise ImportPathPolicyError.

        The error message intentionally does not echo the configured roots:
        it must be safe to return to a Web client without disclosing server
        directories.
        """
        resolved = canonical_source_path(source)
        if not self.roots:
            raise ImportPathPolicyError(
                f"Web {purpose} 已禁用：未配置 LIBRARY_IMPORT_ROOTS 导入目录。"
                "如需启用，请在服务端配置明确的导入根目录后重启服务。"
            )
        if not any(_contained(resolved, root) for root in self.roots):
            raise ImportPathPolicyError(
                f"{purpose} 路径不在允许的导入目录内，已拒绝。"
                "请将文件放入服务端配置的导入目录，或由本机用户通过 CLI 导入。"
            )
        return resolved

    def display_relative(self, source: Path | str) -> str | None:
        """Root-relative display path when inside a configured root, else None."""
        try:
            resolved = canonical_source_path(source)
        except OSError:
            return None
        for root in self.roots:
            if _contained(resolved, root):
                base = _norm(root)
                child = _norm(resolved)
                if child == base:
                    return ""
                # slice the normcased strings; re-slash for display
                return child[len(base) + 1 :].replace("\\", "/")
        return None


def policy_from_roots_value(value: str | None) -> ImportPathPolicy:
    """Parse a ``LIBRARY_IMPORT_ROOTS``-style value (os.pathsep separated)."""
    if not value:
        return ImportPathPolicy(())
    roots = [item.strip() for item in value.split(os.pathsep) if item.strip()]
    return ImportPathPolicy(roots)
