from enum import Enum


class WorkerErrorField(Enum):
    """Field names of the JSON error a loader worker writes to stderr."""

    TYPE = "type"
    MESSAGE = "message"
