from plotloom.video.failures import classify_failure, is_retryable_code_or_message


def test_classify_content_rejected_failure():
    failure = classify_failure("submit", "InputImageSensitiveContentDetected.PrivacyInformation: input image may contain real person")

    assert failure.category == "content_rejected"
    assert failure.retryable is False
    assert failure.code == "SUBMIT_CONTENT_REJECTED"


def test_retryable_code_helper_handles_timeout_and_auth():
    assert is_retryable_code_or_message("DOWNLOAD_PROVIDER_UNREACHABLE", None) is True
    assert is_retryable_code_or_message(None, "401 unauthorized") is False
