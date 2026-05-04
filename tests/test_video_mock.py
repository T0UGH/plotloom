import json
import tomllib

from click.testing import CliRunner

import plotloom.commands.video as video_commands
from plotloom.cli import main
from plotloom.video.adapters.mock import MockVideoAdapter


def test_video_submit_mock_writes_receipt_and_candidate(tmp_path):
    repo = _series_repo(tmp_path)
    ep = repo / "episodes" / "ep001"

    result = CliRunner().invoke(
        main,
        ["--repo", str(repo), "video", "submit", "--episode", "ep001", "--clip", "clip-01", "--adapter", "mock"],
    )

    assert result.exit_code == 0
    assert list((ep / "videos" / "clip-01" / "tasks").glob("mock-*.toml"))
    assert list((ep / "videos" / "clip-01" / "candidates").glob("v001.mock.mp4"))


def test_video_submit_mock_json_includes_receipt_and_candidate(tmp_path):
    repo = _series_repo(tmp_path)

    result = CliRunner().invoke(
        main,
        [
            "--json",
            "--repo",
            str(repo),
            "video",
            "submit",
            "--episode",
            "ep001",
            "--clip",
            "clip-01",
            "--adapter",
            "mock",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["ok"] is True
    assert payload["command"] == "video.submit"
    assert payload["provider_task_id"] == "local"
    assert payload["receipt_path"].endswith("tasks/mock-local.toml")
    assert payload["candidate_path"].endswith("candidates/v001.mock.mp4")


def test_video_submit_failure_writes_classified_receipt(tmp_path, monkeypatch):
    class FailingSubmitAdapter(MockVideoAdapter):
        def submit(self, request, *, candidate_path):
            raise TimeoutError("provider timed out")

    monkeypatch.setattr(video_commands, "MockVideoAdapter", FailingSubmitAdapter)
    repo = _series_repo(tmp_path)

    result = CliRunner().invoke(
        main,
        ["--repo", str(repo), "video", "submit", "--episode", "ep001", "--clip", "clip-01", "--adapter", "mock"],
    )

    assert result.exit_code == 1
    receipt_path = next((repo / "episodes" / "ep001" / "videos" / "clip-01" / "tasks").glob("*submit-failed*.toml"))
    receipt = tomllib.loads(receipt_path.read_text(encoding="utf-8"))
    assert receipt["status"] == "failed"
    assert receipt["failure_stage"] == "submit"
    assert receipt["failure_category"] == "provider_unreachable"
    assert receipt["retryable"] is True
    assert receipt["error_code"] == "SUBMIT_PROVIDER_UNREACHABLE"


def test_video_submit_mock_records_reference_intent_without_provider_payload_change(tmp_path):
    repo = _series_repo(tmp_path)
    reference = repo / "assets" / "cast" / "ethan" / "safe-face.png"
    reference.parent.mkdir(parents=True)
    reference.write_bytes(b"png")
    (repo / "assets" / "cast" / "ethan" / "face-policy.toml").write_text(
        '[face]\nstrategy = "safe-face-reference"\npath = "assets/cast/ethan/safe-face.png"\n',
        encoding="utf-8",
    )
    runner = CliRunner()
    plan = runner.invoke(
        main,
        [
            "--repo",
            str(repo),
            "video",
            "plan-references",
            "--episode",
            "ep001",
            "--clip",
            "clip-01",
            "--reference",
            "character:ethan=assets/cast/ethan/safe-face.png",
            "--write",
        ],
    )
    assert plan.exit_code == 0

    result = runner.invoke(
        main,
        [
            "--repo",
            str(repo),
            "video",
            "submit",
            "--episode",
            "ep001",
            "--clip",
            "clip-01",
            "--adapter",
            "mock",
            "--reference-map",
            "episodes/ep001/videos/clip-01/reference-map.toml",
        ],
    )

    assert result.exit_code == 0
    receipt_path = repo / "episodes" / "ep001" / "videos" / "clip-01" / "tasks" / "mock-local.toml"
    receipt = tomllib.loads(receipt_path.read_text(encoding="utf-8"))
    assert receipt["reference_map_path"] == "episodes/ep001/videos/clip-01/reference-map.toml"
    assert receipt["reference_intent"] == [
        {
            "slot": 1,
            "kind": "character",
            "path": "assets/cast/ethan/safe-face.png",
            "source": "asset",
            "character": "ethan",
        }
    ]
    assert receipt["provider_request"]["adapter"] == "mock"
    assert receipt["provider_data"] == {"mock": True}

    poll = runner.invoke(main, ["--repo", str(repo), "video", "poll", "--episode", "ep001", "--clip", "clip-01"])
    assert poll.exit_code == 0
    updated = tomllib.loads(receipt_path.read_text(encoding="utf-8"))
    assert updated["reference_intent"] == receipt["reference_intent"]


def test_video_submit_reference_map_rejects_text_only_face_policy(tmp_path):
    repo = _series_repo(tmp_path)
    reference = repo / "assets" / "cast" / "ethan" / "safe-face.png"
    reference.parent.mkdir(parents=True)
    reference.write_bytes(b"png")
    (repo / "assets" / "cast" / "ethan" / "face-policy.toml").write_text(
        '[face]\nstrategy = "text-only"\ndescription = "Ethan face should be prompt-only."\n',
        encoding="utf-8",
    )
    runner = CliRunner()
    plan = runner.invoke(
        main,
        [
            "--repo",
            str(repo),
            "video",
            "plan-references",
            "--episode",
            "ep001",
            "--clip",
            "clip-01",
            "--reference",
            "character:ethan=assets/cast/ethan/safe-face.png",
            "--write",
        ],
    )
    assert plan.exit_code == 0

    result = runner.invoke(
        main,
        [
            "--repo",
            str(repo),
            "video",
            "submit",
            "--episode",
            "ep001",
            "--clip",
            "clip-01",
            "--adapter",
            "mock",
            "--reference-map",
            "episodes/ep001/videos/clip-01/reference-map.toml",
        ],
    )

    assert result.exit_code == 1
    assert "face strategy is text-only" in result.output


def test_video_submit_reference_map_accepts_cloud_face_body_reference(tmp_path):
    repo = _series_repo(tmp_path)
    body = repo / "assets" / "cast" / "ethan" / "body-wardrobe.png"
    body.parent.mkdir(parents=True)
    body.write_bytes(b"png")
    (repo / "assets" / "cast" / "ethan" / "face-policy.toml").write_text(
        "\n".join(
            [
                "[face]",
                'strategy = "cloud-face-asset"',
                'provider = "volcengine-seedance"',
                'cloud_asset = "asset://asset-20260224225526-g6kpx"',
                'body_reference = "assets/cast/ethan/body-wardrobe.png"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    runner = CliRunner()
    plan = runner.invoke(
        main,
        [
            "--repo",
            str(repo),
            "video",
            "plan-references",
            "--episode",
            "ep001",
            "--clip",
            "clip-01",
            "--reference",
            "character:ethan=assets/cast/ethan/body-wardrobe.png",
            "--write",
        ],
    )
    assert plan.exit_code == 0

    result = runner.invoke(
        main,
        [
            "--repo",
            str(repo),
            "video",
            "submit",
            "--episode",
            "ep001",
            "--clip",
            "clip-01",
            "--adapter",
            "mock",
            "--reference-map",
            "episodes/ep001/videos/clip-01/reference-map.toml",
        ],
    )

    assert result.exit_code == 0


def test_video_poll_mock_uses_latest_pointer(tmp_path):
    repo = _series_repo(tmp_path)
    runner = CliRunner()
    submit = runner.invoke(
        main,
        ["--repo", str(repo), "video", "submit", "--episode", "ep001", "--clip", "clip-01", "--adapter", "mock"],
    )
    assert submit.exit_code == 0

    result = runner.invoke(
        main,
        ["--json", "--repo", str(repo), "video", "poll", "--episode", "ep001", "--clip", "clip-01"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["ok"] is True
    assert payload["command"] == "video.poll"
    assert payload["adapter"] == "mock"
    assert payload["status"] == "succeeded"


def _series_repo(tmp_path):
    repo = tmp_path / "series"
    ep = repo / "episodes" / "ep001"
    ep.mkdir(parents=True)
    (repo / "series.md").write_text("# Series\n", encoding="utf-8")
    (repo / "characters.md").write_text("# Characters\n", encoding="utf-8")
    (ep / "video-prompts-en.md").write_text("## Clip 01\n\nPrompt string:\nA fake clip.\n", encoding="utf-8")
    return repo
