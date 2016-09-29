## espeak TTS Bindings for Python3

###### Licenced under GNU GPLv3. Contains precompiled binaries for espeak v1.48.04. Sources for included binaries available [here](http://espeak.sourceforge.net/).
[![Code Climate](https://codeclimate.com/github/sayak-brm/espeak4py/badges/gpa.svg)](https://codeclimate.com/github/sayak-brm/espeak4py) [![Test Coverage](https://codeclimate.com/github/sayak-brm/espeak4py/badges/coverage.svg)](https://codeclimate.com/github/sayak-brm/espeak4py/coverage) [![Issue Count](https://codeclimate.com/github/sayak-brm/espeak4py/badges/issue_count.svg)](https://codeclimate.com/github/sayak-brm/espeak4py)

### Usage:

```
import espeak4py

espeak4py.say('Hello, World!')
```

The above will stop interrupt any ongoing speech.
Code to wait for any ongoing speech to complete:

```
espeak4py.say('I am a demo of the say() function.', wait4prev=True)
```

#### Changing speech properties:

###### Pitch:

By default the pitch is set at 80.

Change it by:

```
espeak4py.say('I am a demo of the say function', pitch=120)
```

###### Words per Minute:

By default WPM is set at 120.

Change it by:

```
espeak4py.say('I am a demo of the say function', wpm=140)
```

###### Voice:

By default WPM is set to 'en'.
Uses voice file of set name from `espeak-data/voices`.

Change it by:

```
espeak4py.say('I am a demo of the say function', voice="es")
```