import io
import json
import os
from unittest import mock

import pytest

import espeakng


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


def test_auto_backend_prefers_loader_but_honors_custom_executable():
    speaker = espeakng.Speaker()
    with mock.patch("espeakng.importlib.util.find_spec", return_value=object()):
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
    with mock.patch("espeakng.importlib.util.find_spec", return_value=object()):
        with pytest.raises(ValueError, match="embedded null byte"):
            speaker.say("before\0after")
    previous.terminate.assert_not_called()


def test_loader_sends_versioned_json_request_over_stdin():
    process = mock.Mock()
    process.args = ["python", "-m", "espeakng._loader_worker"]
    process.stdin = NonClosingBytesIO()
    speaker = espeakng.Speaker(backend="loader", voice="es", pitch=70)

    with mock.patch(
        "espeakng.importlib.util.find_spec", return_value=object()
    ), mock.patch(
        "espeakng.platform.system", return_value="Linux"
    ), mock.patch(
        "espeakng.subprocess.Popen", return_value=process
    ) as popen:
        # Keep a reference because _start_loader deliberately detaches process.stdin.
        stdin = process.stdin
        speaker.say("¡Hola!", export_path="output.wav", wpm=220)

    popen.assert_called_once_with(
        [espeakng.sys.executable, "-m", "espeakng._loader_worker"],
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
    speaker.prevproc = process
    speaker._prev_backend = "loader"

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
    speaker.prevproc = process
    speaker._prev_backend = "loader"

    with mock.patch("espeakng.importlib.util.find_spec", return_value=object()), \
            mock.patch("espeakng.subprocess.Popen") as popen:
        with pytest.raises(espeakng.SpeechError, match="Previous synthesis failed"):
            speaker.say("Next", wait4prev=True)

    popen.assert_not_called()
