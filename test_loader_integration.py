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
