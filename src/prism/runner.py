"""Safe subprocess wrapper for external analysis tools.

Safety properties (each is covered by a test or a code comment):
- argument list, never a shell string (no shell=True)
- hard timeout
- `python -I` (isolated mode) so the working directory is not added to the
  import path and PYTHONPATH/user-site are ignored
- the analyzed file is only ever *read* by the tools, never imported/run
"""

from __future__ import annotations

import importlib.metadata
import importlib.util
import subprocess
import sys
from pathlib import Path


class ToolError(Exception):
    """Base class for tool failures."""


class ToolMissingError(ToolError):
    pass


class ToolTimeoutError(ToolError):
    pass


class ToolExecutionError(ToolError):
    """Tool exited with an unexpected status or could not be started."""


class ToolOutputError(ToolError):
    """Tool ran but its output could not be parsed as expected."""


def tool_version(package: str) -> str | None:
    try:
        return importlib.metadata.version(package)
    except importlib.metadata.PackageNotFoundError:
        return None


def run_module(
    module: str,
    args: list[str],
    *,
    cwd: Path,
    timeout: float,
    ok_exit_codes: tuple[int, ...] = (0,),
) -> str:
    """Run `python -I -m <module> <args>` and return stdout."""
    if importlib.util.find_spec(module) is None:
        raise ToolMissingError(f"{module} is not installed in this Python environment.")
    cmd = [sys.executable, "-I", "-m", module, *args]
    return _run_process(cmd, module, cwd=cwd, timeout=timeout, ok_exit_codes=ok_exit_codes)


def run_python_callable(
    module: str,
    callable_name: str,
    args: list[str],
    *,
    cwd: Path,
    timeout: float,
    ok_exit_codes: tuple[int, ...] = (0,),
) -> str:
    """Run an installed Python console entry point without ``python -m``."""
    if importlib.util.find_spec(module) is None:
        raise ToolMissingError(f"{module} is not installed in this Python environment.")
    call = (
        "import importlib, sys; "
        f"sys.exit(getattr(importlib.import_module({module!r}), {callable_name!r})())"
    )
    cmd = [sys.executable, "-I", "-c", call, *args]
    return _run_process(cmd, module, cwd=cwd, timeout=timeout, ok_exit_codes=ok_exit_codes)


def _run_process(
    cmd: list[str],
    tool_name: str,
    *,
    cwd: Path,
    timeout: float,
    ok_exit_codes: tuple[int, ...],
) -> str:
    try:
        proc = subprocess.run(  # noqa: S603 - fixed argv list, no shell
            cmd,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            shell=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise ToolTimeoutError(f"{tool_name} timed out after {timeout:g}s.") from exc
    except OSError as exc:
        raise ToolExecutionError(f"Could not start {tool_name}: {exc}") from exc
    if proc.returncode not in ok_exit_codes:
        stderr = (proc.stderr or "").strip()[:500]
        raise ToolExecutionError(f"{tool_name} exited with status {proc.returncode}: {stderr}")
    return proc.stdout
