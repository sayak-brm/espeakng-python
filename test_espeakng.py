import errno
import io
import json
import os
import subprocess
import sys
from unittest import mock

import pytest

import espeakng
from espeakng.AudioPlaybackError import AudioPlaybackError


class NonClosingBytesIO(io.BytesIO):
    def close(self):
        pass


def test_defaults_and_command_generation():
    speaker = espeakng.Speaker()

    assert speaker.voice == "en"
    assert speaker.wpm == 175
    assert speaker.pitch == 50
    assert speaker.amplitude == 100
    assert speaker.wordgap == 0
    assert speaker.backend == "auto"
    with mock.patch("espeakng.importlib.util.find_spec", return_value=None):
        assert speaker.selected_backend == "cli"
    assert speaker.generate_command("Hello") == [
        "espeak-ng", "-v", "en", "-s", "175", "-p", "50",
        "-a", "100", "-g", "0", "Hello",
    ]


def test_command_generation_applies_overrides_and_absolute_export_path():
    speaker = espeakng.Speaker(voice="en-us", wpm=200, pitch=60)
    command = speaker.generate_command(
        "Hello", "speech.wav", voice="es", wpm=240, wordgap=3
    )

    assert command == [
        "espeak-ng", "-v", "es", "-s", "240", "-p", "60",
        "-a", "100", "-g", "3", "-w",
        os.path.join(os.getcwd(), "speech.wav"), "Hello",
    ]


@pytest.mark.parametrize(
    ("name", "value", "limits"),
    [
        ("wpm", 79, (80, 500)),
        ("wpm", 501, (80, 500)),
        ("pitch", -1, (0, 99)),
        ("pitch", 100, (0, 99)),
        ("amplitude", -1, (0, 200)),
        ("amplitude", 201, (0, 200)),
        ("wordgap", -1, (0, None)),
    ],
)
def test_parameter_validation(name, value, limits):
    with pytest.raises(espeakng.SpeechParameterError) as caught:
        espeakng.Speaker(**{name: value})

    assert str(caught.value) == (
        "Parameter {} is out of range: {} -> ({}-{}).".format(
            name, value, limits[0], limits[1]
        )
    )


def test_cli_say_starts_in_package_directory_and_interrupts_previous_process():
    first = mock.Mock()
    second = mock.Mock()
    speaker = espeakng.Speaker(backend="cli")
    speaker.prevproc = first

    with mock.patch("espeakng.platform.system", return_value="Linux"), mock.patch(
        "espeakng.subprocess.Popen", return_value=second
    ) as popen:
        speaker.say("Hello")

    first.terminate.assert_called_once_with()
    first.wait.assert_not_called()
    popen.assert_called_once_with(
        speaker.generate_command("Hello"),
        cwd=os.path.dirname(os.path.abspath(espeakng.__file__)),
    )
    assert speaker.prevproc is second


def test_wait4prev_waits_instead_of_interrupting():
    previous = mock.Mock()
    speaker = espeakng.Speaker(backend="cli")
    speaker.prevproc = previous

    with mock.patch("espeakng.platform.system", return_value="Linux"), mock.patch(
        "espeakng.subprocess.Popen", return_value=mock.Mock()
    ):
        speaker.say("Hello", wait4prev=True)

    previous.wait.assert_called_once_with()
    previous.terminate.assert_not_called()


def test_process_helpers_preserve_existing_semantics():
    process = mock.Mock()
    process.poll.return_value = None
    speaker = espeakng.Speaker()
    speaker.prevproc = process

    assert speaker.is_talking() is True
    speaker.wait()
    speaker.quiet()

    process.wait.assert_called_once_with()
    process.terminate.assert_called_once_with()


def test_invalid_backend_is_rejected():
    with pytest.raises(ValueError, match="backend must be one of"):
        espeakng.Speaker(backend="unknown")


def loader_installed():
    return mock.patch("espeakng.importlib.util.find_spec", return_value=object())


def audio_player_available(available):
    return mock.patch.object(
        espeakng.AudioPlayer, "is_available", return_value=available
    )


def test_auto_backend_prefers_loader_but_honors_custom_executable():
    speaker = espeakng.Speaker()
    with loader_installed(), audio_player_available(True):
        assert speaker.selected_backend == "loader"
        speaker.executable = "custom-espeak-ng"
        assert speaker.selected_backend == "cli"


