#!/usr/bin/env python
"""Public export of the challenge line (branch main) for the code release, with a leak check against the research line.

    python synth-common/tools/export_public.py --out /path/to/export                          # branch main (default)
    python synth-common/tools/export_public.py --ref 6.0 --out /path/to/export                # a tag or commit
    ... --public-repo owner/name     # point the weight manifests, clone lines and links at the public repository

The repository has two branches: `main` holds the challenge entries only; `synth-cv` adds the research line, and only
under synth-* paths (synth-docs/README.md). The challenge asks the top teams to release their code, and the research
must stay private while the CVPR paper is under review (synth-paper/README.md). This tool turns a committed ref (main
by default) into a plain tree for a NEW public repository, with no git history:
  1. drops every path under synth-* (empty for main; a safety net for any other ref);
  2. drops every Markdown line that mentions the research line (none expected on main);
  3. with --public-repo, rewrites the private repository's name (releases/<tag>/weights.json, clone lines, links) to
     the public one, so that `release_weights.py fetch` works there once the weights are published to it;
  4. scans every text file of the result for the research line's names and refuses (exit 1) if anything is left.
Nothing is pushed. Never make this repository (or the synth-cv branch) public: its history holds the research.
"""
import argparse
import re
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DROP_PATH = re.compile(r"^synth-[^/]+/")
LINE = re.compile(r"synth-|synthtwin|synth-cv|RESEARCH-AGENDA|research agenda|synth research|synth line|Calibrated Twin Distributions|\bCTD\b",
                  re.IGNORECASE)
LEAK = re.compile(r"synth-common|synth-lumpi|synth-v2x|synth-paper|synth-docs|synth-tumtraf|synth-cv|synthtwin|RESEARCH-AGENDA|"
                  r"Calibrated Twin Distributions|TSNPE|Sourcerer|paired multi-render|research agenda|\bscribe\b|annotator twin",
                  re.IGNORECASE)
TEXT = {".md", ".py", ".sh", ".yaml", ".yml", ".json", ".txt", ".csv", ".cfg", ".toml"}
PRIVATE_SLUG = "karmarv/utsim2real-bdc26"


def export(out: Path, ref: str, public_repo: str | None = None) -> int:
    if out.exists() and any(out.iterdir()):
        raise SystemExit(f"{out} is not empty")
    out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        tar = Path(tmp) / "src.tar"
        subprocess.run(["git", "-C", str(REPO), "archive", "--format=tar", "-o", str(tar), ref], check=True)
        with tarfile.open(tar) as t:
            names = [m.name for m in t.getmembers() if m.isfile()]
            kept = [n for n in names if not DROP_PATH.match(n)]
            for n in kept:
                t.extract(n, out)
    dropped_lines = 0
    for f in kept:
        p = out / f
        if p.suffix != ".md":
            continue
        with open(p, newline="") as fh:                  # newline="": line endings stay as they are
            text = fh.read()
        lines = text.split("\n")
        keep = [l for l in lines if not LINE.search(l)]
        if len(keep) != len(lines):
            dropped_lines += len(lines) - len(keep)
            with open(p, "w", newline="") as fh:
                fh.write("\n".join(keep))
    renamed = 0
    if public_repo:
        for f in kept:
            p = out / f
            if p.suffix in TEXT and p.stat().st_size < 20_000_000:
                b = p.read_bytes()                       # bytes: keeps CRLF files (registry.csv) as they are
                if PRIVATE_SLUG.encode() in b:
                    p.write_bytes(b.replace(PRIVATE_SLUG.encode(), public_repo.encode()))
                    renamed += 1
    leaks = []
    for f in kept:
        p = out / f
        if p.suffix in TEXT and p.stat().st_size < 20_000_000:
            for k, l in enumerate(p.read_text(errors="ignore").split("\n"), 1):
                if LEAK.search(l):
                    leaks.append(f"{f}:{k}: {l[:120]}")
    print(f"exported {len(kept)} files of {ref} to {out}; dropped {len(names) - len(kept)} synth-* files and {dropped_lines} Markdown lines"
          + (f"; repository name rewritten in {renamed} files" if public_repo else ""))
    if leaks:
        print("LEAKS (export refused):\n  " + "\n  ".join(leaks[:50]))
        return 1
    print("leak scan: clean")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True)
    ap.add_argument("--ref", default="main", help="a branch, tag or commit (default: main)")
    ap.add_argument("--public-repo", default=None, help="owner/name of the public repository")
    a = ap.parse_args()
    sys.exit(export(Path(a.out).resolve(), a.ref, a.public_repo))


if __name__ == "__main__":
    main()
