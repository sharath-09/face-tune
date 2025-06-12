import queue
import sounddevice as sd
import soundfile as sf
from pathlib import Path
import numpy as np
import logging

from pedalboard.io import AudioStream
from pedalboard import Pedalboard, LowpassFilter

log = logging.getLogger(__name__)

class Stream:
    def __init__(self, Audio : Path):
        """Set stream parameters"""
        self.sample_rate = 48000
        self.channels = 2
        self.blocksize = 1024
        self.num_channels = 2
        self.buffersize = 20
        self.audio_path = Audio
        self.audio_buffer = queue.Queue(maxsize=self.buffersize)
        self.pedalboard = Pedalboard([LowpassFilter()])
        self.low_pass_filter = self.pedalboard[0]


    
    def buffer_stream(self, buffer_data: np.ndarray):
        """Prefill buffer with audio data

        Args:
            buffer_data (np.ndarray): Audio data with shape (channels, frames=blocksize)
        """
        log.info("Buffering")
        for _ in range(self.buffersize):
            data = buffer_data.read(self.blocksize)
            self.audio_buffer.put_nowait(data)
        log.info("Finished buffering")


    def start_stream(self, output_device):
        """Start playback stream"""
        with sf.SoundFile(self.audio_path) as f:
            stream = sd.OutputStream(
                samplerate=self.sample_rate, blocksize=self.blocksize,
                device=output_device, channels=self.num_channels, dtype='float32',
                callback=self.callback)

            self.buffer_stream(f)

            print('Starting Playback ...')
            start = 0
            with stream:
                timeout = self.blocksize * self.buffersize / f.samplerate
                count = 0
                while len(data):
                    data = f.read(self.blocksize)
                    self.low_pass_filter.cutoff_frequency_hz = 50
                    # Process this chunk of audio, setting `reset` to `False`
                    # to ensure that reverb tails aren't cut off
                    output = self.pedalboard.process(data.T, self.sample_rate, reset=False)
                    # output = apply_bass_boost(output, cutoff=800)
                    self.audio_buffer.put(output.T, timeout=timeout)

    def callback(self, indata, outdata, frames, time, status):
        """Callback component.

        Args:
            indata (_type_): _description_
            outdata (_type_): _description_
            frames (_type_): _description_
            time (_type_): _description_
            status (_type_): _description_

        Raises:
            sd.CallbackAbort: _description_
            sd.CallbackAbort: _description_
            sd.CallbackStop: _description_
        """        
        assert frames == self.blocksize
        if status.output_underflow:
            print('Output underflow: increase blocksize?')
            raise sd.CallbackAbort
        assert not status
        try:
            data = self.audio_buffer.get_nowait()
        except queue.Empty as e:
            print('Buffer is empty: increase buffersize?')
            raise sd.CallbackAbort from e
        if len(data) < len(outdata):
                outdata[:len(data)] = data
                outdata[len(data):].fill(0)
                raise sd.CallbackStop
        else:
            outdata[:] = data

    
    def end_stream(self):
        sd.stop()
    

if __name__ == "__main__":
    input_device_name = AudioStream.default_input_device_name
    output_device_name = AudioStream.default_output_device_name
    stream = Stream(Path("back_2_me.mp3"))
    try:
        stream.start_stream()
    except KeyboardInterrupt:
        stream.end_stream()