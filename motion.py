import cv2
import numpy as np

class MotionAnalyzer:
    def __init__(self, threshold=25, min_area=500):
        self.prev_frame = None
        self.threshold = threshold
        self.min_area = min_area
        self.motion_intensity = 0.0

    def analyze(self, frame):
        # Convert to grayscale and blur
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        if self.prev_frame is None:
            self.prev_frame = gray
            return {"motion_intensity": 0.0, "status": "Initializing", "contours": []}

        # Compute absolute difference between current and previous frame
        frame_diff = cv2.absdiff(self.prev_frame, gray)
        _, thresh = cv2.threshold(frame_diff, self.threshold, 255, cv2.THRESH_BINARY)
        thresh = cv2.dilate(thresh, None, iterations=2)

        # Find contours
        contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        total_motion_area = 0
        valid_contours = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > self.min_area:
                total_motion_area += area
                valid_contours.append(contour)

        # Normalize motion intensity (heuristic value)
        frame_area = frame.shape[0] * frame.shape[1]
        current_intensity = (total_motion_area / frame_area) * 100.0
        
        # Temporal smoothing
        self.motion_intensity = 0.8 * self.motion_intensity + 0.2 * current_intensity

        # Update previous frame
        self.prev_frame = gray

        status = "Normal"
        if self.motion_intensity > 15.0:
            status = "High Movement"
        elif self.motion_intensity < 0.1:
            status = "Inactive"

        return {
            "motion_intensity": self.motion_intensity,
            "status": status,
            "contours": valid_contours
        }
