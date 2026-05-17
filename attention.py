import numpy as np
import math

class AttentionAnalyzer:
    def __init__(self):
        self.current_attention = 80.0

    def get_invalid_state(self, error_msg):
        return {
            "valid": False, 
            "is_attentive": False, 
            "attention_score": 0.0, 
            "error": error_msg,
            "yaw": 0.0, 
            "pitch": 0.0, 
            "roll": 0.0, 
            "gaze_direction": "Unknown"
        }

    def analyze(self, frame, face_results):
        if not face_results or not face_results.face_landmarks:
            # Gradually decay current_attention towards 0.0 when face is not found
            self.current_attention = 0.85 * self.current_attention + 0.15 * 0.0
            return self.get_invalid_state("No face landmarks")

        face_landmarks = face_results.face_landmarks[0]
        ih, iw, _ = frame.shape

        # Key Landmarks for stable 2D geometry estimation
        # Nose: 1
        # Left eye corner: 33
        # Right eye corner: 263
        # Chin: 152
        # Top of head: 10
        nose = face_landmarks[1]
        l_eye = face_landmarks[33]
        r_eye = face_landmarks[263]
        chin = face_landmarks[152]
        head_top = face_landmarks[10]

        # 1. NOSE OFFSET FROM EYE MIDPOINT (YAW estimation)
        mid_eye_x = (l_eye.x + r_eye.x) / 2
        eye_dist_x = abs(r_eye.x - l_eye.x)
        
        # Avoid division by zero
        if eye_dist_x < 0.01:
            eye_dist_x = 0.01

        # Deviation of nose from midpoint relative to eye distance
        # 0 = perfectly centered. 
        # > 0.2 is starting to turn.
        nose_offset_x = (nose.x - mid_eye_x) / eye_dist_x

        # 2. PITCH ESTIMATION
        # Ratio of eye-to-chin vs head_top-to-eye
        mid_eye_y = (l_eye.y + r_eye.y) / 2
        eye_to_chin = chin.y - mid_eye_y
        top_to_eye = mid_eye_y - head_top.y
        
        if top_to_eye < 0.01:
            top_to_eye = 0.01
            
        # Normal ratio is roughly ~1.0 to 1.3
        vertical_ratio = eye_to_chin / top_to_eye
        # Normalize pitch: centered around 1.10 (more robust baseline for webcam tilt)
        nose_offset_y = (1.10 - vertical_ratio)

        # 3. FACE CENTERING IN FRAME (Soft indicator)
        frame_center_x = 0.5
        frame_center_y = 0.5
        center_dev_x = abs(nose.x - frame_center_x)
        center_dev_y = abs(nose.y - frame_center_y)
        
        # Raw value absolute deviations
        yaw_abs = abs(nose_offset_x)
        pitch_abs = abs(nose_offset_y)

        # Baseline Human Assumption
        score = 85.0

        # Highly tolerant Yaw dead zone (0.28) and soft penalty curve
        if yaw_abs < 0.28:
            yaw_penalty = 0.0
        else:
            yaw_penalty = ((yaw_abs - 0.28) ** 1.8) * 60.0
        yaw_penalty = max(0.0, min(80.0, yaw_penalty))
        score -= yaw_penalty

        # Highly tolerant Pitch dead zone (0.35) and soft penalty curve
        if pitch_abs < 0.35:
            pitch_penalty = 0.0
        else:
            pitch_penalty = ((pitch_abs - 0.35) ** 2.0) * 35.0
        pitch_penalty = max(0.0, min(45.0, pitch_penalty))
        score -= pitch_penalty

        # Extremely low centering penalty (tolerates sitting off-center)
        center_penalty = ((center_dev_x + center_dev_y) ** 2) * 5.0
        score -= center_penalty

        # Alignment bonus: generous alignment bonus when within dead zones
        alignment_bonus = 0.0
        if yaw_abs < 0.28 and pitch_abs < 0.35:
            yaw_factor = (0.28 - yaw_abs) / 0.28
            pitch_factor = (0.35 - pitch_abs) / 0.35
            alignment_bonus = 15.0 * (yaw_factor * pitch_factor)
        score += alignment_bonus

        # Clamp raw score between 0 and 100
        score = max(0.0, min(100.0, score))

        # Temporal Smoothing
        self.current_attention = 0.85 * self.current_attention + 0.15 * score
        self.current_attention = max(0.0, min(100.0, self.current_attention))

        smoothed_score = int(math.ceil(self.current_attention))
        is_attentive = smoothed_score >= 40.0

        # Recalibrated Attention Labels
        if smoothed_score >= 80:
            direction = "Focused"
        elif smoothed_score >= 60:
            direction = "Attentive"
        elif smoothed_score >= 40:
            direction = "Slightly Distracted"
        elif smoothed_score >= 20:
            direction = "Distracted"
        else:
            direction = "Looking Away"

        # Pseudo values to strictly maintain contract with other modules
        yaw = nose_offset_x * 90.0
        pitch = nose_offset_y * 90.0
        roll = 0.0

        return {
            "valid": True,
            "is_attentive": is_attentive,
            "attention_score": smoothed_score,
            "error": "",
            "yaw": yaw,
            "pitch": pitch,
            "roll": roll,
            "gaze_direction": direction
        }
