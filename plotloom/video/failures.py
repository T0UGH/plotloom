from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class FailureClassification:
    category: str
    retryable: bool | None
    code: str


def explain_provider_error(code_or_message: str) -> dict[str, object]:
    text = code_or_message.strip()
    lowered = text.lower()
    if any(token in lowered for token in ("privacy", "sensitive", "real person", "moderation", "content policy", "真人")):
        return {
            "raw": text,
            "category": "content_rejected",
            "retryable": False,
            "likely_cause": "Input image or prompt tripped provider content/privacy policy, often with realistic human face references.",
            "next_step": "Use face policy guidance: avoid full visible-face character sheets, use text-only or approved cloud face asset plus body/wardrobe reference.",
        }
    if any(token in lowered for token in ("rate limit", "too many requests", "retry-after", "throttl")):
        return {
            "raw": text,
            "category": "rate_limited",
            "retryable": True,
            "likely_cause": "Provider throttled the request.",
            "next_step": "Resume later with batch status preserved; do not rerun succeeded items.",
        }
    if any(token in lowered for token in ("timeout", "timed out", "connection", "dns", "temporary", "unreachable")):
        return {
            "raw": text,
            "category": "provider_unreachable",
            "retryable": True,
            "likely_cause": "Provider or network path was temporarily unavailable.",
            "next_step": "Retry the failed item only after checking receipt and batch status.",
        }
    if any(token in lowered for token in ("401", "403", "forbidden", "unauthorized", "api key", "credential", "token", "auth")):
        return {
            "raw": text,
            "category": "auth_error",
            "retryable": False,
            "likely_cause": "Credentials, token, or account permissions are invalid.",
            "next_step": "Run doctor for the adapter and fix credentials before retrying.",
        }
    if any(token in lowered for token in ("400", "invalid", "unsupported", "missing", "bad request", "validation", "malformed")):
        return {
            "raw": text,
            "category": "request_invalid",
            "retryable": False,
            "likely_cause": "Request schema, model, parameter, or media input is invalid for the provider.",
            "next_step": "Inspect provider_request in the receipt and adjust the local intent before submitting again.",
        }
    classification = classify_failure("provider", text)
    return {
        "raw": text,
        "category": classification.category,
        "retryable": classification.retryable,
        "likely_cause": "Provider returned an unclassified error.",
        "next_step": "Check the task receipt, provider_request summary, and provider raw error before retrying.",
    }


def classify_failure(stage: str, message: str) -> FailureClassification:
    category, retryable = _category_and_retryable(stage, message)
    return FailureClassification(category=category, retryable=retryable, code=f"{stage.upper()}_{category.upper()}")


def is_retryable_code_or_message(error_code: str | None, error_message: str | None) -> bool | None:
    for text in (error_code, error_message):
        if not text:
            continue
        lowered = str(text).lower()
        if any(token in lowered for token in ("timeout", "timed out", "connection", "unreachable", "rate limit", "throttl", "temporary")):
            return True
        if re.search(r"\b5\d{2}\b", lowered):
            return True
        if any(token in lowered for token in ("401", "403", "forbidden", "unauthorized", "api key", "credential", "invalid", "unsupported")):
            return False
    return None


def _category_and_retryable(stage: str, message: str) -> tuple[str, bool | None]:
    lowered = (message or "").lower()
    if any(token in lowered for token in ("timed out", "timeout", "connection", "connect", "dns", "temporary", "unreachable")):
        return "provider_unreachable", True
    if any(token in lowered for token in ("rate limit", "too many requests", "retry-after", "throttl")):
        return "rate_limited", True
    if any(token in lowered for token in ("privacy", "sensitive", "real person", "content policy", "moderation", "审核", "真人")):
        return "content_rejected", False
    if any(token in lowered for token in ("401", "403", "forbidden", "unauthorized", "api key", "credential", "token", "auth")):
        return "auth_error", False
    if any(token in lowered for token in ("400", "invalid", "unsupported", "missing", "bad request", "validation", "malformed")):
        return "request_invalid", False
    if any(token in lowered for token in ("ioerror", "oserror", "permission", "denied", "permission denied")):
        return "filesystem_error", False
    if any(token in lowered for token in ("upload", "media", "uploading")):
        return "upload_failed", True
    if stage == "download":
        return "download_failed", True
    return "provider_error", None