def test_explicit_loader_reports_missing_extra_before_launching():
    speaker = espeakng.Speaker(backend="loader")
    previous = mock.Mock()
    speaker.prevproc = previous
    with mock.patch("espeakng.importlib.util.find_spec", return_value=None):
        with pytest.raises(espeakng.SpeechError, match="espeakng-loader"):
            speaker.say("Hello")
    previous.terminate.assert_not_called()
    previous.wait.assert_not_called()


def test_loader_rejects_embedded_null_before_interrupting():
    speaker = espeakng.Speaker(backend="loader")
    previous = mock.Mock()
    speaker.prevproc = previous
    with loader_installed(), audio_player_available(True):
        with pytest.raises(ValueError, match="embedded null byte"):
            speaker.say("before\0after")
    previous.terminate.assert_not_called()


def test_loader_sends_versioned_json_request_over_stdin():
    process = mock.Mock()
    process.stdin = NonClosingBytesIO()
    speaker = espeakng.Speaker(backend="loader", voice="es", pitch=70)

    with loader_installed(), mock.patch(
        "espeakng.platform.system", return_value="Linux"
    ), mock.patch(
        "espeakng.subprocess.Popen", return_value=process
    ) as popen:
        # Keep a reference because send_request deliberately detaches process.stdin.
        stdin = process.stdin
        speaker.say("¡Hola!", export_path="output.wav", wpm=220)

    popen.assert_called_once_with(
        [
            sys.executable, "-c", espeakng.Speaker.LOADER_BOOTSTRAP,
            espeakng.Speaker.LOADER_PACKAGE_ROOT,
        ],
        stdin=espeakng.subprocess.PIPE,
        stderr=espeakng.subprocess.PIPE,
    )
    payload = json.loads(stdin.getvalue().decode("utf-8"))
    assert payload == {
        "protocol": 1,
        "phrase": "¡Hola!",
        "voice": "es",
        "wpm": 220,
        "pitch": 70,
        "amplitude": 100,
        "wordgap": 0,
        "export_path": os.path.join(os.getcwd(), "output.wav"),
    }


def test_loader_wait_raises_worker_error():
    process = mock.Mock()
    process.returncode = 1
    process.communicate.return_value = (
        None,
        json.dumps({
            "type": "NativeSpeechError",
            "message": "Setting voice failed",
        }).encode("utf-8"),
    )
    speaker = espeakng.Speaker(backend="loader")
    speaker._loader_utterance = espeakng.LoaderUtterance(process)
    speaker.prevproc = process

    with pytest.raises(espeakng.SpeechError, match="Setting voice failed"):
        speaker.wait()


def test_wait4prev_propagates_loader_error_before_starting_next_utterance():
    process = mock.Mock()
    process.returncode = 1
    process.communicate.return_value = (
        None,
        json.dumps({"message": "Previous synthesis failed"}).encode("utf-8"),
    )
    speaker = espeakng.Speaker(backend="loader")
    speaker._loader_utterance = espeakng.LoaderUtterance(process)
    speaker.prevproc = process

    with loader_installed(), audio_player_available(True), \
            mock.patch("espeakng.subprocess.Popen") as popen:
        with pytest.raises(espeakng.SpeechError, match="Previous synthesis failed"):
            speaker.say("Next", wait4prev=True)

    popen.assert_not_called()


def failed_worker_process(message):
    process = mock.Mock()
    process.returncode = 1
    process.communicate.return_value = (
        None, json.dumps({"message": message}).encode("utf-8"),
    )
    return process


def test_package_exports_one_speech_error_hierarchy():
    from espeakng import SpeechError

    assert espeakng.SpeechError is SpeechError
    assert issubclass(espeakng.SpeechParameterError, SpeechError)


def test_loader_error_is_reported_once_and_wait_can_repeat():
    process = failed_worker_process("Synthesis failed")
    utterance = espeakng.LoaderUtterance(process)

    with pytest.raises(espeakng.SpeechError, match="Synthesis failed"):
        utterance.wait()
    utterance.wait()
    utterance.wait()

    process.communicate.assert_called_once_with()


