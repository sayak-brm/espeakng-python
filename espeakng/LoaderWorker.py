import io
import json
import signal
import sys
from types import FrameType
from typing import Any, BinaryIO, ClassVar, Dict, Optional, TextIO, Union

from espeakng.AudioPlayer import AudioPlayer
from espeakng.LoaderProtocolError import LoaderProtocolError
from espeakng.LoaderRequestField import LoaderRequestField
from espeakng.WorkerErrorField import WorkerErrorField
from espeakng._native import synthesize


class LoaderWorker:
    """Serves one request inside the isolated loader worker process.

    Input is a JSON request on stdin; the utterance is synthesized to WAV and
    either exported or played; failures are written to stderr as JSON.
    """

    PROTOCOL_VERSION: ClassVar[int] = 1
    SUCCESS_EXIT_CODE: ClassVar[int] = 0
    FAILURE_EXIT_CODE: ClassVar[int] = 1
    # 128 + SIGTERM, the conventional exit code of a terminated process.
    TERMINATED_EXIT_CODE: ClassVar[int] = 143
    UNSUPPORTED_PROTOCOL_MESSAGE: ClassVar[str] = (
        "Unsupported loader worker protocol {!r}; expected {}"
    )

    def __init__(
        self,
        request_stream: BinaryIO,
        error_stream: TextIO,
        audio_player: AudioPlayer,
    ) -> None:
        """Create a worker bound to its request and error streams.

        Args:
            request_stream: Binary stream carrying one JSON request.
            error_stream: Text stream that receives the JSON error on failure.
            audio_player: Plays utterances that are not exported.

        Returns:
            None.

        Raises:
            Nothing.
        """
        self.__request_stream = request_stream
        self.__error_stream = error_stream
        self.__audio_player = audio_player

    @classmethod
    def for_standard_streams(cls) -> "LoaderWorker":
        """Create the worker the loader subprocess runs.

        Args:
            None.

        Returns:
            A worker reading stdin and reporting to stderr.

        Raises:
            Nothing.
        """
        return cls(sys.stdin.buffer, sys.stderr, AudioPlayer.for_current_platform())

    def run(self) -> int:
        """Serve the request on the request stream.

        Args:
            None.

        Returns:
            The process exit code: 0 on success, 1 after reporting a failure.

        Raises:
            SystemExit: The process received SIGTERM.
        """
        signal.signal(signal.SIGTERM, self.__exit_on_terminate)
        try:
            self.__serve(json.loads(self.__request_stream.read()))
        except Exception as failure:
            self.__report(failure)
            return self.FAILURE_EXIT_CODE
        return self.SUCCESS_EXIT_CODE

    def __serve(self, request: Dict[str, Any]) -> None:
        """Synthesize the requested utterance, then export or play it.

        Args:
            request: The decoded JSON request.

        Returns:
            None.

        Raises:
            LoaderProtocolError: The request uses another protocol version.
            NativeSpeechError: eSpeak NG failed.
            AudioPlaybackError: The audio could not be played.
        """
        protocol_version = request.get(LoaderRequestField.PROTOCOL.value)
        if protocol_version != self.PROTOCOL_VERSION:
            raise LoaderProtocolError(self.UNSUPPORTED_PROTOCOL_MESSAGE.format(
                protocol_version, self.PROTOCOL_VERSION
            ))
        export_path = request.get(LoaderRequestField.EXPORT_PATH.value)
        if export_path:
            self.__synthesize(request, export_path)
            return
        wav_buffer = io.BytesIO()
        self.__synthesize(request, wav_buffer)
        self.__audio_player.play(wav_buffer.getvalue())

    def __synthesize(
        self, request: Dict[str, Any], wav_output: Union[str, BinaryIO]
    ) -> None:
        """Run eSpeak NG with the request's voice and prosody settings.

        Args:
            request: The decoded JSON request.
            wav_output: File path or binary stream that receives the WAV data.

        Returns:
            None.

        Raises:
            NativeSpeechError: eSpeak NG failed.
        """
        synthesize(
            phrase=request[LoaderRequestField.PHRASE.value],
            voice=request[LoaderRequestField.VOICE.value],
            wpm=request[LoaderRequestField.WPM.value],
            pitch=request[LoaderRequestField.PITCH.value],
            amplitude=request[LoaderRequestField.AMPLITUDE.value],
            wordgap=request[LoaderRequestField.WORDGAP.value],
            wav_output=wav_output,
        )

    def __report(self, failure: Exception) -> None:
        """Write a failure to the error stream as one line of JSON.

        Args:
            failure: The exception that ended the request.

        Returns:
            None.

        Raises:
            Nothing.
        """
        json.dump(
            {
                WorkerErrorField.TYPE.value: type(failure).__name__,
                WorkerErrorField.MESSAGE.value: str(failure),
            },
            self.__error_stream,
        )
        self.__error_stream.write("\n")

    def __exit_on_terminate(self, signal_number: int, frame: Optional[FrameType]) -> None:
        """Turn SIGTERM into SystemExit so cleanup code runs before exiting.

        Args:
            signal_number: The received signal.
            frame: The interrupted stack frame.

        Returns:
            None.

        Raises:
            SystemExit: Always.
        """
        # Unwinding through AudioPlayer stops the player process and deletes
        # the temporary WAV; the default SIGTERM action would orphan both.
        raise SystemExit(self.TERMINATED_EXIT_CODE)
