import subprocess
import sys


def test_validate_repo_script_still_runs(tmp_path):
    repo = tmp_path / "series"
    (repo / "episodes").mkdir(parents=True)
    (repo / "series.md").write_text("# Series\n", encoding="utf-8")
    (repo / "characters.md").write_text("# Characters\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, "scripts/validate_repo.py", "--repo", str(repo)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 0


def test_select_candidate_script_still_runs(tmp_path):
    candidate = tmp_path / "videos" / "candidates" / "v001.mp4"
    selected = tmp_path / "videos" / "selected.mp4"
    candidate.parent.mkdir(parents=True)
    candidate.write_bytes(b"candidate")

    result = subprocess.run(
        [sys.executable, "scripts/select_candidate.py", "--candidate", str(candidate), "--selected", str(selected)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 0
    assert selected.read_bytes() == b"candidate"
