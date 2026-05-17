import math
import numpy as np

class PostureAnalyzer:
    def __init__(self):
        self.slouch_threshold = 15.0 # Angle threshold for slouching

    def get_invalid_state(self):
        return {
            "valid": False,
            "posture_score": 0.0,
            "shoulder_slope": 0.0,
            "neck_angle": 0.0,
            "torso_angle": 0.0,
            "is_slouching": False,
            "posture_status": "Unknown"
        }

    def analyze(self, pose_results):
        if not pose_results or not pose_results.pose_landmarks:
            return self.get_invalid_state()

        landmarks = pose_results.pose_landmarks[0]

        # Extract required landmarks (using indices from mediapipe.solutions.pose)
        l_shoulder = landmarks[11]
        r_shoulder = landmarks[12]
        nose = landmarks[0]
        l_hip = landmarks[23]
        r_hip = landmarks[24]

        # Calculate shoulder slope (angle of line connecting shoulders)
        dx = r_shoulder.x - l_shoulder.x
        dy = r_shoulder.y - l_shoulder.y
        shoulder_slope = math.degrees(math.atan2(dy, dx))

        # Calculate midpoint of shoulders
        mid_shoulder_x = (l_shoulder.x + r_shoulder.x) / 2
        mid_shoulder_y = (l_shoulder.y + r_shoulder.y) / 2

        # Calculate midpoint of hips
        mid_hip_x = (l_hip.x + r_hip.x) / 2
        mid_hip_y = (l_hip.y + r_hip.y) / 2

        # Torso angle relative to vertical
        torso_dx = mid_hip_x - mid_shoulder_x
        torso_dy = mid_hip_y - mid_shoulder_y
        torso_angle = math.degrees(math.atan2(abs(torso_dx), torso_dy))

        # Neck angle (nose to mid-shoulder relative to vertical)
        neck_dx = mid_shoulder_x - nose.x
        neck_dy = mid_shoulder_y - nose.y
        neck_angle = math.degrees(math.atan2(abs(neck_dx), neck_dy))

        is_slouching = neck_angle > self.slouch_threshold or torso_angle > self.slouch_threshold
        status = "Slouching" if is_slouching else "Good Posture"
        
        posture_score = 100.0 if not is_slouching else max(0.0, 100.0 - (max(neck_angle, torso_angle) - self.slouch_threshold) * 2.5)

        return {
            "valid": True,
            "posture_score": posture_score,
            "shoulder_slope": shoulder_slope,
            "neck_angle": neck_angle,
            "torso_angle": torso_angle,
            "is_slouching": is_slouching,
            "posture_status": status
        }
