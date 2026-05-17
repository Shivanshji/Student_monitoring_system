import cv2

from camera import Camera
from landmarks import LandmarkDetector
from attention import AttentionAnalyzer
from posture import PostureAnalyzer
from motion import MotionAnalyzer
from engagement import EngagementScorer
from visualization import Visualizer

def main():
    camera = Camera()
    detector = LandmarkDetector()
    attention_analyzer = AttentionAnalyzer()
    posture_analyzer = PostureAnalyzer()
    motion_analyzer = MotionAnalyzer()
    engagement_scorer = EngagementScorer()
    visualizer = Visualizer()

    while True:
        frame = camera.get_frame()
        if frame is None:
            break

        # 1. Extract Landmarks & Validate Face
        pose_results, face_results = detector.extract_landmarks(frame)
        validation_data = detector.validate_face_count(face_results)

        # 2. Get Default (Invalid) States
        attention_data = attention_analyzer.get_invalid_state(validation_data["error"])
        posture_data = posture_analyzer.get_invalid_state()
        
        # 3. Motion Analysis (Independent, always runs)
        motion_data = motion_analyzer.analyze(frame)

        if validation_data["valid"]:
            # 4. Attention & Posture Analysis
            attention_data = attention_analyzer.analyze(frame, face_results)
            posture_data = posture_analyzer.analyze(pose_results)

        # 5. Engagement Scoring
        engagement_data = engagement_scorer.calculate(
            validation_data, attention_data, posture_data, motion_data
        )

        # 6. Visualization Overlay
        if validation_data["valid"]:
            frame = detector.draw_landmarks(frame, pose_results, face_results)
            
        frame = visualizer.draw_overlays(
            frame, validation_data, attention_data, posture_data, motion_data, engagement_data
        )

        # Display
        cv2.imshow("Student Monitoring System", frame)

        key = cv2.waitKey(1)
        if key == ord('q'):
            break

    camera.release()

if __name__ == "__main__":
    main()