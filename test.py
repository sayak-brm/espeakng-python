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

import espeak4py
import time

print('Testing espeak4py\n')

mySpeaker = espeak4py.Speaker()

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
