import tomllib

from plotloom.video.receipts import Receipt, receipt_path, write_latest_pointer, write_receipt


def make_receipt(tmp_path, **overrides):
    values = {
        "adapter": "volcengine-seedance",
        "provider": "volcengine",
        "provider_task_id": "cgt-123",
        "status": "queued",
        "repo": str(tmp_path),
        "episode": "ep001",
        "clip": "clip-01",
        "mode": "text-to-video",
        "prompt_file": "episodes/ep001/video-prompts-en.md",
        "compiled_prompt_sha256": "abc",
        "prompt_chars": 10,
        "duration": 5,
        "ratio": "9:16",
        "resolution": "720p",
        "audio_intent": "native_if_supported",
        "credential_source": "config",
    }
    values.update(overrides)
    return Receipt(**values)


def test_write_receipt_and_latest_pointer(tmp_path):
    path = receipt_path(tmp_path, "ep001", "clip-01", "volcengine-seedance", "cgt-123")
    receipt = Receipt(
        adapter="volcengine-seedance",
        provider="volcengine",
        provider_task_id="cgt-123",
        status="queued",
        repo=str(tmp_path),
        episode="ep001",
        clip="clip-01",
        mode="text-to-video",
        prompt_file="episodes/ep001/video-prompts-en.md",
        compiled_prompt_sha256="abc",
        prompt_chars=10,
        duration=5,
        ratio="9:16",
        resolution="720p",
        audio_intent="native_if_supported",
        credential_source="config",
    )
    write_receipt(path, receipt)
    write_latest_pointer(path, receipt)
    assert path.exists()
    latest = tmp_path / "episodes" / "ep001" / "videos" / "clip-01" / "latest-task.toml"
    assert latest.exists()
    assert "tasks/volcengine-seedance-cgt-123.toml" in latest.read_text()


def test_receipt_path_replaces_unsafe_id_separators(tmp_path):
    path = receipt_path(tmp_path, "ep001", "clip-01", "adapter/name", "task:id/child")

    assert path == (
        tmp_path
        / "episodes"
        / "ep001"
        / "videos"
        / "clip-01"
        / "tasks"
        / "adapter-name-task-id-child.toml"
    )


def test_provider_data_does_not_collide_with_top_level_provider(tmp_path):
    path = receipt_path(tmp_path, "ep001", "clip-01", "volcengine-seedance", "cgt-123")
    receipt = make_receipt(
        tmp_path,
        provider="volcengine",
        provider_data={"provider": "nested-provider", "request_id": "req-1"},
    )

    write_receipt(path, receipt)

    data = tomllib.loads(path.read_text(encoding="utf-8"))
    assert data["provider"] == "volcengine"
    assert data["provider_data"] == {
        "provider": "nested-provider",
        "request_id": "req-1",
    }
