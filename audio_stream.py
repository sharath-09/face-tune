
from pathlib import Path
from multiprocessing import Queue
import sounddevice as sd
import soundfile as sf
from pedalboard.io import AudioStream
from pedalboard import Pedalboard, Compressor, LowpassFilter

class AudioLoop:

    def __init__(self):
        self.input_device_name = AudioStream.default_input_device_name
        self.output_device_name = AudioStream.default_output_device_name
        self.audio_file = Path("audio_samples", "back_2_me.mp3")

        self.duration = 0
        self.sample_rate = 48000
        self.num_channels = 2
        self.blocksize = 1024
        self.buffersize = 20

        self.q = Queue(maxsize=self.buffersize)
    
    def callback(self, outdata, frames, time, status):
        assert frames == self.blocksize
        if status.output_underflow:
            print('Output underflow: increase blocksize?')
            raise sd.CallbackAbort
        assert not status
        try:
            data = self.q.get_nowait()
        except Queue.Empty as e:
            print('Buffer is empty: increase buffersize?')
            raise sd.CallbackAbort from e
        if len(data) < len(outdata):
                outdata[:len(data)] = data
                outdata[len(data):].fill(0)
                raise sd.CallbackStop
        else:
            outdata[:] = data
        
    
    def play_audio(self):
        self.board = Pedalboard([LowpassFilter()])
        try:
            print('Opening stream ...')
            with sf.SoundFile(self.audio_file) as f:
                stream = sd.OutputStream(
                    samplerate=self.sample_rate, blocksize=self.blocksize,
                    device=self.output_device_name, channels=self.num_channels, dtype='float32',
                    callback=self.callback)

                print('Buffering ...')
                for _ in range(self.buffersize):
                    data = f.read(self.blocksize)
                    if not len(data):
                        break
                    self.q.put_nowait(data)  # Pre-fill queue

                print('Starting Playback ...')
                start = 0
                with stream:
                    timeout = self.blocksize * self.buffersize / f.samplerate
                    frames_progressed = 0
                    count = 0
                    frames_in_song = (self.sample_rate * self.duration) / self.blocksize
                    while len(data):
                        data = f.read(self.blocksize)
                        count += self.blocksize
                        # self.low_pass_filter.cutoff_frequency_hz = 50
                        # Process this chunk of audio, setting `reset` to `False`
                        # to ensure that reverb tails aren't cut off
                        output = self.board.process(data.T, self.sample_rate, reset=False)
                        # output = apply_bass_boost(output, cutoff=800)
                        self.q.put(output.T, timeout=timeout)
                    self.event.wait()  # Wait until playback is finished
        except KeyboardInterrupt:
            print('\nInterrupted by user')
            sd.stop()