from itertools import repeat
from contextlib import contextmanager

import jack
from numpy import zeros, resize, average

try:
    range = xrange
except NameError:
    pass

_DEFAULT_CLIENT = "system"

class ShapeError(Exception):
    def __str__(self):
        return "Explicitly specify truncate or average for play method"

@contextmanager
def get_client(name, input_map, output_map):
    client = JackAudio(name, input_map, output_map)
    yield client
    client.close()


def easy_client(name, channels_in, channels_out):
    return get_client(name, _port_map(channels_in, False),
                      _port_map(channels_out, True))


def _port_id(client_name, port_name):
    return "{}:{}".format(client_name, port_name)


def _port_map(num_ports, is_output):
    dst_template = 'playback_{}' if is_output else 'capture_{}'
    src_template = 'out_{}' if is_output else 'in_{}'
    return [(src_template.format(i),
             _port_id(_DEFAULT_CLIENT, dst_template.format(i)))
            for i in range(1, num_ports+1)]

class JackAudio(object):
    def __init__(self, name, inputs, outputs):
        self.client = jack.Client(name)
        self.client.activate()

        self._buff_size = self.client.get_buffer_size()
        self._in_channels = len(inputs)
        self._out_channels = len(outputs)

        self._register(outputs, jack.IsOutput)
        self._register(inputs, jack.IsInput)
        self._connect(outputs, True, name)
        self._connect(inputs, False, name)

    def _register(self, ports, kind):
        for src, _ in ports:
            self.client.register_port(src, kind)

    def _connect(self, ports, is_output, name):
        for src, dst in ports:
            src = _port_id(name, src)
            if not is_output:
                src, dst = dst, src
            self.client.connect(src, dst)

    def close(self):
        self.client.deactivate()
        self.client.detach()

    def _generate_chunks(self, data):
        return (data[:, i:i+self._buff_size] for i in
                range(0, data.shape[1] - self._buff_size, self._buff_size))

    def capture(self, sec):
        size = int(self.client.get_sample_rate()*sec)
        captured = zeros((self._in_channels, size), 'f')
        self._process(ins=self._generate_chunks(captured), outs=None)
        return captured

    def play(self, captured, truncate=None):
        size = captured.shape[0]
        if size < self._out_channels or truncate:
            captured = resize(captured, (self._out_channels ,captured.shape[1]))

        elif size > self._out_channels:
            if truncate is None:
                raise ShapeError
            captured[self._out_channels] += average(captured[self._out_channels:,:])
            captured = captured[:self._out_channels,]
        self._process(ins=None, outs=self._generate_chunks(captured))

    def _sanitize(self, data, is_output):
        if data is not None:
            return data
        channels = self._out_channels if is_output else self._in_channels
        return repeat(zeros((channels, self._buff_size), 'f'))

    def _process(self, ins, outs):
        ins, outs = self._sanitize(ins, False), self._sanitize(outs, True)
        for ins, outs in zip(ins, outs):
            try:
                self.client.process(outs, ins)
            except jack.InputSyncError:
                continue
            except jack.OutputSyncError:
                continue
