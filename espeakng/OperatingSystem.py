from enum import Enum


class OperatingSystem(Enum):
    """Operating system names as reported by ``platform.system()``."""

    WINDOWS = "Windows"
    DARWIN = "Darwin"
