from itertools import repeat, chain
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
def get_client(name, inputs, outputs):
    client = JackAudio(name, inputs, outputs)
    yield client
    client.close()


class JackAudio(object):
    def __init__(self, name, inputs, outputs):
        self.client = jack.Client(name)
        self.client.activate()

        self._buff_size = self.client.get_buffer_size()
        self._in_channels = len(inputs)
        self._out_channels = len(outputs)

        self._register(inputs, jack.IsInput, name)
        self._register(outputs, jack.IsOutput, name)

    def _register(self, ports, kind, name):
        for src, dst in ports:
            self.client.register_port(src, kind)
            self.client.connect(port_id(name, src), dst)

    def close(self):
        self.client.deactivate()
        self.client.detach()

    def _generate_chunks(self, data):
        return (data[:, i:i+self._buff_size] for i in
                range(0, data.shape[1] - self._buff_size, self._buff_size))

    def capture(self, sec):
        size = int(self.client.get_sample_rate()*sec)
        captured = zeros((self._in_channels, size), 'f')
        self._process(ins=None, outs=self._generate_chunks(captured))
        return captured

    def play(self, captured):
        self._process(ins=self._generate_chunks(captured), outs=None)

    def _sanitize(self, data, is_output):
        if data is not None:
            return data
        channels = self._out_channels if is_output else self._in_channels
        return repeat(zeros((channels, self._buff_size), 'f'))

    def _process(self, ins, outs):
        ins, outs = self._sanitize(ins, False), self._sanitize(outs, True)
        for ins, outs in zip(ins, outs):
            try:
                self.client.process(ins, outs)
            except jack.InputSyncError:
                continue
            except jack.OutputSyncError:
                continue
