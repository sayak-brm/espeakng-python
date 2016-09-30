#! python3
import espeak4py
import time

print('Testing espeak4py\n')

mySpeaker = espeak4py.Speaker()

print('Increasing Coverage')
mySpeaker.say('', wait4prev=True)

print('Testing wait4prev')

mySpeaker.say('Hello, World!')
time.sleep(1)
mySpeaker.say('Interrupted!')
time.sleep(3)

mySpeaker.say('Hello, World!')
time.sleep(1)
mySpeaker.say('Not Interrupted.', wait4prev=True)
time.sleep(3)

print('Testing pitch')

myHighPitchedSpeaker = espeak4py.Speaker(pitch=120)
myHighPitchedSpeaker.say('I am a demo of the say function')
time.sleep(4)

print('Testing wpm')

myFastSpeaker = espeak4py.Speaker(wpm=140)
myFastSpeaker.say('I am a demo of the say function')
time.sleep(4)

print('Testing voice')

mySpanishSpeaker = espeak4py.Speaker(voice='es')
mySpanishSpeaker.say('Hola. Como estas?')

print('Testing Completed.')
