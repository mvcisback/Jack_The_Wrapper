# Jack The Wrapper
[![LOGO](http://imgur.com/yd7FeUI.png)](http://i.imgur.com/yd7FeUI.png)

## About

## Features

## Installing

## Examples

### Record 3 seconds and play back
```python
from jacked import get_client

with get_client(name="captest", channels=1) as client:
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
