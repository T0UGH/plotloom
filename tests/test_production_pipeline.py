import json
import tomllib

from click.testing import CliRunner

from plotloom.cli import main
from plotloom.video.adapters.volcengine_seedance import VolcEngineSeedanceAdapter
from plotloom.video.types import PlotloomVideoRequest, VideoMode


def test_prompt_refs_and_strict_refs(tmp_path):
    repo = _series_repo(tmp_path, prompt="Prompt string:\nUse Image 2 for the hero face.\n")
    ref = repo / "assets" / "cast" / "ethan" / "safe-face.png"
    ref.parent.mkdir(parents=True)
    ref.write_bytes(b"png")
    (repo / "episodes" / "ep001" / "videos" / "clip-01").mkdir(parents=True)
    (repo / "episodes" / "ep001" / "videos" / "clip-01" / "reference-map.toml").write_text(
        '[[references]]\nslot = 1\nkind = "character"\npath = "assets/cast/ethan/safe-face.png"\ncharacter = "ethan"\n',
        encoding="utf-8",
    )

    refs = CliRunner().invoke(main, ["--json", "--repo", str(repo), "prompt", "refs", "--episode", "ep001", "--clip", "clip-01"])
    assert refs.exit_code == 0
    payload = json.loads(refs.output)
    assert payload["command"] == "prompt.refs"
    assert payload["references"][0]["path"] == "assets/cast/ethan/safe-face.png"

    strict = CliRunner().invoke(main, ["--repo", str(repo), "prompt", "check", "--episode", "ep001", "--clip", "clip-01", "--strict-refs"])
    assert strict.exit_code == 1
    assert "strict refs failed" in strict.output


def test_video_submit_explicit_refs_are_intent_only(tmp_path):
    repo = _series_repo(tmp_path)
    ref = repo / "assets" / "cast" / "ethan" / "body.png"
    ref.parent.mkdir(parents=True)
    ref.write_bytes(b"body")
    (repo / "assets" / "cast" / "ethan" / "face-policy.toml").write_text(
        "\n".join(
            [
                "[face]",
                'strategy = "cloud-face-asset"',
                'provider = "volcengine-seedance"',
                'cloud_asset = "asset://asset-20260224225526-g6kpx"',
                'body_reference = "assets/cast/ethan/body.png"',
                "",
            ]
        ),
        encoding="utf-8",
    )

    result = CliRunner().invoke(
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
            "--reference-image",
            "character:ethan=assets/cast/ethan/body.png",
        ],
    )

    assert result.exit_code == 0
    receipt = tomllib.loads((repo / "episodes" / "ep001" / "videos" / "clip-01" / "tasks" / "mock-local.toml").read_text(encoding="utf-8"))
    assert receipt["reference_intent"][0]["character"] == "ethan"
    assert receipt["provider_request"]["reference_intent_status"] == "intent_only_not_sent"
    assert receipt["provider_request"]["reference_assets"][0]["provider_role"] == "reference_image"
    assert receipt["provider_request"]["reference_assets"][0]["sha256"]


