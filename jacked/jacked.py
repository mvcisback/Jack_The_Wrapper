"""
Author: Marcell Vazquez-Chanlatte - 5/30/2014
"""

from itertools import repeat
from contextlib import contextmanager

# pylint: disable=E0611
from numpy import zeros, resize, average
# pylint: enable=E0611
import jack

try:
    # pylint: disable=W0622,C0103
    range = xrange
    # pylint: enable=W0622,C0103
except NameError:
    pass


_DEFAULT_CLIENT = "system"

@contextmanager
def get_client(name, input_map, output_map):
    """Returns context for a JackAudio client given a name:str and an input/
    output map for example: in_map = [(in_1, system:capture_1), ...]
    out_map = [(out_1, system:playback_1)]"""
    client = JackAudio(name, input_map, output_map)
    yield client
    client.close()


def easy_client(name, channels_in, channels_out):
    """Returns context for Jack Audio Client"""
    return get_client(name, _port_map(channels_in, False),
                      _port_map(channels_out, True))


def _port_id(client_name, port_name):
    """Format for addressing jack ports"""
    return "{}:{}".format(client_name, port_name)


def _port_map(num_ports, is_output):
    """Create port default port map names for a given no. of ports and type"""
    dst_template = 'playback_{}' if is_output else 'capture_{}'
    src_template = 'out_{}' if is_output else 'in_{}'
    return [(src_template.format(i),
             _port_id(_DEFAULT_CLIENT, dst_template.format(i)))
            for i in range(1, num_ports+1)]

class JackAudio(object):
    """Jack Audio Client: wraps pyjack bindings into more pythonic interface."""
    def __init__(self, name, inputs, outputs):
        """Takes a name and input/output maps"""
        self.client = jack.Client(name)
        self.client.activate()

        self._buff_size = self.client.get_buffer_size()
        self._num_in = len(inputs)
        self._num_out = len(outputs)

        self._register(outputs, jack.IsOutput)
        self._register(inputs, jack.IsInput)
        self._connect(outputs, True, name)
        self._connect(inputs, False, name)

    @property
    def sample_rate(self):
        return self.client.get_sample_rate()

    def _register(self, ports, kind):
        """register the ports"""
        for src, _ in ports:
            self.client.register_port(src, kind)

    def _connect(self, ports, is_output, name):
        """connect the ports"""
        for src, dst in ports:
            src = _port_id(name, src)
            if not is_output:
                src, dst = dst, src
            self.client.connect(src, dst)

    def close(self):
        """Deactivates and detaches jack client.
        (has a print sideeffect from pyjack)"""
        self.client.deactivate()
        self.client.detach()

    def _generate_chunks(self, data):
        """Step through data with steps of the jack buffer size"""
        return (data[:, i:i+self._buff_size] for i in
                range(0, data.shape[1] - self._buff_size, self._buff_size))

    def capture(self, sec):
        """Captures sec amount of audio. Returns numpy array of size
        (in channels, sample_rate*sec)"""
        size = int(self.client.get_sample_rate()*sec)
        captured = zeros((self._num_in, size), 'f')
        self._process(ins=self._generate_chunks(captured), outs=None)
        return captured

    def play(self, captured, truncate=False):
        """Plays 2-d numpy array captured. Is interpreted as (channels, samples)
        - Assumes samples were sampled at current sample rate
        - If not truncate, then averages extra channels into one of the output
          channels
        - If truncate, then extra channels will be ignored
        Extra channel means it doesn't have a corresponding input channel"""
        size = captured.shape[0]
        if size < self._num_out or truncate:
            captured = resize(captured, (self._num_out, captured.shape[1]))

        elif size > self._num_out:
            captured[self._num_out] += average(captured[self._num_out:, :])
            captured = captured[:self._num_out,]
        self._process(ins=None, outs=self._generate_chunks(captured))

    def _sanitize(self, data, is_output):
        """If the data is none, us noop data"""
        if data is not None:
            return data
        channels = self._num_out if is_output else self._num_in
        return repeat(zeros((channels, self._buff_size), 'f'))

    def _process(self, ins, outs):
        """Wrapper for pyjack's process function.'"""
        ins, outs = self._sanitize(ins, False), self._sanitize(outs, True)
        for ins, outs in zip(ins, outs):
            try:
                self.client.process(outs, ins)
            except jack.InputSyncError:
                continue
            except jack.OutputSyncError:
                continue
