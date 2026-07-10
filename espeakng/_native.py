"""Minimal, typed bindings for the eSpeak NG shared library."""

import ctypes
import os
from pathlib import Path
import wave


AUDIO_OUTPUT_SYNCHRONOUS = 2
AUDIO_OUTPUT_SYNCH_PLAYBACK = 3

EE_OK = 0
ESPEAK_CHARS_UTF8 = 1

ESPEAK_RATE = 1
ESPEAK_VOLUME = 2
ESPEAK_PITCH = 3
ESPEAK_WORDGAP = 7

_SYNTH_CALLBACK = ctypes.CFUNCTYPE(
    ctypes.c_int,
    ctypes.POINTER(ctypes.c_short),
    ctypes.c_int,
    ctypes.c_void_p,
)


class NativeSpeechError(RuntimeError):
    """Raised when the eSpeak NG C API reports an error."""


def _check(result, operation):
    if result != EE_OK:
        raise NativeSpeechError(
            "{} failed with eSpeak NG error code {}".format(operation, result)
        )


def _load_library():
    try:
        import espeakng_loader
    except ImportError as exc:
        raise NativeSpeechError(
            "The loader backend requires the 'espeakng-loader' package. "
            "Install it with: pip install 'espeakng[loader]'"
        ) from exc

    library_path = espeakng_loader.get_library_path()
    data_path = Path(espeakng_loader.get_data_path())

    try:
        library = ctypes.CDLL(library_path)
    except OSError as exc:
        raise NativeSpeechError(
            "Unable to load the eSpeak NG shared library at {!r}: {}".format(
                library_path, exc
            )
        ) from exc

    library.espeak_Initialize.argtypes = [
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_int,
    ]
    library.espeak_Initialize.restype = ctypes.c_int

    library.espeak_SetSynthCallback.argtypes = [_SYNTH_CALLBACK]
    library.espeak_SetSynthCallback.restype = None

    library.espeak_SetVoiceByName.argtypes = [ctypes.c_char_p]
    library.espeak_SetVoiceByName.restype = ctypes.c_int

    library.espeak_SetParameter.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int]
    library.espeak_SetParameter.restype = ctypes.c_int

    library.espeak_Synth.argtypes = [
        ctypes.c_void_p,
        ctypes.c_size_t,
        ctypes.c_uint,
        ctypes.c_int,
        ctypes.c_uint,
        ctypes.c_uint,
        ctypes.POINTER(ctypes.c_uint),
        ctypes.c_void_p,
    ]
    library.espeak_Synth.restype = ctypes.c_int

    library.espeak_Synchronize.argtypes = []
    library.espeak_Synchronize.restype = ctypes.c_int

    library.espeak_Terminate.argtypes = []
    library.espeak_Terminate.restype = ctypes.c_int

    # espeak_Initialize expects the directory containing espeak-ng-data.
    return library, os.fsencode(str(data_path.parent))


def synthesize(phrase, voice, wpm, pitch, amplitude, wordgap, export_path=None):
    """Synthesize one utterance, optionally streaming it to a WAV file."""
    library, data_parent = _load_library()
    output = (
        AUDIO_OUTPUT_SYNCHRONOUS
        if export_path
        else AUDIO_OUTPUT_SYNCH_PLAYBACK
    )
    sample_rate = library.espeak_Initialize(output, 0, data_parent, 0)
    if sample_rate < 0:
        raise NativeSpeechError("Unable to initialize eSpeak NG")

    wav_file = None
    callback_error = []

    try:
        if export_path:
            wav_file = wave.open(export_path, "wb")
            wav_file.setnchannels(1)
            wav_file.setsampwidth(ctypes.sizeof(ctypes.c_short))
            wav_file.setframerate(sample_rate)

        def on_audio(samples, sample_count, _events):
            if not wav_file or not samples or sample_count <= 0:
                return 0
            try:
                wav_file.writeframesraw(
                    ctypes.string_at(
                        samples,
                        sample_count * ctypes.sizeof(ctypes.c_short),
                    )
                )
            except BaseException as exc:  # ctypes callbacks must not leak exceptions.
                callback_error.append(exc)
                return 1
            return 0

        callback = _SYNTH_CALLBACK(on_audio)
        library.espeak_SetSynthCallback(callback)

        _check(
            library.espeak_SetVoiceByName(voice.encode("utf-8")),
            "Setting voice {!r}".format(voice),
        )
        for parameter, value, name in (
            (ESPEAK_RATE, wpm, "wpm"),
            (ESPEAK_PITCH, pitch, "pitch"),
            (ESPEAK_VOLUME, amplitude, "amplitude"),
            (ESPEAK_WORDGAP, wordgap, "wordgap"),
        ):
            _check(
                library.espeak_SetParameter(parameter, int(value), 0),
                "Setting {}".format(name),
            )

        encoded_phrase = phrase.encode("utf-8")
        text_buffer = ctypes.create_string_buffer(encoded_phrase)
        identifier = ctypes.c_uint(0)
        _check(
            library.espeak_Synth(
                text_buffer,
                len(encoded_phrase) + 1,
                0,
                0,
                0,
                ESPEAK_CHARS_UTF8,
                ctypes.byref(identifier),
                None,
            ),
            "Synthesizing speech",
        )
        _check(library.espeak_Synchronize(), "Waiting for speech")

        if callback_error:
            raise NativeSpeechError(
                "Writing synthesized audio failed: {}".format(callback_error[0])
            )
    finally:
        if wav_file is not None:
            wav_file.close()
        library.espeak_Terminate()