def test_asset_uri_reference_map_accepts_cloud_face_asset(tmp_path):
    repo = _series_repo(tmp_path)
    body = repo / "assets" / "cast" / "ethan" / "body.png"
    body.parent.mkdir(parents=True)
    body.write_bytes(b"body")
    (repo / "assets" / "cast" / "ethan" / "face-policy.toml").write_text(
        "\n".join(
            [
                "[face]",
                'strategy = "cloud-face-asset"',
                'provider = "volcengine-seedance"',
                'cloud_asset = "asset://asset-20260224225526-g6kpx"',
                'body_reference = "assets/cast/ethan/body.png"',
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
            "character:ethan=asset://asset-20260224225526-g6kpx",
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
    receipt = tomllib.loads((repo / "episodes" / "ep001" / "videos" / "clip-01" / "tasks" / "mock-local.toml").read_text(encoding="utf-8"))
    assert receipt["reference_intent"][0]["uri"] == "asset://asset-20260224225526-g6kpx"
    assert receipt["provider_request"]["reference_intent_status"] == "intent_only_not_sent"
    assert receipt["provider_request"]["reference_assets"][0]["uri"] == "asset://asset-20260224225526-g6kpx"
    assert "path" not in receipt["provider_request"]["reference_assets"][0]


def test_seedance_compiles_and_submits_asset_uri_refs_with_fake_http(tmp_path):
    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"id": "cgt-fake", "status": "submitted"}

    class FakeHTTP:
        def __init__(self):
            self.payload = None

        def post(self, _url, *, headers, json, timeout):
            self.payload = json
            return FakeResponse()

    request = PlotloomVideoRequest(
        repo=tmp_path,
        episode="ep001",
        clip="clip-01",
        adapter="volcengine-seedance",
        mode=VideoMode.REFERENCE_TO_VIDEO,
        prompt_file=tmp_path / "prompt.md",
        prompt_text="Use the cloud face asset.",
        ratio="9:16",
        resolution="720p",
        duration=5,
        first_frame_uri="asset://asset-20260224000000-first",
        reference_image_uris=["asset://asset-20260224225526-g6kpx"],
        last_frame_uri="asset://asset-20260224000000-last",
    )
    http = FakeHTTP()
    adapter = VolcEngineSeedanceAdapter(http=http, ark_api_key="test-key")

    native = adapter.compile_native_request(request)
    assert native["payload"]["content"] == [
        {"type": "text", "role": "prompt", "text_chars": len(request.prompt_text)},
        {"type": "image_url", "image_url": {"url": "asset://asset-20260224000000-first"}, "role": "first_frame"},
        {"type": "image_url", "image_url": {"url": "asset://asset-20260224225526-g6kpx"}, "role": "reference_image"},
        {"type": "image_url", "image_url": {"url": "asset://asset-20260224000000-last"}, "role": "last_frame"},
    ]

    result = adapter.submit(request, candidate_path=tmp_path / "out.mp4")

    assert result.provider_task_id == "cgt-fake"
    assert http.payload["content"] == [
        {"type": "text", "text": request.prompt_text},
        {"type": "image_url", "image_url": {"url": "asset://asset-20260224000000-first"}, "role": "first_frame"},
        {"type": "image_url", "image_url": {"url": "asset://asset-20260224225526-g6kpx"}, "role": "reference_image"},
        {"type": "image_url", "image_url": {"url": "asset://asset-20260224000000-last"}, "role": "last_frame"},
    ]


def test_face_policy_and_smoke_prompt(tmp_path):
    repo = _series_repo(tmp_path)
    body = repo / "assets" / "cast" / "ethan" / "body.png"
    body.parent.mkdir(parents=True)
    body.write_bytes(b"body")
    (repo / "assets" / "cast" / "ethan" / "face-policy.toml").write_text(
        "\n".join(
            [
                "[face]",
                'strategy = "cloud-face-asset"',
                'provider = "volcengine-seedance"',
                'cloud_asset = "asset://asset-20260224225526-g6kpx"',
                'body_reference = "assets/cast/ethan/body.png"',
                "",
            ]
        ),
        encoding="utf-8",
    )

    policy = CliRunner().invoke(main, ["--json", "--repo", str(repo), "face", "policy", "--character", "ethan", "--adapter", "volcengine-seedance"])
    assert policy.exit_code == 0
    payload = json.loads(policy.output)
    assert payload["policy"]["cloud_asset_redacted"] != payload["policy"]["cloud_asset"]
    assert "body/wardrobe" in payload["advice"]["notes"][0]

    smoke = CliRunner().invoke(main, ["--repo", str(repo), "face", "smoke-prompt", "--character", "ethan", "--adapter", "volcengine-seedance"])
    assert smoke.exit_code == 0
    assert "Medium close-up" in smoke.output
    assert "face occupies 25-35%" in smoke.output


def test_asset_select_info_and_canonical_validate(tmp_path):
    repo = _series_repo(tmp_path)
    candidate = repo / "assets" / "cast" / "ethan" / "candidates" / "v001.png"
    candidate.parent.mkdir(parents=True)
    candidate.write_bytes(b"candidate")

    select = CliRunner().invoke(
        main,
        ["--repo", str(repo), "asset", "select", "--character", "ethan", "--candidate", "assets/cast/ethan/candidates/v001.png"],
    )
    assert select.exit_code == 0
    assert (repo / "assets" / "cast" / "ethan" / "selected.png").read_bytes() == b"candidate"
    assert (repo / "assets" / "cast" / "ethan" / "metadata.toml").exists()

    info = CliRunner().invoke(main, ["--json", "--repo", str(repo), "asset", "info", "--character", "ethan"])
    assert info.exit_code == 0
    assert json.loads(info.output)["asset"]["selected_exists"] is True

    validate = CliRunner().invoke(main, ["--repo", str(repo), "validate", "--canonical-assets"])
    assert validate.exit_code == 0


def test_image_batch_resume_and_skip_existing(tmp_path):
    repo = _series_repo(tmp_path)
    existing = repo / "assets" / "scenes" / "mine" / "candidates" / "v001.png"
    existing.parent.mkdir(parents=True)
    existing.write_bytes(b"png")
    manifest = repo / "episodes" / "ep001" / "assets.toml"
    manifest.write_text(
        "\n".join(
            [
                "[[items]]",
                'kind = "scene"',
                'output = "assets/scenes/mine/candidates/v001.png"',
                "",
                "[[items]]",
                'kind = "scene"',
                'output = "assets/scenes/town/candidates/v001.png"',
                "",
            ]
        ),
        encoding="utf-8",
    )

    result = CliRunner().invoke(main, ["--repo", str(repo), "image", "batch", "--manifest", "episodes/ep001/assets.toml", "--resume", "--skip-existing"])
    assert result.exit_code == 0
    data = tomllib.loads(manifest.read_text(encoding="utf-8"))
    assert data["items"][0]["status"] == "skipped"
    assert data["items"][1]["status"] == "pending"


def test_review_contact_sheet_and_note(tmp_path):
    repo = _series_repo(tmp_path)
    candidate = repo / "assets" / "scenes" / "mine" / "candidates" / "v001.png"
    candidate.parent.mkdir(parents=True)
    candidate.write_bytes(b"not-a-real-png")

    result = CliRunner().invoke(main, ["--repo", str(repo), "review", "contact-sheet", "--kind", "scenes", "--output", "episodes/ep001/review/contact-sheet.svg"])
    assert result.exit_code == 0
    assert (repo / "episodes" / "ep001" / "review" / "contact-sheet.svg").exists()
    note = repo / "episodes" / "ep001" / "review" / "review-note.md"
    assert "`assets/scenes/mine/candidates/v001.png`" in note.read_text(encoding="utf-8")


def test_doctor_explain_error():
    result = CliRunner().invoke(main, ["--json", "doctor", "--explain-error", "InputImageSensitiveContentDetected.PrivacyInformation"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["command"] == "doctor.explain-error"
    assert payload["error"]["category"] == "content_rejected"
    assert payload["error"]["retryable"] is False


def _series_repo(tmp_path, prompt="Prompt string:\nA fake clip.\n"):
    repo = tmp_path / "series"
    ep = repo / "episodes" / "ep001"
    (ep / "videos").mkdir(parents=True)
    (repo / "assets" / "cast").mkdir(parents=True)
    (repo / "assets" / "scenes").mkdir(parents=True)
    (repo / "series.md").write_text("# Series\n", encoding="utf-8")
    (repo / "characters.md").write_text("# Characters\n", encoding="utf-8")
    (ep / "video-prompts-en.md").write_text(f"## Clip 01\n\n{prompt}", encoding="utf-8")
    return repo
