import json
import subprocess

from click.testing import CliRunner

from plotloom.adapters.image_codex_app_server import CodexImageAdapter
from plotloom.cli import main


def test_codex_image_adapter_copies_result(monkeypatch, tmp_path):
    source = tmp_path / "source.png"
    source.write_bytes(b"png")
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("make an image", encoding="utf-8")
    reference = tmp_path / "reference.png"
    reference.write_bytes(b"ref")
    out_dir = tmp_path / "out"
    calls = []

    def fake_run(*args, **kwargs):
        calls.append(args[0])
        result_path = [str(x) for x in args[0]][args[0].index("--output-last-message") + 1]
        schema_path = [str(x) for x in args[0]][args[0].index("--output-schema") + 1]
        with open(schema_path, encoding="utf-8") as f:
            schema = json.load(f)
        assert schema["required"] == ["image_path", "notes"]
        with open(result_path, "w", encoding="utf-8") as f:
            f.write(f'{{"image_path": "{source}", "notes": "ok"}}')
        return subprocess.CompletedProcess(args=args, returncode=0, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr("shutil.which", lambda name: "/usr/bin/codex")

    result = CodexImageAdapter().generate(prompt_file=prompt, output_dir=out_dir, filename="cover.png", images=[reference], timeout=10)

    assert result["ok"] is True
    assert (out_dir / "cover.png").exists()
    assert result["notes"] == "ok"
    assert "--image" in calls[0]
    assert calls[0][calls[0].index("--image") + 1] == str(reference)


def test_image_generate_cast_command_respects_filename(monkeypatch, tmp_path):
    source = tmp_path / "source.png"
    source.write_bytes(b"png")
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("make reference sheet", encoding="utf-8")
    repo = tmp_path / "series"
    repo.mkdir()

    def fake_run(*args, **kwargs):
        result_path = [str(x) for x in args[0]][args[0].index("--output-last-message") + 1]
        with open(result_path, "w", encoding="utf-8") as f:
            json.dump({"image_path": str(source), "notes": "ok"}, f)
        return subprocess.CompletedProcess(args=args, returncode=0, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr("shutil.which", lambda name: "/usr/bin/codex")

    result = CliRunner().invoke(
        main,
        [
            "--json",
            "--repo",
            str(repo),
            "image",
            "generate",
            "--kind",
            "cast",
            "--character",
            "aelia",
            "--filename",
            "reference-sheet/candidates/v001.png",
            "--prompt-file",
            str(prompt),
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["ok"] is True
    assert payload["image_path"].endswith("assets/cast/aelia/reference-sheet/candidates/v001.png")
    assert (repo / "assets" / "cast" / "aelia" / "reference-sheet" / "candidates" / "v001.png").exists()



def test_image_generate_cover_command_writes_candidate(monkeypatch, tmp_path):
    source = tmp_path / "source.png"
    source.write_bytes(b"png")
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("make cover", encoding="utf-8")
    repo = tmp_path / "series"
    repo.mkdir()

    def fake_run(*args, **kwargs):
        result_path = [str(x) for x in args[0]][args[0].index("--output-last-message") + 1]
        with open(result_path, "w", encoding="utf-8") as f:
            json.dump({"image_path": str(source), "notes": "ok"}, f)
        return subprocess.CompletedProcess(args=args, returncode=0, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr("shutil.which", lambda name: "/usr/bin/codex")

    result = CliRunner().invoke(
        main,
        [
            "--json",
            "--repo",
            str(repo),
            "image",
            "generate",
            "--kind",
            "cover",
            "--episode",
            "ep001",
            "--prompt-file",
            str(prompt),
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["ok"] is True
    assert payload["command"] == "image.generate"
    assert payload["image_path"].endswith("episodes/ep001/images/covers/candidates/v001.png")
    assert (repo / "episodes" / "ep001" / "images" / "covers" / "candidates" / "v001.png").exists()
