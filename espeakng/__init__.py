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
import os
import platform
import subprocess


class SpeechError(Exception):
    pass


class SpeechParameterError(SpeechError):
    def __init__(self, param, val, limits):
        super().__init__("Parameter {} is out of range: {} -> ({}-{}).".format(
            param, val, limits[0], limits[1]))


class Speaker:
    """
    Speaker class for differentiating different speech properties.
    """

    def __init__(self, voice="en", **kwargs):
        self.prevproc = None
        Speaker.validate_parameters(kwargs)
        self.voice = kwargs.get("voice", "en")
        self.wpm = kwargs.get("wpm", 175)  # 80-500 (175)
        self.pitch = kwargs.get("pitch", 50)  # 0-99  (50)
        self.amplitude = kwargs.get("amplitude", 100)  # 0-200 (100)
        # The (additional) length of the pause,
        self.wordgap = kwargs.get("wordgap", 0)
        # in units of 10 mS (at the default speed of 170 wpm)

        self.executable = "espeak-ng"

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

    def generate_command(self, phrase, **kwargs):
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
            phrase,
        ]
        cmd = [str(x) for x in cmd]
        return cmd

    def say(self, phrase, wait4prev=False, **kwargs):
        cmd = self.generate_command(phrase, **kwargs)
        if self.prevproc:
            if wait4prev:
                self.prevproc.wait()
            else:
                self.prevproc.terminate()
        if platform.system() == "Windows":
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.SW_HIDE | subprocess.STARTF_USESHOWWINDOW
            self.prevproc = subprocess.Popen(cmd,
                                             cwd=os.path.dirname(
                                                 os.path.abspath(__file__)),
                                             startupinfo=si)
        else:
            self.prevproc = subprocess.Popen(cmd,
                                             cwd=os.path.dirname(
                                                 os.path.abspath(__file__)))

    def is_talking(self):
        if self.prevproc and self.prevproc.poll() == None:
            return True
        else:
            return False

    def wait(self):
        if self.prevproc:
            self.prevproc.wait()

    def quiet(self):
        if self.prevproc:
            self.prevproc.terminate()
