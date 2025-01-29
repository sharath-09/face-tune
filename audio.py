import queue
import numpy as np
from pedalboard.io import AudioStream
from pedalboard.io import AudioFile

from pedalboard import Reverb
from pedalboard import Pedalboard, Compressor

import sounddevice as sd
import ffmpeg

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

stream = Stream()

q = queue.Queue(maxsize=buffersize)

with AudioFile(AUDIO_2) as f:
    print("Sample rate: ", f.samplerate)
    duration = f.duration
    sample_rate = f.samplerate
    audio = f.read(f.samplerate * int(duration))
    frames = f

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

board = Pedalboard([Compressor(), Reverb()])
reverb = board[1]

# with AudioFile(AUDIO_2) as af:
#     for i in range(0, af.frames, step_size_in_samples):
#         chunk = af.read(step_size_in_samples)

#         # Set the reverb's "wet" parameter to be equal to the
#         # percentage through the track (i.e.: make a ramp from 0% to 100%)
#         percentage_through_track = i / af.frames
#         reverb.wet_level = percentage_through_track

#         # Process this chunk of audio, setting `reset` to `False`
#         # to ensure that reverb tails aren't cut off
#         output = board.process(chunk, af.samplerate, reset=False)
#         play_audio(output.T)


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
    print(f"data size: {len(data)}")
    print(len(outdata))
    assert len(data) == len(outdata)
    outdata[:] = data

try:
    print('Opening stream ...')

    stream = sd.OutputStream(
        samplerate=sample_rate, blocksize=blocksize,
        device=output_device_name, channels=num_channels, dtype='float32',
        callback=callback)
    read_size = blocksize
    start = 0

    print('Buffering ...')
    print(f"Read size {read_size}")
    print(f"Audio stream : {audio.shape}")

    for _ in range(buffersize):
        q.put_nowait(audio[:, start : start + read_size].T)
        start += read_size

    print('Starting Playback ...')
    start = 0
    with stream:
        timeout = (blocksize * buffersize) / sample_rate
        while True:
            q.put(audio[:, start : start + read_size].T, timeout=timeout)
            start += read_size
except KeyboardInterrupt:
    print('\nInterrupted by user')
    sd.stop()

# with AudioStream(input_device_name, output_device_name) as stream:
#     # In this block, audio is streaming through `stream`!
#     # Audio will be coming out of your speakers at this point.

#     gain = Gain()
#     stream.plugins.append(gain)

#     # Add plugins to the live audio stream:
#     reverb = Reverb()
#     # stream.plugins.append(reverb)

#     # Change plugin properties as the stream is running:
#     reverb.wet_level = 1.0

#     # Delete plugins:
#     del stream.plugins[0]
# 
# Or use AudioStream synchronously:
# stream = AudioStream(input_device_name, output_device_name)
# stream.plugins.append(Reverb(wet_level=1.0))
# stream.run()  # Run the stream until Ctrl-C is received