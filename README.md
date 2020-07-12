# eSpeak NG TTS Bindings for Python3

Copyright 2016-2020 [Sayak B](https://sayakb.com/). Licenced under
[GNU GPLv3](https://opensource.org/licenses/GPL-3.0).

[![Python Version](https://img.shields.io/badge/Python-3-brightgreen.svg)](https://www.python.org/download/releases/3.0/)
![Linux](https://img.shields.io/badge/-Linux-brightgreen.svg)
![Windows](https://img.shields.io/badge/-Windows-brightgreen.svg)

## Requirements

You need to have eSpeak NG installed in your system and added to the path.

### Windows

The latest installers for eSpeak NG can be found [here](https://github.com/espeak-ng/espeak-ng/releases/latest).

The installed executable may need to be added to the system path. ([See here](https://www.howtogeek.com/118594/how-to-edit-your-system-path-for-easy-command-line-access/))

### Ubuntu & Debian

```bash
sudo apt-get update
sudo apt-get install espeak-ng
```

### Others

If eSpeak NG is not available in your package manager, you may need to compile the binaries for your system. Refer to [this page](https://github.com/espeak-ng/espeak-ng/blob/master/docs/building.md) for more information.

## Installation

### GitHub Releases

You can download the latest release for this library [here](https://github.com/sayak-brm/espeakng-python/releases/latest).

## Usage

First, we have to initialize a `Speaker`.

```python
import espeakng

mySpeaker = espeakng.Speaker()
```

And then use the `Speaker.say()` method to speak:

```python
mySpeaker.say('Hello, World!')
```

Calling `Speaker.say()` will interrupt any ongoing output from the same object
immediately.

Use the following code if you wish to wait for any ongoing speech to complete:

```python
mySpeaker.say('I am a demo of the say() method.', wait4prev=True)
```

---

### Changing speech properties

#### Pitch

By default the pitch is set at 80.

Change it by:

```python
mySpeaker.pitch = 120
```

#### Words per Minute (WPM)

By default WPM is set at 120.

Change it by:

```python
mySpeaker.wpm = 140
```

#### Voice

By default the voice is set to 'en'. The complete list of supported voices can be found [here](https://github.com/espeak-ng/espeak-ng/blob/master/docs/languages.md).

Change it by:

```python
mySpeaker.voice = 'es'
```
