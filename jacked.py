from itertools import repeat, chain
from contextlib import contextmanager

import jack
from numpy import zeros
import time

try:
    range = xrange
except NameError:
    pass

def port_id(client_name, port_name):
    return "{}:{}".format(client_name, port_name)

@contextmanager
def get_client(name, in_channels, out_channels):
    client = JackAudio(name, in_channels, out_channels)
    yield client
    client.close()


class JackAudio(object):
    def __init__(self, name, in_channels=0, out_channels=0):
        self.client = jack.Client(name)
        self.client.activate()

        self._buff_size = self.client.get_buffer_size()
        self._in_channels = in_channels
        self._out_channels = out_channels
        
        inputs, outputs = self._register(in_channels, out_channels)
        self._connect(inputs, outputs, name)

    def _register(self, in_channels, out_channels):
        inputs = ["in_{}".format(i+1) for i in range(in_channels)]
        outputs = ["out_{}".format(i+1) for i in range(out_channels)]
        ports = chain(zip(inputs, repeat(jack.IsInput)),
                      zip(outputs, repeat(jack.IsOutput)))

        for port, kind in ports:
            self.client.register_port(port, kind)
        return inputs, outputs

    def _connect(self, inputs, outputs, name):
        for i, (in_port, out_port) in enumerate(zip(inputs, outputs)):
            self.client.connect(port_id(name, in_port), port_id("system", "playback_{}".format(i+1)))
            self.client.connect(port_id("system", "capture_{}".format(i+1)), port_id(name, out_port))

        if len(inputs) > len(outputs):
            for in_port in inputs[len(outputs)-1:]:
                self.client.connect(port_id(name, in_port),
                                    port_id("system", "playback_{}".format(len(outputs))))
         
        elif len(outputs) > len(inputs):
            for out_port in outputs[len(inputs)-1:]:
                self.client.connect(port_id("system", "capture_{}".format(len(inputs))),
                                    port_id(name, out_port))


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
