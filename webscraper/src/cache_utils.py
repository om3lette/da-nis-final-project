import hashlib
import json
import os
from pathlib import Path
from urllib.parse import urlparse, ParseResult

import aiofiles

from constants import CACHE_DIR, OUT_DIR


def url_to_filename_hash(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()

def get_out_path(url: str) -> Path:
    parsed: ParseResult = urlparse(url)
    dir_path: Path = OUT_DIR / f"{parsed.netloc}{parsed.path.replace('/', '_')}"
    os.makedirs(dir_path, exist_ok=True)
    return dir_path

def _get_cache_path(url: str, filename: str = "") -> Path:
    path: Path = CACHE_DIR / url_to_filename_hash(url)
    os.makedirs(path, exist_ok=True)

    if filename != "":
        path = path / filename
    return path

def _get_cache_path_source(url: str, timestamp: str, extension: str) -> Path:
    return _get_cache_path(url) / f"{timestamp}.{extension}"

async def store_timestamps(url: str, timestamps: list[str]):
    async with aiofiles.open(_get_cache_path(url, "timestamps.json"), "w") as f:
        await f.write(json.dumps(timestamps))

async def load_timestamps(url: str) -> list[str] | None:
    timestamp_file: Path = _get_cache_path(url, "timestamps.json")
    if not timestamp_file.exists():
        return None

    async with aiofiles.open(timestamp_file, "r") as f:
        return json.loads(await f.read())

async def store_page_source(html: str, url: str, timestamp: str) -> None:
    async with aiofiles.open(_get_cache_path_source(url, timestamp, "html"), "w") as f:
        await f.write(html)

async def load_page_source(url: str, timestamp: str) -> str | None:
    page_source_file: Path = _get_cache_path_source(url, timestamp, "html")
    if not page_source_file.exists():
        return None

    async with aiofiles.open(page_source_file, "r") as f:
        return await f.read()
