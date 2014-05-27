from itertools import repeat
from contextlib import contextmanager

import jack
from numpy import zeros

try:
    range = xrange
except NameError:
    pass

def port_id(client_name, port_name):
    return "{}:{}".format(client_name, port_name)

@contextmanager
def get_client(name, channels):
    client = JackAudio(name, channels)
    yield client
    client.close()


class JackAudio(object):
    def __init__(self, name, channels):
        self.client = jack.Client(name)
        self.client.activate()

        self._buff_size = self.client.get_buffer_size()
        self._channels = channels

        for i in range(channels):
            port = "in_{}".format(i)
            self.client.register_port(port, jack.IsInput)
            self.client.connect(port_id("system", "capture_{}".format(i+1)),
                         port_id(name, port))

        for i in range(channels):
            port = "out_{}".format(i)
            self.client.register_port(port, jack.IsOutput)
            self.client.connect(port_id(name, port),
                         port_id("system", "playback_{}".format(i+1)))

    def close(self):
        self.client.deactivate()
        self.client.detach()

    def _generate_chunks(self, data):
        return (data[:, i:i+self._buff_size] for i in
                range(0, data.shape[1] - self._buff_size, self._buff_size))

    def capture(self, sec):
        size = int(self.client.get_sample_rate()*sec)
        captured = zeros((self._channels, size), 'f')
        self._process(ins=None, outs=self._generate_chunks(captured))
        return captured

    def play(self, captured):
        self._process(ins=self._generate_chunks(captured), outs=None)

    def _sanitize(self, data):
        return repeat(zeros((self._channels, self._buff_size), 'f')) if data is None else data

    def _process(self, ins, outs):
        ins, outs = self._sanitize(ins), self._sanitize(outs)
        for ins, outs in zip(ins, outs):
            try:
                self.client.process(ins, outs)
            except jack.InputSyncError:
                continue
            except jack.OutputSyncError:
                continue

def main():
    with get_client(name="captest", channels=1) as client:
        captured = client.capture(sec=3)
        client.play(captured)

if __name__ == '__main__':
    main()
