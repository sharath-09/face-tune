from pathlib import Path

from matplotlib import pyplot as plt
import numpy as np
import cv2
from insightface.app import FaceAnalysis

from plot import get_slope, plot_positions, plot_y_axis_over_time

PARENT_PATH = Path(__file__).parent


class FaceTracker:

    def __init__(self):
        self.model = FaceAnalysis(root=str(PARENT_PATH), allowed_modules=['detection', 'landmark_2d_106'])
        self.model.prepare(ctx_id=0, det_size=(640,640))
        self.lmk_positions = []
        self.y_buffer = []
    
    def track_frame(self, frame):
        faces = self.model.get(frame)
        color = (200, 160, 75)
        for face in faces:
            lmk = face.landmark_2d_106
            lmk = np.round(lmk).astype(np.int64)
            self.lmk_positions.append(lmk)
            for i in range(lmk.shape[0]):
                p = tuple(lmk[i])
                cv2.circle(frame, p, 1, color, 1, cv2.LINE_AA)
        return frame
    

def main():
    app = FaceAnalysis(root=str(PARENT_PATH), allowed_modules=['detection', 'landmark_2d_106'])
    app.prepare(ctx_id=0, det_size=(640, 640))
    stream(app)

if __name__ == "__main__":
    main()