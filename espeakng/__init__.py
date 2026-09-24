# An eSpeak NG TTS binding for Python3.
# Copyright (C) 2016-2020 Sayak Brahmachari.
##
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License Version 3 as published by
# the Free Software Foundation.
##
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
##
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import importlib.util
import json
import os
import platform
import subprocess
import sys

from espeakng.SpeechError import SpeechError
from espeakng.AudioPlayer import AudioPlayer
from espeakng.LoaderRequestField import LoaderRequestField
from espeakng.LoaderUtterance import LoaderUtterance
from espeakng.LoaderWorker import LoaderWorker


class SpeechParameterError(SpeechError):
    def __init__(self, param, val, limits):
        super().__init__("Parameter {} is out of range: {} -> ({}-{}).".format(
            param, val, limits[0], limits[1]))


class Speaker:
    """
    Speaker class for differentiating different speech properties.
    """

    LOADER_MISSING_MESSAGE = (
        "The loader backend requires the 'espeakng-loader' package. "
        "Install it with: pip install 'espeakng[loader]'"
    )
    LOADER_FROZEN_MESSAGE = (
        "The loader backend cannot start its worker from a frozen application; "
        "use backend='cli'"
    )
    # The worker is started from an explicit package location so that a
    # vendored copy, or an unrelated espeakng/ folder in the caller's working
    # directory, cannot change which code the worker runs.
    LOADER_PACKAGE_ROOT = os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
    LOADER_BOOTSTRAP = (
        "import sys; sys.path.insert(0, sys.argv[1]); "
        "from espeakng.LoaderWorker import LoaderWorker; "
        "raise SystemExit(LoaderWorker.for_standard_streams().run())"
    )

    def __init__(self, voice="en", *, backend="auto", **kwargs):
        self.prevproc = None
        self._loader_utterance = None
        self._audio_player = AudioPlayer.for_current_platform()
        Speaker.validate_parameters(kwargs)
        if backend not in ("cli", "loader", "auto"):
            raise ValueError(
                "backend must be one of 'cli', 'loader', or 'auto'"
            )
        self.voice = voice
        self.wpm = kwargs.get("wpm", 175)  # 80-500 (175)
        self.pitch = kwargs.get("pitch", 50)  # 0-99  (50)
        self.amplitude = kwargs.get("amplitude", 100)  # 0-200 (100)
        # The (additional) length of the pause,
        self.wordgap = kwargs.get("wordgap", 0)
        # in units of 10 mS (at the default speed of 170 wpm)

        self.executable = "espeak-ng"
        self.backend = backend

    @property
    def selected_backend(self):
        """Return the backend this speaker will use to speak its next utterance."""
        if self.backend != "auto":
            return self.backend
        return self._backend_for("")

    def _backend_for(self, export_path):
        """Pick the backend for one utterance.

        Raises SpeechError when backend="loader" was requested explicitly but
        cannot serve this utterance; "auto" falls back to the CLI instead.
        """
        if self.backend == "cli" or (
                self.backend == "auto" and self.executable != "espeak-ng"):
            return "cli"
        loader_problem = self._loader_problem(export_path)
        if loader_problem is None:
            return "loader"
        if self.backend == "loader":
            raise SpeechError(loader_problem)
        return "cli"

    def _loader_problem(self, export_path):
        """Return why the loader cannot serve an utterance, or None if it can."""
        if getattr(sys, "frozen", False):
            return Speaker.LOADER_FROZEN_MESSAGE
        if importlib.util.find_spec("espeakng_loader") is None:
            return Speaker.LOADER_MISSING_MESSAGE
        # Exports never need an audio player.
        if not export_path and not self._audio_player.is_available():
            return self._audio_player.missing_player_message()
        return None

    @staticmethod
    def validate_parameters(kwargs):
        limits = {
            "wpm": (80, 500),
            "pitch": (0, 99),
            "amplitude": (0, 200),
            "wordgap": (0, None),
        }

        for param in [key for key in limits.keys() if key in kwargs.keys()]:
            if (kwargs[param] < limits[param][0]
                    or limits[param][1] is not None
                    and kwargs[param] > limits[param][1]):
                raise SpeechParameterError(param, kwargs[param], limits[param])

    @staticmethod
    def list_voices():
        return ["af","sq","am","ar","an","hy","hyw","as","az","ba","cu","eu","be","bn","bpy","bs","bg","my","ca","chr","yue","hak","haw","cmn","hr","cs","da","nl","en-us","en","en-029","en-gb-x-gbclan","en-gb-x-rp","en-gb-scotland","en-gb-x-gbcwmd","eo","et","fa","fa-latn","fi","fr-be","fr","fr-ch","ga","gd","ka","de","grc","el","kl","gn","gu","ht","he","hi","hu","is","id","ia","io","it","ja","kn","kok","ko","ku","kk","ky","la","lb","ltg","lv","lfn","lt","jbo","mi","mk","ms","ml","mt","mr","nci","ne","nb","nog","or","om","pap","py","pl","pt-br","qdb","qu","quc","qya","pt","pa","piqd","ro","ru","ru-lv","uk","sjn","sr","tn","sd","shn","si","sk","sl","smj","es","es-419","sw","sv","ta","th","tk","tt","te","tr","ug","ur","uz","vi-vn-x-central","vi","vi-vn-x-south","cy"]

    def generate_command(self, phrase, export_path="", **kwargs):
        Speaker.validate_parameters(kwargs)
        cmd = [
            self.executable,
            "-v",
            kwargs.get("voice", self.voice),
            "-s",
            kwargs.get("wpm", self.wpm),
            "-p",
            kwargs.get("pitch", self.pitch),
            "-a",
            kwargs.get("amplitude", self.amplitude),
            "-g",
            kwargs.get("wordgap", self.wordgap),
        ]
        if export_path:
            cmd += ['-w', os.path.join(os.getcwd(), export_path)]
        cmd.append(phrase)
        cmd = [str(x) for x in cmd]
        return cmd

    def say(self, phrase, wait4prev=False, export_path="", **kwargs):
        Speaker.validate_parameters(kwargs)
        backend = self._backend_for(export_path)
        if backend == "loader" and "\0" in str(phrase):
            raise ValueError("embedded null byte")
        if self.prevproc:
            if wait4prev:
                self.wait()
            else:
                self.quiet()
        if backend == "loader":
            self._loader_utterance = self._start_loader(phrase, export_path, kwargs)
            self.prevproc = self._loader_utterance.process
        else:
            cmd = self.generate_command(phrase, export_path, **kwargs)
            self._loader_utterance = None
            self.prevproc = self._start_cli(cmd)
            print(cmd)

    def _start_cli(self, cmd):
        popen_kwargs = {"cwd": os.path.dirname(os.path.abspath(__file__))}
        if platform.system() == "Windows":
            popen_kwargs["startupinfo"] = Speaker._hidden_startupinfo()
        return subprocess.Popen(cmd, **popen_kwargs)

    def _start_loader(self, phrase, export_path, kwargs):
        request = {
            LoaderRequestField.PROTOCOL.value: LoaderWorker.PROTOCOL_VERSION,
            LoaderRequestField.PHRASE.value: str(phrase),
            LoaderRequestField.VOICE.value: str(kwargs.get("voice", self.voice)),
            LoaderRequestField.WPM.value: kwargs.get("wpm", self.wpm),
            LoaderRequestField.PITCH.value: kwargs.get("pitch", self.pitch),
            LoaderRequestField.AMPLITUDE.value: kwargs.get("amplitude", self.amplitude),
            LoaderRequestField.WORDGAP.value: kwargs.get("wordgap", self.wordgap),
            LoaderRequestField.EXPORT_PATH.value: (
                os.path.join(os.getcwd(), export_path) if export_path else None
            ),
        }
        cmd = [sys.executable, "-c", Speaker.LOADER_BOOTSTRAP,
               Speaker.LOADER_PACKAGE_ROOT]
        popen_kwargs = {"stdin": subprocess.PIPE, "stderr": subprocess.PIPE}
        if platform.system() == "Windows":
            popen_kwargs["startupinfo"] = Speaker._hidden_startupinfo()
        utterance = LoaderUtterance(subprocess.Popen(cmd, **popen_kwargs))
        utterance.send_request(json.dumps(request).encode("utf-8"))
        return utterance

    @staticmethod
    def _hidden_startupinfo():
        """Return Windows STARTUPINFO that keeps the child's console window hidden."""
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        return startupinfo

    def _current_loader_utterance(self):
        """Return the loader utterance behind prevproc, if prevproc is one."""
        utterance = self._loader_utterance
        if utterance is not None and utterance.process is self.prevproc:
            return utterance
        return None

    def is_talking(self):
        if self.prevproc and self.prevproc.poll() == None:
            return True
        else:
            return False

    def wait(self):
        utterance = self._current_loader_utterance()
        if utterance is not None:
            utterance.wait()
        elif self.prevproc:
            self.prevproc.wait()

    def quiet(self):
        utterance = self._current_loader_utterance()
        if utterance is not None:
            utterance.stop()
        elif self.prevproc:
            self.prevproc.terminate()
