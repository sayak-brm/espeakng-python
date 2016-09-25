import subprocess

prevproc = None

def say(phrase="hello", voice="en", wpm=120, pitch=80, wait4prev=False):
    global prevproc
    cmd = [
        "espeak",
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
    prevproc = subprocess.Popen(cmd)

if __name__ == "__main__":
    import time
    say(wait4prev=True)
    say("I am a demo of the say function", wait4prev=True)
    time.sleep(1)
    say("hola", voice="es")
