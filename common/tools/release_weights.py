#!/usr/bin/env python
"""The model weights of a release as GitHub release assets, with a committed manifest for traceability.

    # maintainer: write the manifest of the checkpoints (and zips) behind the release's leaderboard versions
    python common/tools/release_weights.py collect --tag 6.0 model-lumpi-track/routed-g8:s6 model-v2x-track/routed-g8b:s6b
    # maintainer: create the GitHub pre-release of the pushed tag (notes: its RELEASES.md section) and upload the assets
    python common/tools/release_weights.py publish --tag 6.0
    # the same as a full release (not marked pre-release; title "<tag>"), e.g. the ranked final-phase entries
    python common/tools/release_weights.py publish --tag 10.1 --final
    # anyone with read access: download, verify (md5) and place the checkpoints of one version, or of all
    python common/tools/release_weights.py fetch --tag 6.0 [--version lumpi:s6]
    python common/tools/release_weights.py verify --tag 6.0        # md5 of the files in place against the manifest

Manifest: releases/<tag>/weights.json (in git). For every asset its name, repository path, md5, size and the versions
that use it; for every version its model folder, submission zip, CodaBench id and leaderboard score, and its
reproduction scripts. Checkpoint assets are named <track>.<model folder>.epoch40.pth and go back to
model-<track>/<model>/train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth (git-ignored), the paths every
model.yaml, decision record and test/reproduce_<tag>.sh refer to. Fetching from a public repository needs no token; for
publishing (or a private repository) the GitHub token is read from $GITHUB_TOKEN or
$GH_TOKEN or typed at a hidden prompt (common/tools/_github.py); the repository is private, so fetching needs one too.
"""
import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

from _common import REPO, model_info

CK = "train/output/pcdet_model/run1/ckpt/checkpoint_epoch_40.pth"


def md5(p: Path) -> str:
    h = hashlib.md5()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


def manifest_path(tag: str) -> Path:
    return REPO / "releases" / tag / "weights.json"


def zip_assets(zips: list[dict]) -> list[dict]:
    """Release asset names of the scored zips. A file name that several versions share (S10 uploads every version as
    <track>_s10_submission.zip) is qualified as <track>.<model folder>.<submission tag>.<file name>, since the assets of
    one GitHub release need unique names; `path` still places each file at its repository path."""
    from collections import Counter
    n = Counter(z["name"] for z in zips)
    out = []
    for z in zips:
        z = dict(z)
        q = z.pop("qualified")
        if n[z["name"]] > 1:
            z["name"] = q
        out.append(z)
    return out


def collect(tag: str, specs: list[str]) -> dict:
    from reproduce_submission import members_inventory, scored_zip
    assets, versions, zips = {}, [], []
    for spec in specs:
        md, vtag = spec.rsplit(":", 1)
        model_dir, card, track = model_info(md)
        t = track.name.replace("-track", "")
        zpath, man = scored_zip(model_dir, vtag)
        rows = members_inventory(model_dir, card, {})
        vname = f"{t}:{vtag}"
        for r in rows:
            for s in (r["bag"] if "bag" in r else [r]):
                p = REPO / s["ckpt"]
                model = Path(s["ckpt"]).parts[1]
                name = f"{t}.{model}.epoch40.pth"
                a = assets.setdefault(name, {"name": name, "kind": "checkpoint", "path": s["ckpt"], "md5": s["md5"] or md5(p),
                                             "bytes": p.stat().st_size, "used_by": []})
                if a["path"] != s["ckpt"]:
                    raise SystemExit(f"asset name clash: {name} for {a['path']} and {s['ckpt']}")
                if vname not in a["used_by"]:
                    a["used_by"].append(vname)
        zrel = str(zpath.relative_to(REPO))
        zips.append({"name": zpath.name, "qualified": f"{t}.{model_dir.name}.{vtag}.{zpath.name}", "kind": "submission", "path": zrel,
                     "md5": md5(zpath), "bytes": zpath.stat().st_size, "used_by": [vname]})
        lb = man.get("leaderboard") or {}
        rel = model_dir.relative_to(REPO)
        versions.append({"version": vname, "model": str(rel), "strategy": card.get("strategy"), "submission_zip": zrel,
                         "zip_md5": man.get("upload_file", {}).get("md5") or man.get("zip_md5"),
                         "codabench_id": man.get("codabench_submission_id"), "leaderboard_combined": lb.get("score_combined"),
                         "reproduce_test": f"{rel}/test/reproduce_{vtag}.sh", "reproduce_validation": f"{rel}/test/reproduce_{vtag}_validation.sh",
                         "checkpoints": sorted(n for n, a in assets.items() if a["kind"] == "checkpoint" and vname in a["used_by"])})
    assets.update({z["name"]: z for z in zip_assets(zips)})
    import _github
    out = {"tag": tag, "repository": _github.repo_slug(REPO), "created": time.strftime("%Y-%m-%d"), "versions": versions,
           "assets": sorted(assets.values(), key=lambda a: (a["kind"], a["name"])),
           "total_bytes": sum(a["bytes"] for a in assets.values())}
    p = manifest_path(tag)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out, indent=2) + "\n")
    print(f"wrote {p.relative_to(REPO)}: {len(assets)} assets, {out['total_bytes'] / 1e9:.2f} GB")
    return out


