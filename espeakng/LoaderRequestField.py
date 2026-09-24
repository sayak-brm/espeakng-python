from enum import Enum


class LoaderRequestField(Enum):
    """Field names of the JSON request sent to a loader worker over stdin."""

    PROTOCOL = "protocol"
    PHRASE = "phrase"
    VOICE = "voice"
    WPM = "wpm"
    PITCH = "pitch"
    AMPLITUDE = "amplitude"
    WORDGAP = "wordgap"
    EXPORT_PATH = "export_path"
