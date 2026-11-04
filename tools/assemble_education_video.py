"""Assemble the original educational MP4 from GitHub-safe source chunks during Pages builds."""
from __future__ import annotations

import hashlib
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "assets" / "media"
OUTPUT_DIR = ROOT / "_site" / "assets" / "media"
EXPECTED_SHA256 = "29df8199188864a5fc7f4d1f4d401cf04a42d24dc4cf16f575a0486769b82016"
EXPECTED_PARTS = 12


def assemble_education_video() -> Path:
    parts = sorted(SOURCE_DIR.glob("education-overview.part[0-9][0-9]"))
    if len(parts) != EXPECTED_PARTS:
        raise RuntimeError(f"Missing education video parts: {len(parts)} of {EXPECTED_PARTS}")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    target = OUTPUT_DIR / "education-overview.mp4"
    digest = hashlib.sha256()
    with target.open("wb") as output:
        for part in parts:
            with part.open("rb") as source:
                while chunk := source.read(1024 * 1024):
                    output.write(chunk)
                    digest.update(chunk)
    if digest.hexdigest() != EXPECTED_SHA256:
        target.unlink(missing_ok=True)
        raise RuntimeError("Education video integrity check failed")
    # The published site needs only the finished MP4, not the Git source chunks.
    for part in OUTPUT_DIR.glob("education-overview.part[0-9][0-9]"):
        part.unlink()
    return target


if __name__ == "__main__":
    print(assemble_education_video())
