## espeak TTS Bindings for Python3

###### Licenced under GNU GPLv3. Contains precompiled binaries. Sources included.

#### Usage:

```
import espeak4py

say('Hello, World!')
```

The above will stop interrupt any ongoing speech.
Code to wait for any ongoing speech to complete:

```
say('I am a demo of the say() function.', wait4prev=True)
```

##### Changing speech properties:

###### Pitch:

By default the pitch is set at 80.

Change it by:

```
say('I am a demo of the say function', pitch=120)
```

###### Words per Minute:

By default WPM is set at 120.

Change it by:

```
say('I am a demo of the say function', wpm=140)
```

###### Voice:

By default WPM is set to 'en'.
Uses voice file of set name from `espeak-data/voices`.

Change it by:

```
say('I am a demo of the say function', voice="es")
```

