import errno
import json
import subprocess
from typing import ClassVar, Optional

from espeakng.SpeechError import SpeechError
from espeakng.WorkerErrorField import WorkerErrorField


class LoaderUtterance:
    """Tracks one loader worker process from request to collected result.

    The worker's outcome is collected exactly once and remembered, so waiting
    again is safe, and an error is raised once rather than on every wait.
    """

    WORKER_OUTPUT_ENCODING: ClassVar[str] = "utf-8"
    EXIT_CODE_MESSAGE: ClassVar[str] = "Loader worker exited with code {}"
    NO_REQUEST_READ_MESSAGE: ClassVar[str] = (
        "Loader worker exited before reading its request"
    )
    # A worker blocked inside a long native synthesis call only handles
    # SIGTERM once that call returns, so give it this long before killing it.
    STOP_GRACE_SECONDS: ClassVar[float] = 1.0

    def __init__(self, process: subprocess.Popen) -> None:
        """Track a worker started with stdin and stderr pipes.

        Args:
            process: The running worker process.

        Returns:
            None.

        Raises:
            Nothing.
        """
        self.__process = process
        self.__collected = False
        self.__stopped = False
        self.__pending_error: Optional[SpeechError] = None

    @property
    def process(self) -> subprocess.Popen:
        """The worker process.

        Args:
            None.

        Returns:
            The Popen object this utterance tracks.

        Raises:
            Nothing.
        """
        return self.__process

    def send_request(self, request_bytes: bytes) -> None:
        """Send the complete request to the worker and close its stdin.

        Args:
            request_bytes: The encoded JSON request.

        Returns:
            None.

        Raises:
            SpeechError: The worker exited before reading the request.
            OSError: Writing the request failed for another reason.
        """
        try:
            self.__process.stdin.write(request_bytes)
            self.__process.stdin.close()
        except OSError as write_error:
            self.__discard_stdin()
            if not self.__is_closed_pipe(write_error):
                self.stop()
                raise
            self.wait()
            raise SpeechError(self.NO_REQUEST_READ_MESSAGE) from None
        except BaseException:
            self.__discard_stdin()
            self.stop()
            raise
        # communicate() must not try to use the stdin pipe we just closed.
        self.__process.stdin = None

    def wait(self) -> None:
        """Wait for the worker to finish and report its failure, once.

        Args:
            None.

        Returns:
            None.

        Raises:
            SpeechError: The worker failed, and that failure was not yet reported.
        """
        self.__collect()
        pending_error, self.__pending_error = self.__pending_error, None
        if pending_error is not None:
            raise pending_error

    def stop(self) -> None:
        """Stop the worker and reap it; an intentional stop is not a failure.

        Args:
            None.

        Returns:
            None.

        Raises:
            Nothing.
        """
        if self.__collected:
            return
        # Recorded before terminating: on Windows a terminated process exits
        # with code 1, which is indistinguishable from a worker error.
        self.__stopped = True
        self.__terminate_promptly()
        self.__collect()

    def __terminate_promptly(self) -> None:
        """Ask the worker to exit, killing it if it does not exit in time.

        Args:
            None.

        Returns:
            None.

        Raises:
            Nothing.
        """
        self.__process.terminate()
        try:
            self.__process.wait(timeout=self.STOP_GRACE_SECONDS)
        except subprocess.TimeoutExpired:
            self.__process.kill()

    def __discard_stdin(self) -> None:
        """Close the request pipe after a failed write, ignoring a broken pipe.

        Args:
            None.

        Returns:
            None.

        Raises:
            Nothing.
        """
        stdin = self.__process.stdin
        self.__process.stdin = None
        try:
            stdin.close()
        except OSError:
            # Closing flushes buffered bytes into the same dead pipe.
            pass

    def __is_closed_pipe(self, write_error: OSError) -> bool:
        """Report whether a write failed because the worker closed its end of the pipe.

        Args:
            write_error: The error raised while writing the request.

        Returns:
            True for a broken pipe; Windows reports that case as EINVAL.

        Raises:
            Nothing.
        """
        return (isinstance(write_error, BrokenPipeError)
                or write_error.errno == errno.EINVAL)

    def __collect(self) -> None:
        """Wait for exit, read stderr, and record any failure, only on the first call.

        Args:
            None.

        Returns:
            None.

        Raises:
            Nothing.
        """
        if self.__collected:
            return
        _stdout, worker_stderr = self.__process.communicate()
        self.__collected = True
        if self.__process.returncode and not self.__stopped:
            self.__pending_error = SpeechError(self.__failure_message(worker_stderr))

    def __failure_message(self, worker_stderr: Optional[bytes]) -> str:
        """Extract the worker's error message from its stderr.

        Args:
            worker_stderr: Everything the worker wrote to stderr.

        Returns:
            The JSON error's message, the raw stderr text, or the exit code.

        Raises:
            Nothing.
        """
        exit_code_message = self.EXIT_CODE_MESSAGE.format(self.__process.returncode)
        if not worker_stderr:
            return exit_code_message
        try:
            worker_error = json.loads(worker_stderr.decode(self.WORKER_OUTPUT_ENCODING))
            return str(worker_error.get(WorkerErrorField.MESSAGE.value, exit_code_message))
        except (UnicodeDecodeError, ValueError, AttributeError):
            # Not our JSON error, e.g. a traceback from a worker that failed to start.
            return worker_stderr.decode(
                self.WORKER_OUTPUT_ENCODING, errors="replace"
            ).strip()
