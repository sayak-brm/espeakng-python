#! python3
import subprocess
import os
import platform

class Speaker:
    """
    Speaker class for differentiating different speech properties.
    """

    def setVoice(self, voice):
        self.voice = voice

    def setWPM(self, wpm):
        self.wpm = wpm

    def setPitch(self, pitch):
        self.pitch = pitch

    def setProperties(self, voice="en", wpm=120, pitch=80):
        self.setVoice(voice)
        self.setWPM(wpm)
        self.setPitch(pitch)

    def __init__(self, voice="en", wpm=120, pitch=80):
        self.prevproc = None
        self.setProperties(voice, wpm, pitch)
        if platform.system() == 'Windows': self.executable = os.path.dirname(os.path.abspath(__file__)) + "/espeak.exe"
        else: self.executable = os.path.dirname(os.path.abspath(__file__)) + "/espeak"

    def generateCommand(self, phrase):
        cmd = [
            self.executable,
            "--path=.",
            "-v", self.voice,
            "-p", self.pitch,
            "-s", self.wpm,
            phrase
        ]
        cmd = [str(x) for x in cmd]
        return cmd

    def say(self, phrase, wait4prev=False):
        cmd=self.generateCommand(phrase)
        if wait4prev:
            try: self.prevproc.wait()
            except AttributeError: pass
        else:
            try: self.prevproc.terminate()
            except AttributeError: pass
        self.prevproc = subprocess.Popen(cmd, executable=self.executable, cwd=os.path.dirname(os.path.abspath(__file__)))