def notes(tag: str, slug: str | None = None) -> str:
    """The release's RELEASES.md section; relative links become links to the files at the tag on GitHub."""
    import re
    lines, on = [], False
    for line in (REPO / "RELEASES.md").read_text().splitlines():
        if line.startswith("## "):
            if on:
                break
            on = line.startswith(f"## {tag} ")
        if on:
            lines.append(line)
    if not lines:
        raise SystemExit(f"no '## {tag} ' section in RELEASES.md")
    body = "\n".join(lines[1:]).strip() + f"\n\nWeights and reproduction: `releases/{tag}/weights.json`, `python common/tools/release_weights.py fetch --tag {tag}`.\n"
    if slug:
        body = re.sub(r"\]\((?!https?://|#)([^)\s]+)\)", lambda m_: f"](https://github.com/{slug}/blob/{tag}/{m_.group(1)})", body)
    return body


def release_title(tag: str, title: str | None, final: bool) -> str:
    """The GitHub release name: the given title, else '<tag>' for a full release and '<tag> (pre-release)' otherwise."""
    return title or (tag if final else f"{tag} (pre-release)")


def publish(tag: str, title: str | None, final: bool = False) -> None:
    import _github
    m = json.loads(manifest_path(tag).read_text())
    for a in m["assets"]:
        p = REPO / a["path"]
        if not p.exists() or p.stat().st_size != a["bytes"]:
            raise SystemExit(f"{a['path']}: missing or size differs from the manifest")
    rel = _github.create_or_update_release(m["repository"], tag, release_title(tag, title, final), notes(tag, m["repository"]),
                                           prerelease=not final)
    print(f"release {tag}: {rel['html_url']}")
    for k, a in enumerate(m["assets"], 1):
        print(f"[{k}/{len(m['assets'])}] {a['name']} ({a['bytes'] / 1e6:.1f} MB)", flush=True)
        _github.upload_asset(rel, a["name"], REPO / a["path"])
    rel = _github.release(m["repository"], tag)
    have = {a["name"]: a["size"] for a in rel["assets"]}
    bad = [a["name"] for a in m["assets"] if have.get(a["name"]) != a["bytes"]]
    print("all assets uploaded and sizes match" if not bad else f"MISSING or wrong size: {bad}")
    sys.exit(1 if bad else 0)


def selected(m: dict, version: str | None) -> list[dict]:
    if not version:
        return m["assets"]
    v = next((v for v in m["versions"] if v["version"] == version), None)
    if v is None:
        raise SystemExit(f"unknown version {version}; the manifest has {[v['version'] for v in m['versions']]}")
    return [a for a in m["assets"] if version in a["used_by"]]


def fetch(tag: str, version: str | None, force: bool) -> None:
    import _github
    m = json.loads(manifest_path(tag).read_text())
    rel = None
    for a in selected(m, version):
        p = REPO / a["path"]
        if p.exists() and not force and md5(p) == a["md5"]:
            print(f"{a['path']}: present, md5 ok")
            continue
        if rel is None:
            rel = _github.release(m["repository"], tag, required=False)      # a public repository: no token needed
            if rel is None:
                rel = _github.release(m["repository"], tag)                   # a private one: asks for a token
            if rel is None:
                raise SystemExit(f"no GitHub release {tag} in {m['repository']} (or the token cannot read it)")
            by_name = {x["name"]: x for x in rel["assets"]}
        if a["name"] not in by_name:
            raise SystemExit(f"release {tag} has no asset {a['name']}")
        print(f"{a['name']} -> {a['path']} ({a['bytes'] / 1e6:.1f} MB)", flush=True)
        _github.download_asset(by_name[a["name"]], p)
        got = md5(p)
        if got != a["md5"]:
            raise SystemExit(f"{a['path']}: md5 {got} differs from the manifest {a['md5']}")
    print("fetched and verified")


def verify(tag: str, version: str | None) -> None:
    m = json.loads(manifest_path(tag).read_text())
    bad = 0
    for a in selected(m, version):
        p = REPO / a["path"]
        ok = p.exists() and md5(p) == a["md5"]
        bad += not ok
        print(f"{'ok     ' if ok else 'MISSING' if not p.exists() else 'DIFFERS'} {a['path']}")
    sys.exit(1 if bad else 0)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("collect"); c.add_argument("--tag", required=True); c.add_argument("versions", nargs="+", help="<model folder>:<submission tag>")
    p = sub.add_parser("publish"); p.add_argument("--tag", required=True); p.add_argument("--title", default=None)
    p.add_argument("--final", action="store_true", help="a full release instead of a pre-release (an existing release is updated)")
    f = sub.add_parser("fetch"); f.add_argument("--tag", required=True); f.add_argument("--version", default=None); f.add_argument("--force", action="store_true")
    v = sub.add_parser("verify"); v.add_argument("--tag", required=True); v.add_argument("--version", default=None)
    a = ap.parse_args()
    if a.cmd == "collect":
        collect(a.tag, a.versions)
    elif a.cmd == "publish":
        publish(a.tag, a.title, a.final)
    elif a.cmd == "fetch":
        fetch(a.tag, a.version, a.force)
    else:
        verify(a.tag, a.version)


if __name__ == "__main__":
    main()
