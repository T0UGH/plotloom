import json

from click.testing import CliRunner

import plotloom.selection as selection_module
from plotloom.cli import main
from plotloom.paths import next_candidate_path, selected_for_candidate
from plotloom.selection import select_candidate


def test_candidate_numbering_skips_adapter_suffixes(tmp_path):
    candidates = tmp_path / "candidates"
    candidates.mkdir()
    (candidates / "v001.dreamina-cli.mp4").write_bytes(b"first")

    path = next_candidate_path(candidates, ".mp4", adapter="volcengine-seedance")

    assert path == candidates / "v002.volcengine-seedance.mp4"


def test_candidate_numbering_counts_dotted_adapter_suffixes(tmp_path):
    candidates = tmp_path / "candidates"
    candidates.mkdir()
    (candidates / "v001.provider.v2.mp4").write_bytes(b"first")

    path = next_candidate_path(candidates, ".mp4", adapter="provider.v2")

    assert path == candidates / "v002.provider.v2.mp4"


def test_selected_for_candidate_maps_to_sibling_selected_file(tmp_path):
    candidate = tmp_path / "videos" / "candidates" / "v001.volcengine-seedance.mp4"

    assert selected_for_candidate(candidate) == tmp_path / "videos" / "selected.mp4"


def test_selected_for_candidate_rejects_non_candidate_path(tmp_path):
    candidate = tmp_path / "videos" / "v001.mp4"

    try:
        selected_for_candidate(candidate)
    except ValueError as error:
        assert "candidates" in str(error)
    else:
        raise AssertionError("expected candidates directory validation")


def test_select_copies_candidate_and_backs_up_previous_selected(tmp_path):
    candidates = tmp_path / "videos" / "candidates"
    candidates.mkdir(parents=True)
    candidate = candidates / "v001.volcengine-seedance.mp4"
    selected = tmp_path / "videos" / "selected.mp4"
    candidate.write_bytes(b"new candidate")
    selected.write_bytes(b"old selected")

    result = select_candidate(candidate)

    assert result.selected_path == selected
    assert result.backup_path is not None
    assert result.backup_path.parent == selected.parent
    assert result.backup_path.name.startswith("selected-prev-")
    assert result.backup_path.suffix == ".mp4"
    assert result.backup_path.read_bytes() == b"old selected"
    assert selected.read_bytes() == b"new candidate"
    assert candidate.read_bytes() == b"new candidate"


def test_select_uses_unique_backup_path_when_timestamp_collides(tmp_path, monkeypatch):
    class FixedDatetime:
        @classmethod
        def now(cls):
            return cls()

        def strftime(self, _format):
            return "20260430-120000-000000"

    candidates = tmp_path / "videos" / "candidates"
    candidates.mkdir(parents=True)
    candidate = candidates / "v001.mp4"
    selected = tmp_path / "videos" / "selected.mp4"
    existing_backup = tmp_path / "videos" / "selected-prev-20260430-120000-000000.mp4"
    candidate.write_bytes(b"new candidate")
    selected.write_bytes(b"old selected")
    existing_backup.write_bytes(b"existing backup")
    monkeypatch.setattr(selection_module, "datetime", FixedDatetime)

    result = selection_module.select_candidate(candidate)

    expected_backup = tmp_path / "videos" / "selected-prev-20260430-120000-000000-1.mp4"
    assert result.backup_path == expected_backup
    assert existing_backup.read_bytes() == b"existing backup"
    assert expected_backup.read_bytes() == b"old selected"
    assert selected.read_bytes() == b"new candidate"


def test_select_command_json_reports_selected_and_backup_paths(tmp_path):
    candidates = tmp_path / "videos" / "candidates"
    candidates.mkdir(parents=True)
    candidate = candidates / "v001.mp4"
    candidate.write_bytes(b"candidate")

    result = CliRunner().invoke(main, ["--json", "select", str(candidate)])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["ok"] is True
    assert payload["command"] == "select"
    assert payload["selected_path"] == str(tmp_path / "videos" / "selected.mp4")
    assert payload["backup_path"] is None
    assert (tmp_path / "videos" / "selected.mp4").read_bytes() == b"candidate"
