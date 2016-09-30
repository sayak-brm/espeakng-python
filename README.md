## espeak TTS Bindings for Python3

###### Licenced under GNU GPLv3. Contains precompiled binaries for espeak v1.48.04. Sources for included binaries available [here](http://espeak.sourceforge.net/).
[![Build status](https://ci.appveyor.com/api/projects/status/o2j9pe6sttd0j684?svg=true)](https://ci.appveyor.com/project/sayak-brm/espeak4py) [![Build Status](https://travis-ci.org/sayak-brm/espeak4py.svg?branch=master)](https://travis-ci.org/sayak-brm/espeak4py) [![Coverage](https://codeclimate.com/github/sayak-brm/espeak4py/badges/coverage.svg)](https://codeclimate.com/github/sayak-brm/espeak4py/coverage) [![Code Climate](https://codeclimate.com/github/sayak-brm/espeak4py/badges/gpa.svg)](https://codeclimate.com/github/sayak-brm/espeak4py) [![Issue Count](https://codeclimate.com/github/sayak-brm/espeak4py/badges/issue_count.svg)](https://codeclimate.com/github/sayak-brm/espeak4py) [![QuantifiedCode Issues](https://www.quantifiedcode.com/api/v1/project/bf3ba612b8c04e07beb901dcbbe4b325/badge.svg)](https://www.quantifiedcode.com/app/project/bf3ba612b8c04e07beb901dcbbe4b325) [![Python Version](https://img.shields.io/badge/Python-3-brightgreen.svg)](https://www.python.org/download/releases/3.0/) [![espeak Version](https://img.shields.io/badge/espeak-v1.48.04-brightgreen.svg)](http://espeak.sourceforge.net/) ![Linux](https://img.shields.io/badge/Linux--brightred.svg) ![Windows](https://img.shields.io/badge/Windows--brightgreen.svg)

### Usage:

First, we have to initialize a `Speaker`.

```python
import espeak4py

mySpeaker = espeak4py.Speaker()
```

And then to speak:

```python
mySpeaker.say('Hello, World!')
```

The above will stop interrupt the `Speaker` (`mySpeaker` in this case).


Code to wait for any ongoing speech to complete:

```python
mySpeaker.say('I am a demo of the say() function.', wait4prev=True)
```

---

#### Changing speech properties:

###### Pitch:

By default the pitch is set at 80.

Change it by:

```python
myHighPitchedSpeaker = espeak4py.Speaker(pitch=120)

myHighPitchedSpeaker.say('I am a demo of the say function')
```

or

```
mySpeaker.setPitch(120)
```

or

```
mySpeaker.pitch = 120
```

###### Words per Minute (WPM):

By default WPM is set at 120.

Change it by:

```python
myFastSpeaker = espeak4py.Speaker(wpm=140)

myFastSpeaker.say('I am a demo of the say function')
```

or

```
mySpeaker.setWPM(140)
```

or

```
mySpeaker.wpm = 140
```

###### Voice:

By default the voice is set to 'en'.
Uses voice file of set name from `espeak-data/voices`.

Change it by:

```python
mySpanishSpeaker = espeak4py.Speaker(voice='es')

mySpanishSpeaker.say('Hola. Como estas?')
```

or

```
mySpeaker.setVoice('es')
```

or

```
mySpeaker.voice = 'es'
```

###### All at Once:

Change all properties at once by:

```
mySpeaker.setProperties('es', 140, 120)
```

or

```
mySpeaker.setProperties(voice='es', wpm=140, pitch=120)
```

###### Reset Properties:

Reset all changed properties at once by:

```
mySpeaker.setProperties()
```