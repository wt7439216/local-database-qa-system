import os
import subprocess
import sys
from collections.abc import Sequence
from os import PathLike

from core import config


def configure_console_encoding() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def run_command(cmd: Sequence[str | PathLike[str]], description: str) -> bool:
    print(f"\n{'='*50}")
    print(description)
    print(f"{'='*50}")

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    command = [
        os.fspath(part) if isinstance(part, PathLike) else str(part)
        for part in cmd
    ]

    try:
        result = subprocess.run(
            command,
            shell=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
        )
    except OSError as exc:
        print(f"[失败] 无法启动命令：{exc}")
        return False

    if result.returncode != 0:
        print(f"[失败] {result.stderr}")
        return False
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)
    return True


def run_python_script(script: str | PathLike[str], description: str, *args: str) -> bool:
    return run_command(
        [sys.executable, os.fspath(script), *args],
        description,
    )


def main() -> int:
    configure_console_encoding()

    if not run_command(["ollama", "list"], "步骤0：检查模型"):
        return 1

    if not run_python_script(
        config.ROOT_DIR / "scripts" / "pdf_to_book_txt.py",
        "步骤1：提取教材文本",
    ):
        return 1

    if not run_python_script(
        config.ROOT_DIR / "scripts" / "build_library.py",
        "步骤2：构建并验证结构化教材库",
    ):
        return 1

    print("\n重建完成！现在可以运行：")
    print(f'"{sys.executable}" -m desktop')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
