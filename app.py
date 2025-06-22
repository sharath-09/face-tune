from pathlib import Path
from multiprocessing import Queue, Process

from matplotlib import pyplot as plt
import numpy as np
import cv2
from insightface.app import FaceAnalysis

from plot import get_slope, plot_positions, plot_y_axis_over_time
from webcam_stream import FaceTracker
from audio_stream import AudioLoop

PARENT_PATH = Path(__file__).parent


def main():
    #Initialise tracker
    tracker = FaceTracker()
    audio_stream = AudioLoop()

    p = Process(target=audio_stream.play_audio)
    p.start()

    frame_num = 0
    lmk_positions = []
    slopes = []
    prev_lmk = None
    try:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Cannot open camera")
            exit()
        while cap.isOpened():
            # Capture frame-by-frame
            ret, frame = cap.read()
            # if frame is read correctly ret is True
            if not ret:
                print("Can't receive frame (stream end?). Exiting ...")
                break
            frame_num += 1
            frame = tracker.track_frame(frame)
            cv2.imshow("yerr", frame)
    except KeyboardInterrupt:
        # When everything done, release the capture
        p.join()
        cap.release()
        cv2.destroyAllWindows()
        print(slopes)

if __name__ == "__main__":
    main()