def test_speaker_recovers_after_reporting_loader_error():
    process = failed_worker_process("Previous synthesis failed")
    speaker = espeakng.Speaker(backend="loader")
    speaker._loader_utterance = espeakng.LoaderUtterance(process)
    speaker.prevproc = process
    next_process = mock.Mock()
    next_process.stdin = NonClosingBytesIO()

    with loader_installed(), mock.patch(
        "espeakng.subprocess.Popen", return_value=next_process
    ):
        with pytest.raises(espeakng.SpeechError):
            speaker.say("Next", wait4prev=True, export_path="next.wav")
        speaker.say("Next", wait4prev=True, export_path="next.wav")

    assert speaker.prevproc is next_process


def test_stopping_loader_utterance_is_not_an_error():
    # A terminated worker exits nonzero (1 on Windows, -15 on POSIX).
    process = failed_worker_process("ignored")
    utterance = espeakng.LoaderUtterance(process)

    utterance.stop()
    utterance.wait()

    process.terminate.assert_called_once_with()
    process.communicate.assert_called_once_with()


def test_stop_kills_worker_that_ignores_terminate():
    process = failed_worker_process("ignored")
    process.wait.side_effect = subprocess.TimeoutExpired("worker", 1)
    utterance = espeakng.LoaderUtterance(process)

    utterance.stop()

    process.kill.assert_called_once_with()


def test_quiet_then_wait4prev_speaks_next_loader_utterance():
    process = failed_worker_process("ignored")
    speaker = espeakng.Speaker(backend="loader")
    speaker._loader_utterance = espeakng.LoaderUtterance(process)
    speaker.prevproc = process
    next_process = mock.Mock()
    next_process.stdin = NonClosingBytesIO()

    with loader_installed(), mock.patch(
        "espeakng.subprocess.Popen", return_value=next_process
    ):
        speaker.quiet()
        speaker.say("Next", wait4prev=True, export_path="next.wav")

    assert speaker.prevproc is next_process


def test_broken_request_pipe_reports_worker_stderr():
    process = failed_worker_process("Worker could not start")
    process.stdin = mock.Mock()
    process.stdin.write.side_effect = BrokenPipeError()
    process.stdin.close.side_effect = BrokenPipeError()
    utterance = espeakng.LoaderUtterance(process)

    with pytest.raises(espeakng.SpeechError, match="Worker could not start"):
        utterance.send_request(b"{}")


def test_worker_that_exits_immediately_raises_speech_error(tmp_path):
    # A phrase larger than the pipe buffer makes the request write itself fail.
    speaker = espeakng.Speaker(backend="loader")
    failing_bootstrap = (
        "import sys; sys.stderr.write('worker failed to start'); sys.exit(1)"
    )

    with loader_installed(), mock.patch.object(
        espeakng.Speaker, "LOADER_BOOTSTRAP", failing_bootstrap
    ):
        with pytest.raises(espeakng.SpeechError, match="worker failed to start"):
            speaker.say("x" * 200000, export_path=str(tmp_path / "out.wav"))
            speaker.wait()


def test_auto_uses_loader_for_export_but_cli_for_playback_without_player():
    speaker = espeakng.Speaker()

    with loader_installed(), audio_player_available(False):
        assert speaker.selected_backend == "cli"
        assert speaker._backend_for("speech.wav") == "loader"


def test_explicit_loader_without_player_fails_before_interrupting():
    speaker = espeakng.Speaker(backend="loader")
    previous = mock.Mock()
    speaker.prevproc = previous

    with loader_installed(), audio_player_available(False):
        with pytest.raises(espeakng.SpeechError, match="No audio player found"):
            speaker.say("Hello")

    previous.terminate.assert_not_called()


def test_frozen_application_falls_back_to_cli_or_rejects_explicit_loader():
    with loader_installed(), audio_player_available(True), \
            mock.patch.object(espeakng.sys, "frozen", True, create=True):
        assert espeakng.Speaker().selected_backend == "cli"
        with pytest.raises(espeakng.SpeechError, match="frozen"):
            espeakng.Speaker(backend="loader").say("Hello", export_path="a.wav")


def test_loader_is_not_asked_for_cli_command():
    speaker = espeakng.Speaker(backend="loader")
    process = mock.Mock()
    process.stdin = NonClosingBytesIO()

    with loader_installed(), mock.patch(
        "espeakng.subprocess.Popen", return_value=process
    ), mock.patch.object(espeakng.Speaker, "generate_command") as generate:
        speaker.say("Hello", export_path="speech.wav")

    generate.assert_not_called()


