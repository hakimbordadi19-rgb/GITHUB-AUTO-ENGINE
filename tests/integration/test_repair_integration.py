import shutil
import pytest

from engine.intelligent_repair import intelligent_repair


def test_python_integration(tmp_path):
    file = tmp_path / "broken.py"
    file.write_text('print("Hello"\n')

    result = intelligent_repair(file)

    assert result["status"] == "REPAIRED"
    assert result["repair_success"] is True
    assert result["final_status"] == "OK"


def test_javascript_integration(tmp_path):
    if not shutil.which("node"):
        pytest.skip("Node.js unavailable")

    file = tmp_path / "broken.js"
    file.write_text('console.log("Hello"\n')

    result = intelligent_repair(file)

    assert result["status"] == "REPAIRED"
    assert result["repair_success"] is True
    assert result["final_status"] == "REPAIRED"
    assert result["backup"]
