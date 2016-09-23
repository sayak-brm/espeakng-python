import os
import subprocess
import ctypes
from threading import Thread, RLock
import time

prevproc = None
Lock = RLock()
isSpeaking=False

def say(phrase="hello", voice="en", wpm=120, pitch=80, wait4prev=False):
    global prevproc
    cmd = [
        "cmd", "/c",
        "espeak.exe",
        "--path=.",
        "-v", voice,
        "-p", pitch,
        "-s", wpm,
        phrase
    ]
    cmd = [str(x) for x in cmd]
    com=""
    for x in cmd:
        com += x+" "
    if wait4prev:
        try:
            prevproc.wait()
        except AttributeError: pass
    else:
        try:
            subprocess.Popen(['taskkill', '/F', '/PID', str(prevproc.pid)], shell=True)
        except AttributeError: pass
    prevproc = subprocess.Popen(cmd, shell=True)

class SayThread(Thread):
    def __init__(self, phrase="hello", voice="en", wpm=120, pitch=80, wait4prev=False):
        Thread.__init__(self)
        self.phrase=phrase
        self.voice=voice
        self.wpm=wpm
        self.pitch=pitch
        self.wait4prev=wait4prev
        self.start()
    def run(self):
        global isSpeaking
        Lock.acquire()
        while isSpeaking == True and self.wait4prev == True:
            Lock.release()
            time.sleep(1)
            Lock.acquire()
        isSpeaking = True
        Lock.release()
        say(phrase=self.phrase, voice=self.voice, wpm=self.wpm, pitch=self.pitch, wait4prev=self.wait4prev)
        Lock.acquire()
        isSpeaking=False
        Lock.release()

if __name__ == "__main__":
    import time
    print("DEMO")
    say(wait4prev=True)
    say(phrase="I am a demo of the say function", wait4prev=True)
    time.sleep(1)
    say(phrase="hola", voice="es")
