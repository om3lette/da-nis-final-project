import os
from pathlib import Path

PROJECT_ROOT: Path = Path(__file__).parents[1]

CONFIG_PATH: Path = PROJECT_ROOT / "config.yaml"

GEN_DIR: Path = PROJECT_ROOT / "gen"
OUT_DIR: Path = GEN_DIR / "out"
CACHE_DIR: Path = GEN_DIR / "cache"

os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)
