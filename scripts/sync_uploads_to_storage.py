#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import os
import re
import shutil
from pathlib import Path

ALLOWED_FOLDERS = ("profiles", "businesses", "portfolio")
FILE_RE = re.compile(r"^[a-f0-9]{32,40}\.(?:jpg|png|webp)$")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sync(source_root: Path, target_root: Path) -> tuple[int, int, int]:
    source_root = source_root.resolve()
    target_root = target_root.resolve()
    target_root.mkdir(parents=True, exist_ok=True, mode=0o750)
    copied = skipped = conflicts = 0

    for folder in ALLOWED_FOLDERS:
        source_dir = source_root / folder
        target_dir = target_root / folder
        target_dir.mkdir(parents=True, exist_ok=True, mode=0o750)
        if not source_dir.is_dir():
            continue
        for source in source_dir.iterdir():
            if not source.is_file() or not FILE_RE.fullmatch(source.name):
                continue
            target = target_dir / source.name
            if target.exists():
                if target.is_file() and source.stat().st_size == target.stat().st_size and sha256(source) == sha256(target):
                    skipped += 1
                    continue
                conflicts += 1
                print(f"CONFLICT {source.relative_to(source_root)} (target differs; not overwritten)")
                continue
            temp = target_dir / f".{source.name}.copying"
            try:
                shutil.copyfile(source, temp)
                os.chmod(temp, 0o640)
                os.replace(temp, target)
                copied += 1
            finally:
                temp.unlink(missing_ok=True)
    return copied, skipped, conflicts


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Safely copy legacy LocalConnect user images into configured persistent storage.")
    parser.add_argument("--source", default=str(project_root / "uploads"))
    parser.add_argument("--target", default=os.getenv("UPLOAD_STORAGE_ROOT", ""))
    args = parser.parse_args()
    if not args.target:
        raise SystemExit("UPLOAD_STORAGE_ROOT (or --target) is required.")
    copied, skipped, conflicts = sync(Path(args.source), Path(args.target))
    print(f"copied={copied} skipped={skipped} conflicts={conflicts}")
    return 2 if conflicts else 0


if __name__ == "__main__":
    raise SystemExit(main())
