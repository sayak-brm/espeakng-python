#! python3
import subprocess
import os
import platform

class Speaker:
    def __init__(self, voice="en", wpm=120, pitch=80):
        self.prevproc = None
        self.voice = voice
        self.wpm = wpm
        self.pitch = pitch
        if platform.system() == 'Windows': self.executable = os.path.dirname(os.path.abspath(__file__)) + "/espeak.exe"
        else: self.executable = os.path.dirname(os.path.abspath(__file__)) + "/espeak"
        
    def generateCmd(self, phrase):
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
        cmd=self.generateCmd(phrase)
        if wait4prev:
            try: self.prevproc.wait()
            except AttributeError: pass
        else:
            try: self.prevproc.terminate()
            except AttributeError: pass
        self.prevproc = subprocess.Popen(cmd, executable=self.executable, cwd=os.path.dirname(os.path.abspath(__file__)))
