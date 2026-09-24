import os
import platform
import shutil
import subprocess
import tempfile
from typing import Callable, ClassVar, Dict, List, Optional, Tuple

from espeakng.AudioPlaybackError import AudioPlaybackError
from espeakng.OperatingSystem import OperatingSystem


class AudioPlayer:
    """Plays WAV audio through a player that ships with the operating system.

    The bundled eSpeak NG libraries are built without an audio backend, so the
    loader backend synthesizes to WAV and hands the result to this class.
    """

    COMMAND_CANDIDATES_BY_SYSTEM: ClassVar[Dict[str, Tuple[Tuple[str, ...], ...]]] = {
        OperatingSystem.DARWIN.value: (("afplay",),),
    }
    # Linux and other Unix-likes: PipeWire, then PulseAudio, then raw ALSA.
    FALLBACK_COMMAND_CANDIDATES: ClassVar[Tuple[Tuple[str, ...], ...]] = (
        ("pw-play",),
        ("paplay",),
        ("aplay", "-q"),
    )
    TEMPORARY_FILE_SUFFIX: ClassVar[str] = ".wav"
    NO_PLAYER_MESSAGE: ClassVar[str] = (
        "No audio player found. Install one of: {}, or pass export_path "
        "to write a WAV file instead."
    )
    PLAYER_FAILURE_MESSAGE: ClassVar[str] = "{} exited with code {}: {}"
    PLAYER_OUTPUT_ENCODING: ClassVar[str] = "utf-8"

    def __init__(
        self,
        system_name: str,
        executable_finder: Callable[[str], Optional[str]],
    ) -> None:
        """Create a player for one operating system.

        Args:
            system_name: Operating system name as returned by ``platform.system()``.
            executable_finder: Resolves a program name to its path, or None
                when the program is not installed (``shutil.which`` in practice).

        Returns:
            None.

        Raises:
            Nothing.
        """
        self.__system_name = system_name
        self.__executable_finder = executable_finder

    @classmethod
    def for_current_platform(cls) -> "AudioPlayer":
        """Create a player for the operating system this process runs on.

        Args:
            None.

        Returns:
            An AudioPlayer that looks up players on the current PATH.

        Raises:
            Nothing.
        """
        return cls(platform.system(), shutil.which)

    def is_available(self) -> bool:
        """Report whether this machine has a way to play audio.

        Args:
            None.

        Returns:
            True when play() has a player to use.

        Raises:
            Nothing.
        """
        return self.__uses_winsound() or self.__find_command() is not None

    def play(self, wav_bytes: bytes) -> None:
        """Play a complete WAV file and return once playback has finished.

        Args:
            wav_bytes: The WAV file contents, header included.

        Returns:
            None.

        Raises:
            AudioPlaybackError: No player is installed, or the player failed.
        """
        if self.__uses_winsound():
            self.__play_with_winsound(wav_bytes)
            return
        command = self.__find_command()
        if command is None:
            raise AudioPlaybackError(self.missing_player_message())
        self.__play_with_command(command, wav_bytes)

    def __uses_winsound(self) -> bool:
        """Report whether playback goes through the standard-library winsound module.

        Args:
            None.

        Returns:
            True on Windows.

        Raises:
            Nothing.
        """
        return self.__system_name == OperatingSystem.WINDOWS.value

    def __command_candidates(self) -> Tuple[Tuple[str, ...], ...]:
        """List the player commands to try on this operating system, in order.

        Args:
            None.

        Returns:
            Candidate commands; the first element of each is the program name.

        Raises:
            Nothing.
        """
        return self.COMMAND_CANDIDATES_BY_SYSTEM.get(
            self.__system_name, self.FALLBACK_COMMAND_CANDIDATES
        )

    def __find_command(self) -> Optional[List[str]]:
        """Find the first installed player command.

        Args:
            None.

        Returns:
            The command with its program resolved to a full path, or None.

        Raises:
            Nothing.
        """
        for candidate in self.__command_candidates():
            program_path = self.__executable_finder(candidate[0])
            if program_path:
                return [program_path, *candidate[1:]]
        return None

    def missing_player_message(self) -> str:
        """Build the error message listing the players that are looked for.

        Args:
            None.

        Returns:
            A message naming every candidate program.

        Raises:
            Nothing.
        """
        program_names = [candidate[0] for candidate in self.__command_candidates()]
        return self.NO_PLAYER_MESSAGE.format(", ".join(program_names))

    def __play_with_winsound(self, wav_bytes: bytes) -> None:
        """Play audio in-process on Windows.

        Args:
            wav_bytes: The WAV file contents.

        Returns:
            None.

        Raises:
            RuntimeError: Windows could not play the sound.
        """
        # winsound only exists on Windows, so it cannot be imported at module level.
        import winsound

        # SND_NODEFAULT stops Windows from playing its default beep on failure.
        winsound.PlaySound(wav_bytes, winsound.SND_MEMORY | winsound.SND_NODEFAULT)

    def __play_with_command(self, command: List[str], wav_bytes: bytes) -> None:
        """Play audio through an external player, which needs a real file.

        Args:
            command: The player command, without the file argument.
            wav_bytes: The WAV file contents.

        Returns:
            None.

        Raises:
            AudioPlaybackError: The player exited with an error.
        """
        wav_path = self.__write_temporary_wav(wav_bytes)
        try:
            self.__run_player([*command, wav_path])
        finally:
            os.remove(wav_path)

    def __write_temporary_wav(self, wav_bytes: bytes) -> str:
        """Write audio to a new temporary file.

        Args:
            wav_bytes: The WAV file contents.

        Returns:
            The path of the temporary file; the caller removes it.

        Raises:
            OSError: The file could not be written.
        """
        file_descriptor, wav_path = tempfile.mkstemp(suffix=self.TEMPORARY_FILE_SUFFIX)
        with os.fdopen(file_descriptor, "wb") as wav_file:
            wav_file.write(wav_bytes)
        return wav_path

    def __run_player(self, command: List[str]) -> None:
        """Run a player to completion, never letting it outlive this process's request.

        Args:
            command: The full player command, file argument included.

        Returns:
            None.

        Raises:
            AudioPlaybackError: The player exited with a nonzero code.
        """
        # The player gets its own stderr pipe so it never holds the worker's
        # stderr open, which the parent reads until EOF.
        player = subprocess.Popen(
            command, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        try:
            _stdout, player_stderr = player.communicate()
        finally:
            # Reached with SystemExit when the worker is told to stop mid-playback.
            if player.poll() is None:
                player.terminate()
                player.wait()
        if player.returncode != 0:
            raise AudioPlaybackError(self.PLAYER_FAILURE_MESSAGE.format(
                command[0], player.returncode,
                player_stderr.decode(self.PLAYER_OUTPUT_ENCODING, errors="replace").strip(),
            ))
