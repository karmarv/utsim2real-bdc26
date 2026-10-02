"""Parallel HTTP range downloads and split-zip access.

Three data hosts are used by this project and all accept HTTP Range requests:
  - Harvard Dataverse (UT-LUMPI, UT-V2X-Real-IC): split zip parts, STORED (uncompressed) members,
    signed S3 URLs obtained by following the access API redirect. About 1.5 MB/s per connection,
    so parts are fetched with many parallel range requests.
  - LUMPI vault (data.uni-hannover.de): 7-zip style raw split zips (`lidar.zip.001`, ...).
  - UCLA box.com (V2X-Real): single deflate zips behind `https://ucla.box.com/shared/static/<id>`.

A split zip is a plain byte concatenation of its parts, so `MultiPartFile` presents the parts as one
seekable file and `zipfile.ZipFile` works on top of it, for local parts and for remote parts alike.
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import threading
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Callable, Iterable, Sequence

import requests

DATAVERSE_ACCESS = "https://dataverse.harvard.edu/api/access/datafile/"
CHUNK = 32 * 1024 * 1024


# --------------------------------------------------------------------------------------------
# URL resolution
# --------------------------------------------------------------------------------------------
class Resolver:
    """Returns a (possibly short-lived) direct URL for a remote object; re-resolves on demand."""

    def __init__(self, fn: Callable[[], str], ttl_s: float = 1800.0):
        self._fn, self._ttl = fn, ttl_s
        self._url, self._t = None, 0.0
        self._lock = threading.Lock()

    def get(self, force: bool = False) -> str:
        with self._lock:
            if force or self._url is None or time.time() - self._t > self._ttl:
                self._url, self._t = self._fn(), time.time()
            return self._url


def dataverse_resolver(file_id: int) -> Resolver:
    def fn() -> str:
        r = requests.get(DATAVERSE_ACCESS + str(file_id), allow_redirects=False, timeout=60)
        if r.status_code in (301, 302, 303, 307, 308):
            return r.headers["Location"]
        r.raise_for_status()
        return DATAVERSE_ACCESS + str(file_id)
    return Resolver(fn)


def static_resolver(url: str) -> Resolver:
    def fn() -> str:
        r = requests.get(url, headers={"Range": "bytes=0-0"}, allow_redirects=True, timeout=60, stream=True)
        final = r.url
        r.close()
        return final
    return Resolver(fn, ttl_s=600.0)


def remote_size(res: Resolver) -> int:
    r = requests.get(res.get(), headers={"Range": "bytes=0-0"}, allow_redirects=True, timeout=60, stream=True)
    cr = r.headers.get("Content-Range", "")
    r.close()
    if "/" not in cr:
        raise RuntimeError(f"server did not honour a Range request: {res.get()[:80]}")
    return int(cr.rsplit("/", 1)[1])


def get_range(res: Resolver, start: int, end_incl: int, retries: int = 6) -> bytes:
    for attempt in range(retries):
        try:
            r = requests.get(res.get(force=attempt > 0), headers={"Range": f"bytes={start}-{end_incl}"},
                             timeout=300, allow_redirects=True)
            if r.status_code == 206 and len(r.content) == end_incl - start + 1:
                return r.content
            if r.status_code == 200 and start == 0 and len(r.content) == end_incl + 1:
                return r.content
        except requests.RequestException:
            pass
        time.sleep(min(2 ** attempt, 30))
    raise RuntimeError(f"range {start}-{end_incl} failed after {retries} attempts")


# --------------------------------------------------------------------------------------------
# Parallel, resumable download of one file
# --------------------------------------------------------------------------------------------
def md5_of(path: Path, bufsize: int = 16 * 1024 * 1024) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(bufsize), b""):
            h.update(block)
    return h.hexdigest()


def download(res: Resolver, dest: Path, size: int | None = None, md5: str | None = None,
             workers: int = 16, chunk: int = CHUNK, log: Callable[[str], None] = print) -> Path:
    """Download `res` to `dest` with `workers` parallel range requests. Resumable via a sidecar."""
    dest = Path(dest)
    if dest.exists() and (md5 is None or md5_of(dest) == md5):
        return dest
    size = size or remote_size(res)
    part, state = dest.with_suffix(dest.suffix + ".part"), dest.with_suffix(dest.suffix + ".chunks")
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not part.exists():
        with open(part, "wb") as f:
            f.truncate(size)
    done = set(json.loads(state.read_text())) if state.exists() else set()
    todo = [i for i in range((size + chunk - 1) // chunk) if i not in done]
    lock, t0, nbytes = threading.Lock(), time.time(), 0
    fd = os.open(part, os.O_WRONLY)

    def work(i: int) -> int:
        lo, hi = i * chunk, min(size, (i + 1) * chunk) - 1
        data = get_range(res, lo, hi)
        os.pwrite(fd, data, lo)
        return i

    try:
        with ThreadPoolExecutor(workers) as ex:
            for fut in as_completed([ex.submit(work, i) for i in todo]):
                i = fut.result()
                with lock:
                    done.add(i)
                    nbytes += min(chunk, size - i * chunk)
                    state.write_text(json.dumps(sorted(done)))
                    if len(done) % 16 == 0:
                        log(f"  {dest.name}: {len(done) * chunk / size:5.1%} at {nbytes / max(time.time() - t0, 1e-6) / 1e6:5.1f} MB/s")
    finally:
        os.close(fd)
    if md5 is not None and md5_of(part) != md5:
        state.unlink(missing_ok=True)
        raise RuntimeError(f"MD5 mismatch for {dest.name}; delete {part} and retry")
    part.rename(dest)
    state.unlink(missing_ok=True)
    return dest


# --------------------------------------------------------------------------------------------
# Split zips (local or remote parts) as one seekable file
# --------------------------------------------------------------------------------------------
class MultiPartFile(io.RawIOBase):
    """Byte concatenation of parts. A part is a local path or a (Resolver, size) pair."""

    def __init__(self, parts: Sequence[Path | tuple[Resolver, int]]):
        self.parts = list(parts)
        self.sizes = [p.stat().st_size if isinstance(p, Path) else p[1] for p in self.parts]
        self.offsets = [sum(self.sizes[:i]) for i in range(len(self.sizes))]
        self.size, self.pos = sum(self.sizes), 0
        self._fh: dict[int, io.BufferedReader] = {}

    def readable(self): return True
    def seekable(self): return True
    def tell(self): return self.pos

    def seek(self, off, whence=0):
        self.pos = off if whence == 0 else (self.pos + off if whence == 1 else self.size + off)
        return self.pos

    def _read_part(self, i: int, lo: int, n: int) -> bytes:
        p = self.parts[i]
        if isinstance(p, Path):
            fh = self._fh.get(i) or self._fh.setdefault(i, open(p, "rb"))
            fh.seek(lo)
            return fh.read(n)
        return get_range(p[0], lo, lo + n - 1)

    def readinto(self, b) -> int:
        n = min(len(b), self.size - self.pos)
        if n <= 0:
            return 0
        out, start, left = bytearray(), self.pos, n
        while left > 0:
            i = max(k for k in range(len(self.offsets)) if self.offsets[k] <= start)
            lo = start - self.offsets[i]
            take = min(left, self.sizes[i] - lo)
            out += self._read_part(i, lo, take)
            start += take
            left -= take
        b[:n] = out
        self.pos += n
        return n

    def close(self):
        for fh in self._fh.values():
            fh.close()
        super().close()


def open_zip(parts: Sequence[Path | tuple[Resolver, int]], buffer: int = 4 * 1024 * 1024) -> zipfile.ZipFile:
    return zipfile.ZipFile(io.BufferedReader(MultiPartFile(parts), buffer_size=buffer))


def extract_members(open_zip_fn: Callable[[], zipfile.ZipFile], names: Iterable[str], out_dir: Path,
                    workers: int = 8, strip_prefix: str = "", log: Callable[[str], None] = print) -> int:
    """Extract `names` with `workers` threads, each owning its own ZipFile. Skips existing files."""
    out_dir = Path(out_dir)
    names = [n for n in names if not n.endswith("/")]
    todo = [n for n in names if not (out_dir / n[len(strip_prefix):]).exists()]
    local = threading.local()

    def work(name: str) -> str:
        if not hasattr(local, "zf"):
            local.zf = open_zip_fn()
        target = out_dir / name[len(strip_prefix):]
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_suffix(target.suffix + ".tmp")
        with local.zf.open(name) as src, open(tmp, "wb") as dst:
            while block := src.read(4 * 1024 * 1024):
                dst.write(block)
        tmp.rename(target)
        return name

    t0 = time.time()
    with ThreadPoolExecutor(workers) as ex:
        for k, fut in enumerate(as_completed([ex.submit(work, n) for n in todo]), 1):
            fut.result()
            if k % 500 == 0 or k == len(todo):
                log(f"  extracted {k}/{len(todo)} ({k / max(time.time() - t0, 1e-6):.1f} files/s)")
    return len(todo)


def dataverse_parts(listing_json: Path) -> list[dict]:
    """Parts of a Dataverse split zip, sorted by filename: [{id, filename, size, md5}]."""
    files = json.loads(Path(listing_json).read_text())["data"]
    parts = [{"id": f["dataFile"]["id"], "filename": f["dataFile"]["filename"],
              "size": f["dataFile"]["filesize"], "md5": f["dataFile"].get("md5")} for f in files]
    return sorted(parts, key=lambda p: p["filename"])