def test_audio_player_prefers_platform_players_in_order():
    installed = {"paplay": "/usr/bin/paplay", "aplay": "/usr/bin/aplay"}
    linux = espeakng.AudioPlayer("Linux", installed.get)
    mac = espeakng.AudioPlayer("Darwin", {"afplay": "/usr/bin/afplay"}.get)
    bare = espeakng.AudioPlayer("Linux", {}.get)

    assert linux.is_available() is True
    assert linux._AudioPlayer__find_command() == ["/usr/bin/paplay"]
    assert mac._AudioPlayer__find_command() == ["/usr/bin/afplay"]
    assert bare.is_available() is False
    assert espeakng.AudioPlayer("Windows", {}.get).is_available() is True


def test_audio_player_without_player_raises():
    player = espeakng.AudioPlayer("Linux", {}.get)

    with pytest.raises(AudioPlaybackError, match="pw-play, paplay, aplay"):
        player.play(b"RIFF")


def test_audio_player_uses_winsound_without_default_beep():
    winsound = mock.Mock(SND_MEMORY=4, SND_NODEFAULT=2)

    with mock.patch.dict(sys.modules, {"winsound": winsound}):
        espeakng.AudioPlayer("Windows", {}.get).play(b"RIFF")

    winsound.PlaySound.assert_called_once_with(b"RIFF", 4 | 2)


@pytest.mark.skipif(os.name == "nt", reason="uses a POSIX shebang script")
def test_audio_player_runs_player_and_removes_temporary_file(tmp_path):
    received = tmp_path / "received.wav"
    played_path = tmp_path / "played-path.txt"
    player_script = tmp_path / "aplay"
    player_script.write_text(
        "#!{}\nimport shutil, sys\n"
        "shutil.copy(sys.argv[-1], {!r})\n"
        "open({!r}, 'w').write(sys.argv[-1])\n".format(
            sys.executable, str(received), str(played_path)
        )
    )
    player_script.chmod(0o755)
    player = espeakng.AudioPlayer("Linux", {"aplay": str(player_script)}.get)

    player.play(b"RIFF-data")

    assert received.read_bytes() == b"RIFF-data"
    assert not os.path.exists(played_path.read_text())


@pytest.mark.skipif(os.name == "nt", reason="uses a POSIX shebang script")
def test_audio_player_reports_player_failure(tmp_path):
    player_script = tmp_path / "aplay"
    player_script.write_text(
        "#!{}\nimport sys\nsys.stderr.write('no soundcard')\nsys.exit(3)\n".format(
            sys.executable
        )
    )
    player_script.chmod(0o755)
    player = espeakng.AudioPlayer("Linux", {"aplay": str(player_script)}.get)

    with pytest.raises(AudioPlaybackError, match="code 3: no soundcard"):
        player.play(b"RIFF")


def test_loader_worker_reports_unsupported_protocol_as_json():
    errors = io.StringIO()
    worker = espeakng.LoaderWorker(
        io.BytesIO(json.dumps({"protocol": 99}).encode("utf-8")),
        errors,
        mock.Mock(),
    )

    with mock.patch("signal.signal"):
        exit_code = worker.run()

    assert exit_code == espeakng.LoaderWorker.FAILURE_EXIT_CODE
    assert json.loads(errors.getvalue())["type"] == "LoaderProtocolError"


def test_windows_closed_pipe_error_reports_worker_stderr():
    process = failed_worker_process("Worker could not start")
    process.stdin = mock.Mock()
    process.stdin.write.side_effect = OSError(errno.EINVAL, "Invalid argument")
    utterance = espeakng.LoaderUtterance(process)

    with pytest.raises(espeakng.SpeechError, match="Worker could not start"):
        utterance.send_request(b"{}")


def test_unrelated_request_write_error_stops_worker_and_propagates():
    process = failed_worker_process("ignored")
    process.stdin = mock.Mock()
    process.stdin.write.side_effect = OSError(errno.EIO, "I/O error")
    utterance = espeakng.LoaderUtterance(process)

    with pytest.raises(OSError, match="I/O error"):
        utterance.send_request(b"{}")

    process.terminate.assert_called_once_with()
