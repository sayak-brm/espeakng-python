## espeak TTS Bindings for Python3

###### Copyright 2016-2020 [Sayak B](https://sayakb.com/). Licenced under [GNU GPLv3](https://opensource.org/licenses/GPL-3.0).
[![Python Version](https://img.shields.io/badge/Python-3-brightgreen.svg)](https://www.python.org/download/releases/3.0/) [![espeak Version](https://img.shields.io/badge/espeak-v1.48.04-brightgreen.svg)](http://espeak.sourceforge.net/) ![Linux](https://img.shields.io/badge/-Linux-brightgreen.svg) ![Windows](https://img.shields.io/badge/-Windows-orange.svg)

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

###### Note: A `Speaker` object can only interrupt itself.

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
mySpeaker.pitch = 120
```

###### Words per Minute (WPM):

By default WPM is set at 120.

Change it by:

```python
mySpeaker.wpm = 140
```

###### Voice:

By default the voice is set to 'en'.
Uses voice file of set name from `espeak-data/voices`.

Change it by:

```python
mySpeaker.voice = 'es'
```