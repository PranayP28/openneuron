import os
import tempfile

import pytest

# Keep test artefacts (metrics db, manifests, uploads) out of the repo.
_TMP = tempfile.mkdtemp(prefix="zeroday-tests-")
os.environ.setdefault("METRICS_DB_PATH", os.path.join(_TMP, "metrics.db"))
os.environ.setdefault("MANIFEST_DIR", os.path.join(_TMP, "manifests"))
os.environ.setdefault("UPLOAD_DIR", os.path.join(_TMP, "uploads"))
os.environ.setdefault("WARMUP_ON_STARTUP", "false")


@pytest.fixture(autouse=True)
def _run_in_tmp(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
