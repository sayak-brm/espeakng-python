import io
import json
import os
import shutil
import subprocess
import sys
import time
import wave

import pytest

import espeakng


pytest.importorskip("espeakng_loader")


def _assert_valid_wav(path):
    with wave.open(str(path), "rb") as wav_file:
        assert wav_file.getnchannels() == 1
        assert wav_file.getsampwidth() == 2
        assert wav_file.getframerate() > 0
        assert wav_file.getnframes() > 0


def test_loader_exports_unicode_wav(tmp_path):
    output = tmp_path / "speech ü.wav"
    speaker = espeakng.Speaker(backend="loader", voice="es")

    speaker.say("Hola, ¿cómo estás?", export_path=output)
    speaker.wait()

    assert speaker.prevproc.returncode == 0
    assert speaker.is_talking() is False
    _assert_valid_wav(output)


def test_loader_preserves_documented_maximum_wpm(tmp_path):
    output = tmp_path / "fast.wav"
    speaker = espeakng.Speaker(backend="loader", wpm=500)

    speaker.say("Maximum speed", export_path=output)
    speaker.wait()

    assert speaker.prevproc.returncode == 0
    _assert_valid_wav(output)


def test_loader_speakers_are_process_isolated(tmp_path):
    first_output = tmp_path / "first.wav"
    second_output = tmp_path / "second.wav"
    first = espeakng.Speaker(backend="loader", voice="en", pitch=20)
    second = espeakng.Speaker(backend="loader", voice="es", pitch=80)

    first.say("The first independent speaker", export_path=first_output)
    second.say("El segundo altavoz independiente", export_path=second_output)
    first.wait()
    second.wait()

    assert first.prevproc.returncode == 0
    assert second.prevproc.returncode == 0
    _assert_valid_wav(first_output)
    _assert_valid_wav(second_output)


def test_loader_interrupts_previous_utterance(tmp_path):
    interrupted_output = tmp_path / "interrupted.wav"
    replacement_output = tmp_path / "replacement.wav"
    speaker = espeakng.Speaker(backend="loader", wpm=80)

    speaker.say("This utterance should be interrupted. " * 100,
                export_path=interrupted_output)
    first_process = speaker.prevproc
    speaker.say("Replacement", export_path=replacement_output)
    speaker.wait()

    assert first_process.poll() is not None
    assert speaker.prevproc.returncode == 0
    _assert_valid_wav(replacement_output)


def _install_fake_players(tmp_path, monkeypatch, script_body):
    """Put a stand-in for every supported player first on PATH."""
    bin_dir = tmp_path / "fake-bin"
    bin_dir.mkdir()
    for name in ("pw-play", "paplay", "aplay", "afplay"):
        script = bin_dir / name
        script.write_text("#!{}\n{}".format(sys.executable, script_body))
        script.chmod(0o755)
    monkeypatch.setenv("PATH", str(bin_dir) + os.pathsep + os.environ["PATH"])


def _wait_for(path, timeout_seconds):
    deadline = time.monotonic() + timeout_seconds
    while not path.exists():
        assert time.monotonic() < deadline, "timed out waiting for {}".format(path)
        time.sleep(0.05)


def test_loader_wait_can_be_repeated(tmp_path):
    speaker = espeakng.Speaker(backend="loader")

    speaker.say("First", export_path=tmp_path / "first.wav")
    speaker.wait()
    speaker.wait()
    speaker.say("Second", wait4prev=True, export_path=tmp_path / "second.wav")
    speaker.wait()

    _assert_valid_wav(tmp_path / "second.wav")


def test_loader_speaker_recovers_after_worker_error(tmp_path):
    speaker = espeakng.Speaker(backend="loader", voice="no-such-voice")

    speaker.say("Broken", export_path=tmp_path / "broken.wav")
    with pytest.raises(espeakng.SpeechError, match="Setting voice"):
        speaker.wait()
    speaker.voice = "en"
    speaker.say("Recovered", wait4prev=True, export_path=tmp_path / "ok.wav")
    speaker.wait()

    _assert_valid_wav(tmp_path / "ok.wav")


def test_loader_quiet_then_wait4prev_speaks_next(tmp_path):
    speaker = espeakng.Speaker(backend="loader")

    speaker.say("long text " * 20000, export_path=tmp_path / "long.wav")
    speaker.quiet()
    speaker.say("Next", wait4prev=True, export_path=tmp_path / "next.wav")
    speaker.wait()

    _assert_valid_wav(tmp_path / "next.wav")


@pytest.mark.skipif(os.name == "nt", reason="stand-in players are POSIX scripts")
def test_loader_plays_through_system_player(tmp_path, monkeypatch):
    received = tmp_path / "played.wav"
    _install_fake_players(
        tmp_path, monkeypatch,
        "import shutil, sys\nshutil.copy(sys.argv[-1], {!r})\n".format(str(received)),
    )
    speaker = espeakng.Speaker()

    assert speaker.selected_backend == "loader"
    speaker.say("Played aloud")
    speaker.wait()

    _assert_valid_wav(received)


@pytest.mark.skipif(os.name == "nt", reason="stand-in players are POSIX scripts")
def test_loader_quiet_stops_player_and_removes_temporary_file(tmp_path, monkeypatch):
    started = tmp_path / "started.json"
    _install_fake_players(
        tmp_path, monkeypatch,
        "import json, os, sys, time\n"
        "open({!r}, 'w').write(json.dumps([os.getpid(), sys.argv[-1]]))\n"
        "time.sleep(60)\n".format(str(started)),
    )
    speaker = espeakng.Speaker(backend="loader")

    speaker.say("Interrupted while playing")
    _wait_for(started, 10)
    speaker.quiet()
    speaker.wait()

    player_pid, wav_path = json.loads(started.read_text())
    with pytest.raises(ProcessLookupError):
        os.kill(player_pid, 0)
    assert not os.path.exists(wav_path)


def test_loader_worker_runs_vendored_package_from_other_directory(tmp_path):
    project = tmp_path / "project"
    shutil.copytree(
        os.path.dirname(espeakng.__file__), str(project / "espeakng"),
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    output = tmp_path / "vendored.wav"
    (project / "app.py").write_text(
        "import espeakng\n"
        "speaker = espeakng.Speaker(backend='loader')\n"
        "speaker.say('Vendored', export_path={!r})\n"
        "speaker.wait()\n".format(str(output))
    )
    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)

    subprocess.run(
        [sys.executable, str(project / "app.py")],
        cwd=str(tmp_path), env=environment, check=True,
    )

    _assert_valid_wav(output)


def test_native_initialization_failure_raises_instead_of_exiting(monkeypatch):
    import espeakng_loader
    from espeakng._native import NativeSpeechError, synthesize

    monkeypatch.setattr(
        espeakng_loader, "get_data_path", lambda: "/nonexistent/espeak-ng-data"
    )

    with pytest.raises(NativeSpeechError, match="Unable to initialize"):
        synthesize("Hello", "en", 175, 50, 100, 0, io.BytesIO())
