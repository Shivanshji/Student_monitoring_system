import cv2

class Visualizer:
    def __init__(self):
        self.font = cv2.FONT_HERSHEY_SIMPLEX

    def get_color(self, score):
        if score >= 75:
            return (0, 255, 0)      # Green
        elif score >= 50:
            return (0, 255, 255)    # Yellow
        elif score >= 30:
            return (0, 165, 255)    # Orange
        else:
            return (0, 0, 255)      # Red

    def draw_overlays(self, frame, validation_data, attention, posture, motion, engagement):
        # Draw subtle motion contours if any
        if motion and motion.get("contours"):
            cv2.drawContours(frame, motion["contours"], -1, (0, 255, 255), 1)

        # Transparent dark panel (Compact HUD)
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (330, 150), (20, 20, 20), -1)
        frame = cv2.addWeighted(overlay, 0.7, frame, 0.3, 0)

        y_offset = 35
        line_spacing = 25

        if not validation_data["valid"]:
            # Critical Validation Warning ONLY for no face or multiple faces
            cv2.rectangle(frame, (0, 0), (frame.shape[1], 40), (0, 0, 200), -1)
            cv2.putText(frame, f"CRITICAL: {validation_data['error']}", (20, 28), 
                        self.font, 0.7, (255, 255, 255), 2)
            
            # Simple HUD for invalid state
            cv2.putText(frame, "Engagement: N/A", (20, y_offset + line_spacing), self.font, 0.6, (150, 150, 150), 1)
            return frame

        # PRIMARY: Engagement
        score = engagement.get("score", 0.0)
        state = engagement.get("state", "Unknown")
        color = self.get_color(score)
        
        cv2.putText(frame, f"Engagement: {score:.1f}% ({state})", (20, y_offset), 
                    self.font, 0.65, color, 2)
        y_offset += line_spacing

        # SECONDARY: Attention
        gaze = attention.get("gaze_direction", "Unknown")
        att_score = attention.get("attention_score", 0.0)
        att_color = self.get_color(att_score)
        
        cv2.putText(frame, f"Attention: {att_score:.0f}% | {gaze}", (20, y_offset), 
                    self.font, 0.55, att_color, 1)
        y_offset += line_spacing

        # TERTIARY: Posture + Motion
        posture_status = posture.get("posture_status", "Unknown") if posture else "Unknown"
        motion_status = motion.get("status", "Unknown") if motion else "Unknown"
        
        cv2.putText(frame, f"Posture: {posture_status}", (20, y_offset), 
                    self.font, 0.5, (200, 200, 200), 1)
        y_offset += line_spacing
        cv2.putText(frame, f"Motion : {motion_status}", (20, y_offset), 
                    self.font, 0.5, (200, 200, 200), 1)

        return frame
