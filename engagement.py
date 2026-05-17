class EngagementScorer:
    def __init__(self, smoothing_factor=0.92):
        self.smoothing_factor = smoothing_factor
        self.current_score = 100.0

    def calculate(self, validation_data, attention_data, posture_data, motion_data):
        if not validation_data["valid"]:
            self.current_score = 0.0
            return {
                "valid": False,
                "score": 0.0,
                "state": "Invalid",
                "reason": validation_data["error"]
            }

        # Safe defaults
        att_score = attention_data.get("attention_score", 0.0) if attention_data and attention_data.get("valid") else 0.0
        post_score = posture_data.get("posture_score", 0.0) if posture_data and posture_data.get("valid") else 0.0
        
        motion_intensity = min(100.0, motion_data.get("motion_intensity", 0.0)) if motion_data else 0.0
        mot_score = max(0.0, 100.0 - motion_intensity)

        # Base Score calculation (55% Attention, 30% Posture, 15% Motion)
        raw_score = (att_score * 0.55) + (post_score * 0.30) + (mot_score * 0.15)
        raw_score = max(0.0, min(100.0, raw_score))

        # Temporal smoothing (high stability)
        self.current_score = (self.smoothing_factor * self.current_score) + \
                             ((1.0 - self.smoothing_factor) * raw_score)

        # Determine state based on continuous thresholds
        if self.current_score >= 75:
            state = "Highly Engaged"
        elif self.current_score >= 50:
            state = "Engaged"
        elif self.current_score >= 30:
            state = "Distracted"
        else:
            state = "Not Attentive"

        return {
            "valid": True,
            "score": self.current_score,
            "state": state,
            "reason": attention_data.get("gaze_direction", "Unknown") if attention_data else "Unknown"
        }
