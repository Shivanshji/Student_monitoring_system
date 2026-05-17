import numpy as np

class AttentionAnalyzer:
    def __init__(self):
        pass

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
            
        # Normal ratio is roughly ~1.2 to 1.5
        vertical_ratio = eye_to_chin / top_to_eye
        # Normalize pitch: 0 is centered. negative is looking down, positive is looking up.
        nose_offset_y = (1.35 - vertical_ratio) # Approximation

        # 3. FACE CENTERING IN FRAME (Soft indicator)
        frame_center_x = 0.5
        frame_center_y = 0.5
        center_dev_x = abs(nose.x - frame_center_x)
        center_dev_y = abs(nose.y - frame_center_y)
        
        # Create continuous, soft score (Base 100)
        score = 100.0
        
        # Soft penalty for yaw (Exponential decay curve: small deviations barely register)
        yaw_penalty = min(80.0, (abs(nose_offset_x) ** 1.5) * 170.0)
        score -= yaw_penalty
        
        # Soft penalty for pitch 
        pitch_penalty = min(60.0, (abs(nose_offset_y) ** 1.5) * 120.0)
        score -= pitch_penalty
        
        # Very soft penalty for centering (tolerates laptop webcams)
        center_penalty = ((center_dev_x + center_dev_y) ** 2) * 50.0
        score -= center_penalty
        
        # Clamp score between 0 and 100
        score = max(0.0, min(100.0, score))
        
        is_attentive = True # No instant collapse
        
        # Labels: Focused, Slight Left, Slight Right, Slight Up, Slight Down, Distracted, Looking Away
        if score < 20:
            direction = "Looking Away"
        elif score < 45:
            direction = "Distracted"
        elif score < 75:
            if abs(nose_offset_x) > abs(nose_offset_y):
                direction = "Slight Right" if nose_offset_x < 0 else "Slight Left"
            else:
                direction = "Slight Down" if nose_offset_y < 0 else "Slight Up"
        else:
            direction = "Focused"

        # Pseudo values to strictly maintain contract with other modules
        yaw = nose_offset_x * 90.0
        pitch = nose_offset_y * 90.0
        roll = 0.0

        return {
            "valid": True,
            "is_attentive": is_attentive,
            "attention_score": score,
            "error": "",
            "yaw": yaw,
            "pitch": pitch,
            "roll": roll,
            "gaze_direction": direction
        }
