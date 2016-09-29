#! python3
import subprocess
import os
import platform

prevproc = None

if platform.system() == 'Windows': executable=os.path.dirname(os.path.abspath(__file__))+"/espeak.exe"
else: executable=os.path.dirname(os.path.abspath(__file__))+"/espeak"

def say(phrase="hello", voice="en", wpm=120, pitch=80, wait4prev=False):
    global prevproc
    cmd = [
        executable,
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
            prevproc.terminate()
        except AttributeError: pass
    prevproc = subprocess.Popen(cmd, executable=executable, cwd=os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    import time
    say(wait4prev=True)
    say("I am a demo of the say function", wait4prev=True)
    time.sleep(1)
    say("hola", voice="es")
