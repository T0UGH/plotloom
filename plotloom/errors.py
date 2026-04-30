class PlotloomError(Exception):
    exit_code = 1
    code = "PLOTLOOM_ERROR"

    def __init__(self, message: str, *, next_step: str | None = None):
        super().__init__(message)
        self.message = message
        self.next_step = next_step


class ConfigError(PlotloomError):
    exit_code = 2
    code = "CONFIG_ERROR"


class ProviderError(PlotloomError):
    exit_code = 3
    code = "PROVIDER_ERROR"


class MediaValidationError(PlotloomError):
    exit_code = 4
    code = "MEDIA_VALIDATION_ERROR"
