#! python3

##    An espeak TTS binding for Python3.
##    Copyright (C) 2016 Sayak Brahmachari.
##
##    This program is free software: you can redistribute it and/or modify
##    it under the terms of the GNU General Public License as published by
##    the Free Software Foundation, either version 3 of the License, or
##    (at your option) any later version.
##
##    This program is distributed in the hope that it will be useful,
##    but WITHOUT ANY WARRANTY; without even the implied warranty of
##    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##    GNU General Public License for more details.
##
##    You should have received a copy of the GNU General Public License
##    along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import platform
import subprocess


class Speaker:
    """
    Speaker class for differentiating different speech properties.
    """
    def __init__(self, voice='en', wpm=120, pitch=80):
        self.prevproc = None
        self.voice = voice
        self.wpm = wpm
        self.pitch = pitch

        executable = 'espeak.exe' if platform.system() == 'Windows' else 'espeak'
        self.executable = os.path.join(os.path.dirname(os.path.abspath(__file__)), executable)

    def generate_command(self, phrase):
        cmd = [
            self.executable,
            '--path=.',
            '-v', self.voice,
            '-p', self.pitch,
            '-s', self.wpm,
            phrase
        ]
        cmd = [str(x) for x in cmd]
        return cmd

    def say(self, phrase, wait4prev=False):
        cmd = self.generate_command(phrase)
        if self.prevproc:
            if wait4prev:
                self.prevproc.wait()
            else:
                self.prevproc.terminate()
        self.prevproc = subprocess.Popen(cmd, cwd=os.path.dirname(os.path.abspath(__file__)))
