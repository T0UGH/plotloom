from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any

from plotloom.video.adapters.base import VideoSubmitResult, VideoTaskStatus
from plotloom.video.capabilities import capabilities_for, validate_request
from plotloom.video.types import PlotloomVideoRequest, VideoMode


class DreaminaCliAdapter:
    name = "dreamina-cli"
    provider = "dreamina"

    def __init__(self, binary: str = "dreamina", home: str = "~", model_version: str = "seedance2.0fast") -> None:
        self.binary = binary
        self.home = home
        self.model_version = model_version

    def capabilities(self):
        return capabilities_for(self.name)

    def validate_request(self, request: PlotloomVideoRequest):
        return validate_request(request, self.capabilities())

    def compile_native_request(self, request: PlotloomVideoRequest) -> dict[str, object]:
        command = self._submit_command(request)
        redacted: list[str] = []
        skip_prompt = False
        for arg in command:
            if skip_prompt:
                redacted.append("<compiled-prompt>")
                skip_prompt = False
                continue
            redacted.append(arg)
            if arg == "--prompt":
                skip_prompt = True
        return {
            "adapter": self.name,
            "provider": self.provider,
            "mode": request.mode.value,
            "binary": self.binary,
            "command": redacted,
            "model_version": self.model_version,
            "prompt_chars": len(request.prompt_text),
        }

    def submit(self, request: PlotloomVideoRequest, *, candidate_path: Path) -> VideoSubmitResult:
        command = self._submit_command(request)
        completed = subprocess.run(command, capture_output=True, text=True, check=False, env=self._env())
        if completed.returncode != 0:
            raise RuntimeError(_stderr_or_stdout(completed))
        submit_id = _parse_submit_id(completed.stdout) or _parse_submit_id(completed.stderr)
        if not submit_id:
            raise RuntimeError("dreamina submit did not return submit_id")
        return VideoSubmitResult(
            adapter=self.name,
            provider=self.provider,
            provider_task_id=submit_id,
            status="queued",
            local_path=candidate_path,
            raw={"stdout": completed.stdout, "stderr": completed.stderr},
        )

    def poll(self, provider_task_id: str, *, download_dir: Path) -> VideoTaskStatus:
        download_dir.mkdir(parents=True, exist_ok=True)
        command = [
            self.binary,
            "query_result",
            "--submit_id",
            provider_task_id,
            "--download_dir",
            str(download_dir),
        ]
        completed = subprocess.run(command, capture_output=True, text=True, check=False, env=self._env())
        if completed.returncode != 0:
            return VideoTaskStatus(
                adapter=self.name,
                provider_task_id=provider_task_id,
                status="failed",
                error_message=_stderr_or_stdout(completed),
                raw={"stdout": completed.stdout, "stderr": completed.stderr},
            )
        payload = _json_payload(completed.stdout)
        status = str(payload.get("status") or payload.get("state") or "succeeded")
        return VideoTaskStatus(
            adapter=self.name,
            provider_task_id=provider_task_id,
            status=_normalize_status(status),
            local_path=_newest_file(download_dir),
            raw=payload or {"stdout": completed.stdout, "stderr": completed.stderr},
        )

    def _submit_command(self, request: PlotloomVideoRequest) -> list[str]:
        base = [
            self.binary,
            "text2video" if request.mode == VideoMode.TEXT_TO_VIDEO else "image2video",
        ]
        if request.mode == VideoMode.IMAGE_TO_VIDEO:
            if request.first_frame is None:
                raise ValueError("first_frame is required for dreamina image-to-video")
            base.extend(["--image", str(request.first_frame)])
        elif request.mode != VideoMode.TEXT_TO_VIDEO:
            raise ValueError(f"dreamina does not support mode: {request.mode.value}")
        base.extend(
            [
                "--prompt",
                request.prompt_text,
                "--duration",
                str(request.duration),
                "--ratio",
                request.ratio,
                "--video_resolution",
                request.resolution,
                "--model_version",
                self.model_version,
                "--poll=0",
            ]
        )
        return base

    def _env(self) -> dict[str, str]:
        env = os.environ.copy()
        if self.home and self.home != "~":
            env["HOME"] = str(Path(self.home).expanduser())
        return env


def _parse_submit_id(text: str) -> str | None:
    payload = _json_payload(text)
    for key in ("submit_id", "submitId", "task_id", "taskId", "id"):
        value = payload.get(key)
        if value:
            return str(value)
    match = re.search(r"(?:submit_id|submitId|task_id|taskId|id)\s*[:=]\s*['\"]?([A-Za-z0-9_.-]+)", text)
    return match.group(1) if match else None


def _json_payload(text: str) -> dict[str, Any]:
    text = text.strip()
    if not text:
        return {}
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start < 0 or end <= start:
            return {}
        try:
            data = json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return {}
    return data if isinstance(data, dict) else {}


def _normalize_status(status: str) -> str:
    lowered = status.lower()
    if lowered in {"success", "succeeded", "done", "completed"}:
        return "succeeded"
    if lowered in {"fail", "failed", "error"}:
        return "failed"
    return lowered


def _newest_file(directory: Path) -> Path | None:
    files = [path for path in directory.iterdir() if path.is_file()]
    return max(files, key=lambda path: path.stat().st_mtime) if files else None


def _stderr_or_stdout(completed: subprocess.CompletedProcess[str]) -> str:
    return completed.stderr.strip() or completed.stdout.strip() or f"process exited {completed.returncode}"
