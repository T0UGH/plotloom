from __future__ import annotations

from pathlib import Path
from typing import Any

from plotloom.video.adapters.base import VideoSubmitResult, VideoTaskStatus
from plotloom.video.capabilities import capabilities_for, validate_request
from plotloom.video.types import PlotloomVideoRequest


DEFAULT_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
DEFAULT_MODEL = "doubao-seedance-2-0-260128"


class VolcEngineSeedanceAdapter:
    name = "volcengine-seedance"
    provider = "volcengine"

    def __init__(
        self,
        *,
        http: Any | None = None,
        ark_api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        model: str = DEFAULT_MODEL,
        timeout: int = 600,
    ) -> None:
        self.http = http or _requests()
        self.ark_api_key = ark_api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def capabilities(self):
        return capabilities_for(self.name)

    def validate_request(self, request: PlotloomVideoRequest):
        return validate_request(request, self.capabilities())

    def compile_native_request(self, request: PlotloomVideoRequest) -> dict[str, Any]:
        payload = {
            "model": self.model,
            "content": _summary_content(request),
            "generate_audio": True,
            "ratio": request.ratio,
            "duration": request.duration,
            "watermark": False,
        }
        return {
            "adapter": self.name,
            "provider": self.provider,
            "endpoint": "/contents/generations/tasks",
            "payload": payload,
        }

    def submit(
        self,
        request: PlotloomVideoRequest,
        *,
        candidate_path: Path,
        reference_images: list[str] | None = None,
        reference_videos: list[str] | None = None,
        reference_audio: str | None = None,
        generate_audio: bool = True,
        watermark: bool = False,
    ) -> VideoSubmitResult:
        if not self.ark_api_key:
            raise RuntimeError("ARK_API_KEY is required for volcengine-seedance")
        payload = {
            "model": self.model,
            "content": _content(
                request.prompt_text,
                image_inputs=_request_image_inputs(request),
                reference_images=reference_images or [],
                reference_videos=reference_videos or [],
                reference_audio=reference_audio,
            ),
            "generate_audio": generate_audio,
            "ratio": request.ratio,
            "duration": request.duration,
            "watermark": watermark,
        }
        response = self.http.post(
            f"{self.base_url}/contents/generations/tasks",
            headers=self._headers(),
            json=payload,
            timeout=self.timeout,
        )
        _raise_for_status(response)
        data = _json(response)
        task_id = _task_id(data)
        if not task_id:
            raise RuntimeError("volcengine submit did not return task id")
        return VideoSubmitResult(
            adapter=self.name,
            provider=self.provider,
            provider_task_id=task_id,
            status="queued",
            local_path=candidate_path,
            raw=data,
        )

    def poll(self, provider_task_id: str, *, download_dir: Path) -> VideoTaskStatus:
        if not self.ark_api_key:
            raise RuntimeError("ARK_API_KEY is required for volcengine-seedance")
        response = self.http.get(
            f"{self.base_url}/contents/generations/tasks/{provider_task_id}",
            headers=self._headers(),
            timeout=self.timeout,
        )
        _raise_for_status(response)
        data = _json(response)
        status = _normalize_status(str(data.get("status") or data.get("state") or "unknown"))
        return VideoTaskStatus(
            adapter=self.name,
            provider_task_id=provider_task_id,
            status=status,
            video_url=_video_url(data),
            raw=data,
        )

    def _headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.ark_api_key}",
        }


def _content(
    prompt: str,
    *,
    image_inputs: list[dict[str, str]] | None = None,
    reference_images: list[str],
    reference_videos: list[str],
    reference_audio: str | None,
) -> list[dict[str, Any]]:
    content: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
    for item in image_inputs or []:
        content.append({"type": "image_url", "image_url": {"url": item["url"]}, "role": item["role"]})
    for url in reference_images:
        content.append({"type": "image_url", "image_url": {"url": url}, "role": "reference_image"})
    for url in reference_videos:
        content.append({"type": "video_url", "video_url": {"url": url}, "role": "reference_video"})
    if reference_audio:
        content.append({"type": "audio_url", "audio_url": {"url": reference_audio}, "role": "reference_audio"})
    return content


def _summary_content(request: PlotloomVideoRequest) -> list[dict[str, Any]]:
    content: list[dict[str, Any]] = [{"type": "text", "role": "prompt", "text_chars": len(request.prompt_text)}]
    for item in _request_image_inputs(request):
        content.append({"type": "image_url", "image_url": {"url": item["url"]}, "role": item["role"]})
    return content


def _request_image_inputs(request: PlotloomVideoRequest) -> list[dict[str, str]]:
    inputs: list[dict[str, str]] = []
    if request.first_frame_uri:
        inputs.append({"url": request.first_frame_uri, "role": "first_frame"})
    for uri in request.reference_image_uris:
        inputs.append({"url": uri, "role": "reference_image"})
    if request.last_frame_uri:
        inputs.append({"url": request.last_frame_uri, "role": "last_frame"})
    return inputs


def _requests() -> Any:
    import requests

    return requests


def _json(response: Any) -> dict[str, Any]:
    data = response.json()
    return data if isinstance(data, dict) else {}


def _raise_for_status(response: Any) -> None:
    raise_for_status = getattr(response, "raise_for_status", None)
    if callable(raise_for_status):
        raise_for_status()


def _task_id(data: dict[str, Any]) -> str | None:
    for key in ("id", "task_id", "taskId"):
        if data.get(key):
            return str(data[key])
    output = data.get("output")
    if isinstance(output, dict):
        for key in ("id", "task_id", "taskId"):
            if output.get(key):
                return str(output[key])
    return None


def _video_url(data: dict[str, Any]) -> str | None:
    for key in ("video_url", "url"):
        if data.get(key):
            return str(data[key])
    output = data.get("output")
    if isinstance(output, dict):
        for key in ("video_url", "url"):
            if output.get(key):
                return str(output[key])
        video = output.get("video")
        if isinstance(video, dict) and video.get("url"):
            return str(video["url"])
    content = data.get("content")
    if isinstance(content, dict):
        for key in ("video_url", "url"):
            if content.get(key):
                return str(content[key])
    return None


def _normalize_status(status: str) -> str:
    lowered = status.lower()
    if lowered in {"success", "succeeded", "done", "completed"}:
        return "succeeded"
    if lowered in {"fail", "failed", "error"}:
        return "failed"
    if lowered in {"queued", "running", "pending", "processing"}:
        return lowered
    return lowered
