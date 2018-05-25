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
    def __init__(self, voice='en', wpm=170, pitch=50, amplitude=100, wordgap=0):
        self.prevproc = None
        self.voice = voice
        self.wpm = wpm             # 80-500 (170)
        self.pitch = pitch         # 0-99  (50)
        self.amplitude = amplitude # 0-200 (100)
        self.wordgap = wordgap     # The (additional) length of the pause, in units of 10 mS (at the default speed of 170 wpm)

        executable = 'espeak.exe' if platform.system() == 'Windows' else 'espeak'
        self.executable = os.path.join(os.path.dirname(os.path.abspath(__file__)), executable)

    def generate_command(self, phrase, **kwargs):
        cmd = [
            self.executable,
            '-v', kwargs.get('voice', self.voice),
            '-s', kwargs.get('wpm', self.wpm),
            '-p', kwargs.get('pitch', self.pitch),
            '-a', kwargs.get('amplitude', self.amplitude),
            '-g', kwargs.get('wordgap', self.wordgap),
            phrase
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
        if platform.system() == 'Windows':
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.SW_HIDE | subprocess.STARTF_USESHOWWINDOW
            self.prevproc = subprocess.Popen(cmd, cwd=os.path.dirname(os.path.abspath(__file__)), startupinfo=si)
        else:
            self.prevproc = subprocess.Popen(cmd, cwd=os.path.dirname(os.path.abspath(__file__)))

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
