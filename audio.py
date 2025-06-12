import queue
import threading
import numpy as np
from pedalboard.io import AudioStream
from pedalboard.io import AudioFile

from pedalboard import Reverb
from pedalboard import Pedalboard, Compressor, LowpassFilter
from scipy.signal import butter, lfilter

import sounddevice as sd
import soundfile as sf

from stream import Stream

# Pass both an input and output device name to connect both ends:
input_device_name = AudioStream.default_input_device_name
output_device_name = AudioStream.default_output_device_name
AUDIO_1 = "SMEEGLE.mp3"
AUDIO_2 = "back_2_me.mp3"

duration = 0
sample_rate = 48000
num_channels = 2
blocksize = 1024
buffersize = 20

# stream = Stream()

q = queue.Queue(maxsize=buffersize)

with AudioFile(AUDIO_2) as f:
    print("Sample rate: ", f.samplerate)
    duration = f.duration
    sample_rate = f.samplerate
    audio = f.read(f.samplerate * int(duration))
    frames = f.frames

step_size_in_samples = sample_rate * 5

# stream = AudioStream(input_device_name, output_device_name)
reverb = Reverb()

def play_audio(audio_chunk: np.ndarray):
    """Plays an input audio stream

    Args:
        audio_chunk (np.ndarray): Audio stream.
    """    
    sd.play(audio_chunk, sample_rate, blocking=False)
    sd.wait()

board = Pedalboard([LowpassFilter()])
# reverb = board[1]
low_pass_filter = board[0]

def callback(outdata, frames, time, status):
    assert frames == blocksize
    if status.output_underflow:
        print('Output underflow: increase blocksize?')
        raise sd.CallbackAbort
    assert not status
    try:
        data = q.get_nowait()
    except queue.Empty as e:
        print('Buffer is empty: increase buffersize?')
        raise sd.CallbackAbort from e
    if len(data) < len(outdata):
            outdata[:len(data)] = data
            outdata[len(data):].fill(0)
            raise sd.CallbackStop
    else:
        outdata[:] = data

event = threading.Event()

try:
    print('Opening stream ...')
    with sf.SoundFile(AUDIO_2) as f:
        stream = sd.OutputStream(
            samplerate=sample_rate, blocksize=blocksize,
            device=output_device_name, channels=num_channels, dtype='float32',
            callback=callback)

        print('Buffering ...')
        for _ in range(buffersize):
            data = f.read(blocksize)
            if not len(data):
                break
            q.put_nowait(data)  # Pre-fill queue

        print('Starting Playback ...')
        start = 0
        with stream:
            timeout = blocksize * buffersize / f.samplerate
            frames_progressed = 0
            count = 0
            frames_in_song = (sample_rate * duration) / blocksize
            while len(data):
                data = f.read(blocksize)
                count += blocksize
                low_pass_filter.cutoff_frequency_hz = 50
                # Process this chunk of audio, setting `reset` to `False`
                # to ensure that reverb tails aren't cut off
                output = board.process(data.T, sample_rate, reset=False)
                # output = apply_bass_boost(output, cutoff=800)
                q.put(output.T, timeout=timeout)
            event.wait()  # Wait until playback is finished
except KeyboardInterrupt:
    print('\nInterrupted by user')
    sd.stop()