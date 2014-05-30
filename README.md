# Jack The Wrapper
[![LOGO](http://imgur.com/yd7FeUI.png)](http://i.imgur.com/yd7FeUI.png)

## About

Easy to use jack audio wrapper for python
- Uses context managers and sane defaults to make interfacing with jack less painful

## Installing

- Currently only supports python2 (due to pyjack C extension)
  - python 3 port on the roadmap

```shell
$ python setup.py install
```

## Examples

### Record 3 seconds and play back
```python
from jacked import easy_client

def main():
    with easy_client(name="captest", channels_in=2, channels_out=2) as client:
        captured = client.capture(sec=3)
        client.play(captured)
```

## Roadmap
- See issue list (milestone 1)

## References

## Credits
 - Logo and Name: Eric Mills
 - Module Name: John Espinosa
 - pyjack: jack bindings
