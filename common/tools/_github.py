"""Minimal GitHub REST client for release assets (standard library only; the GitHub CLI is not required).

Token: $GITHUB_TOKEN or $GH_TOKEN, else typed at a hidden prompt (never echoed, never written anywhere). The repository
is private, so downloads need a token with read access too; publishing needs contents write access.
"""
import getpass
import json
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://api.github.com"
_TOKEN = None


def slug_from_url(url: str) -> str:
    """owner/repo from an https or ssh GitHub remote URL."""
    slug = url.strip().split("github.com", 1)[1].lstrip(":/")
    return slug[:-4] if slug.endswith(".git") else slug


def repo_slug(repo_dir: Path) -> str:
    return slug_from_url(subprocess.run(["git", "-C", str(repo_dir), "remote", "get-url", "origin"], capture_output=True, text=True,
                                        check=True).stdout)


def token() -> str:
    global _TOKEN
    if _TOKEN is None:
        _TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or getpass.getpass("GitHub token (not echoed): ").strip()
        if not _TOKEN:
            raise SystemExit("no GitHub token")
    return _TOKEN


def _headers(extra: dict | None = None) -> dict:
    h = {"Authorization": f"Bearer {token()}", "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28",
         "User-Agent": "utsim2real-bdc26-release"}
    h.update(extra or {})
    return h


def api(method: str, url: str, body: dict | None = None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url if url.startswith("http") else API + url, data=data, method=method,
                                 headers=_headers({"Content-Type": "application/json"} if data else None))
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            raw = r.read()
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise SystemExit(f"GitHub API {method} {url}: {e.code} {e.read().decode(errors='replace')[:400]}")


def release(slug: str, tag: str):
    return api("GET", f"/repos/{slug}/releases/tags/{urllib.parse.quote(tag)}")


def create_or_update_release(slug: str, tag: str, name: str, body: str, prerelease: bool = True) -> dict:
    r = release(slug, tag)
    if r is None:
        return api("POST", f"/repos/{slug}/releases", {"tag_name": tag, "name": name, "body": body, "prerelease": prerelease, "draft": False})
    return api("PATCH", f"/repos/{slug}/releases/{r['id']}", {"name": name, "body": body, "prerelease": prerelease})


class _Progress:
    def __init__(self, f, total: int, label: str):
        self.f, self.total, self.label, self.done, self.next = f, total, label, 0, 0.1

    def read(self, n=-1):
        b = self.f.read(n)
        self.done += len(b)
        if self.total and self.done / self.total >= self.next:
            print(f"  {self.label}: {100 * self.done / self.total:.0f}%", file=sys.stderr, flush=True)
            self.next += 0.1
        return b


def upload_asset(rel: dict, name: str, path: Path) -> dict:
    size = path.stat().st_size
    for a in rel.get("assets", []):
        if a["name"] == name:
            if a["size"] == size and a.get("state") == "uploaded":
                print(f"  {name}: already uploaded ({size} bytes)")
                return a
            api("DELETE", a["url"])
    url = rel["upload_url"].split("{", 1)[0] + "?" + urllib.parse.urlencode({"name": name})
    with open(path, "rb") as f:
        req = urllib.request.Request(url, data=_Progress(f, size, name), method="POST",
                                     headers=_headers({"Content-Type": "application/octet-stream", "Content-Length": str(size)}))
        try:
            with urllib.request.urlopen(req, timeout=3600) as r:
                a = json.loads(r.read())
        except urllib.error.HTTPError as e:
            raise SystemExit(f"upload of {name} failed: {e.code} {e.read().decode(errors='replace')[:400]}")
    print(f"  {name}: uploaded ({size} bytes)")
    return a


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def download_asset(asset: dict, dest: Path) -> None:
    """Asset download: the API answers with a redirect to a signed URL, fetched without the token."""
    req = urllib.request.Request(asset["url"], headers=_headers({"Accept": "application/octet-stream"}))
    opener = urllib.request.build_opener(_NoRedirect)
    try:
        r = opener.open(req, timeout=120)
        target = None
    except urllib.error.HTTPError as e:
        if e.code not in (301, 302, 303, 307, 308):
            raise SystemExit(f"download of {asset['name']} failed: {e.code}")
        target = e.headers["Location"]
    src = urllib.request.urlopen(urllib.request.Request(target, headers={"User-Agent": "utsim2real-bdc26-release"}), timeout=3600) if target else r
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(dest.name + ".part")
    with src, open(tmp, "wb") as f:
        while True:
            b = src.read(1 << 22)
            if not b:
                break
            f.write(b)
    tmp.replace(dest)
