from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any, Iterable, Optional


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_json(path: Path, payload: Any) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    # Windows-created JSON files may include BOM, so use utf-8-sig for robustness.
    return json.loads(path.read_text(encoding="utf-8-sig"))


def stable_hash(parts: Iterable[str]) -> str:
    digest = hashlib.sha256()
    for part in parts:
        digest.update(part.encode("utf-8"))
        digest.update(b"|")
    return digest.hexdigest()


def which(binary: str) -> Optional[str]:
    return shutil.which(binary)


def run_cmd(command: list[str], cwd: Optional[Path] = None, input_text: Optional[str] = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=str(cwd) if cwd else None,
        text=True,
        input=input_text,
        capture_output=True,
        check=False,
    )
