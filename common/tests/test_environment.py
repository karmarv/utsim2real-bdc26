"""The project environment (.venv_ut) matches requirements.txt and requirements-lock.txt exactly."""
import re
from importlib import metadata
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]


def _pins(path: Path) -> dict:
    out = {}
    for line in path.read_text().splitlines():
        line = line.split("#", 1)[0].strip()
        m = re.match(r"^([A-Za-z0-9_.\-]+)==([^\s;]+)$", line)
        if m:
            out[m.group(1)] = m.group(2)
    return out


def _installed(name: str):
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


@pytest.mark.parametrize("fname", ["requirements.txt", "requirements-lock.txt"])
def test_installed_versions_match_the_pins(fname):
    pins = _pins(REPO / fname)
    assert len(pins) > 20, f"{fname}: expected pinned packages"
    drift = {n: (v, _installed(n)) for n, v in pins.items() if _installed(n) != v}
    assert not drift, f"{fname} pin != installed (pinned, installed): {drift}"


def test_every_direct_pin_is_in_the_lock():
    req, lock = _pins(REPO / "requirements.txt"), _pins(REPO / "requirements-lock.txt")
    norm = lambda n: re.sub(r"[-_.]+", "-", n).lower()
    lock_n = {norm(k): v for k, v in lock.items()}
    missing = {n: v for n, v in req.items() if n not in ("setuptools", "wheel") and lock_n.get(norm(n)) != v}
    assert not missing, f"requirements.txt pins missing from or different in the lock: {missing}"


def test_open3d_ray_casting_runs_in_the_project_environment():
    import numpy as np
    import open3d as o3d
    scene = o3d.t.geometry.RaycastingScene(nthreads=1)
    V = (np.array([[0, -1, -1], [0, 1, -1], [0, 1, 1], [0, -1, 1]]) + [5, 0, 0]).astype(np.float32)
    scene.add_triangles(o3d.core.Tensor(V), o3d.core.Tensor(np.array([[0, 1, 2], [0, 2, 3]], dtype=np.uint32)))
    t = scene.cast_rays(o3d.core.Tensor(np.array([[0, 0, 0, 1, 0, 0]], dtype=np.float32)))["t_hit"].numpy()
    assert abs(float(t[0]) - 5.0) < 1e-5
