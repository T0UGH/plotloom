from __future__ import annotations

import shutil
from pathlib import Path

from plotloom.video.adapters.base import VideoSubmitResult, VideoTaskStatus
from plotloom.video.capabilities import capabilities_for, validate_request
from plotloom.video.types import PlotloomVideoRequest


class MockVideoAdapter:
    name = "mock"
    provider = "local"

    def capabilities(self):
        return capabilities_for(self.name)

    def validate_request(self, request: PlotloomVideoRequest):
        return validate_request(request, self.capabilities())

    def compile_native_request(self, request: PlotloomVideoRequest) -> dict[str, object]:
        return {
            "adapter": self.name,
            "provider": self.provider,
            "mode": request.mode.value,
            "duration": request.duration,
            "ratio": request.ratio,
            "resolution": request.resolution,
            "artifact": "local fixture or placeholder",
        }

    def submit(self, request: PlotloomVideoRequest, *, candidate_path: Path) -> VideoSubmitResult:
        candidate_path.parent.mkdir(parents=True, exist_ok=True)
        fixture = Path(__file__).resolve().parents[3] / "examples" / "fixtures" / "fake-video.mp4"
        if fixture.exists():
            shutil.copy2(fixture, candidate_path)
        else:
            candidate_path.write_bytes(b"mock video placeholder")
        return VideoSubmitResult(
            adapter=self.name,
            provider=self.provider,
            provider_task_id="local",
            status="succeeded",
            local_path=candidate_path,
            raw={"mock": True},
        )

    def poll(self, provider_task_id: str, *, download_dir: Path) -> VideoTaskStatus:
        return VideoTaskStatus(
            adapter=self.name,
            provider_task_id=provider_task_id,
            status="succeeded",
            local_path=download_dir / "candidates",
            raw={"mock": True},
        )
