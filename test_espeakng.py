#! /usr/bin/python3
# An espeak TTS binding for Python3.
# Copyright (C) 2016 Sayak Brahmachari.
##
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
##
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
##
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import time

import espeakng

def test_espeakng():
    print("Testing espeak4py\n")

    mySpeaker = espeakng.Speaker()

    mySpeaker.say("", wait4prev=True)

    print("Testing wait4prev")

    mySpeaker.say("Hello, World!")
    time.sleep(1)
    mySpeaker.say("Interrupted!")
    time.sleep(3)

    mySpeaker.say("Hello, World!")
    time.sleep(1)
    mySpeaker.say("Not Interrupted.", wait4prev=True)
    time.sleep(3)

    print("Testing pitch")

    myHighPitchedSpeaker = espeakng.Speaker(pitch=99)
    myHighPitchedSpeaker.say("I am a demo of the say function")
    time.sleep(4)

    print("Testing wpm")

    myFastSpeaker = espeakng.Speaker(wpm=140)
    myFastSpeaker.say("I am a demo of the say function")

    print("Testing parameter overrides with say")
    myFastSpeaker.say("I am a demo of the say function", wait4prev=True, wpm=240)
    time.sleep(4)

    print("Testing voice")

    mySpanishSpeaker = espeakng.Speaker(voice="es")
    mySpanishSpeaker.say("Hola. Como estas?")

    print("Testing Completed.")

if __name__ == "__main__":
    test_espeakng()
    