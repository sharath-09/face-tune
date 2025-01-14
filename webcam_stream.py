from pathlib import Path

from matplotlib import pyplot as plt
import numpy as np
import cv2
from insightface.data import get_image as ins_get_image
from insightface.app import FaceAnalysis

from plot import get_slope, plot_positions, plot_y_axis_over_time

PARENT_PATH = Path(__file__).parent


def stream(model): 
    frame_num = 0
    lmk_positions = []
    slopes = []
    prev_lmk = None
    try:
        cap = cv2.VideoCapture(1)
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
            faces = model.get(frame)
            color = (200, 160, 75)
            for face in faces:
                lmk = face.landmark_2d_106
                lmk = np.round(lmk).astype(np.int64)
                lmk_positions.append(lmk)
                if prev_lmk is not None:
                    p1 = prev_lmk[0, :]
                    p2 = lmk[0,:]
                    slope = get_slope(p1, p2)
                    slopes.append(slope)
                prev_lmk = lmk
                for i in range(lmk.shape[0]):
                    p = tuple(lmk[i])
                    cv2.circle(frame, p, 1, color, 1, cv2.LINE_AA)
            # Display the resulting frame
            cv2.imshow('frame', frame)
    except KeyboardInterrupt:
        # When everything done, release the capture
        cap.release()
        cv2.destroyAllWindows()
        print(slopes)
        plot_positions(np.array(lmk_positions))
        plot_y_axis_over_time(np.array(lmk_positions))

def main():
    app = FaceAnalysis(root=str(PARENT_PATH), allowed_modules=['detection', 'landmark_2d_106'])
    app.prepare(ctx_id=0, det_size=(640, 640))
    stream(app)

if __name__ == "__main__":
    main()