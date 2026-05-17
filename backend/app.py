import sys
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import cv2
import json
import asyncio
import time
import math

# Add the parent directory to the path so we can import the existing modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from camera import Camera
from landmarks import LandmarkDetector
from attention import AttentionAnalyzer
from posture import PostureAnalyzer
from motion import MotionAnalyzer
from engagement import EngagementScorer
from visualization import Visualizer

app = FastAPI(title="Student Monitoring API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
class SystemState:
    def __init__(self):
        self.camera = None
        self.detector = LandmarkDetector()
        self.attention_analyzer = AttentionAnalyzer()
        self.posture_analyzer = PostureAnalyzer()
        self.motion_analyzer = MotionAnalyzer()
        self.engagement_scorer = EngagementScorer()
        self.visualizer = Visualizer()
        
        self.is_running = False
        self.current_metrics = {
            "engagement": 0,
            "attention": "Unknown",
            "posture": "Unknown",
            "motion": "Unknown",
            "valid": False,
            "error": "Not started",
            "average_attention": 0,
            "warning_triggered": False
        }
        self.session_summary = {
            "session_id": "none",
            "start_time": "",
            "end_time": "",
            "average_attention": 0,
            "average_engagement": 0,
            "no_face_events": 0,
            "multiple_face_events": 0,
            "warning_triggered": False,
            "total_frames": 0,
            "valid_frames": 0,
            "engagement_sum": 0,
            "attention_sum": 0
        }
        self.last_error_state = ""

state = SystemState()

@app.post("/start-session")
def start_session():
    if not state.is_running:
        state.camera = Camera()
        state.is_running = True
        state.session_summary = {
            "session_id": "session_" + str(int(time.time())),
            "start_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "end_time": "",
            "average_attention": 0,
            "average_engagement": 0,
            "no_face_events": 0,
            "multiple_face_events": 0,
            "warning_triggered": False,
            "total_frames": 0,
            "valid_frames": 0,
            "engagement_sum": 0,
            "attention_sum": 0
        }
        state.last_error_state = ""
    return {"status": "started", "session_id": state.session_summary["session_id"]}

@app.post("/end-session")
async def end_session():
    if state.is_running:
        state.is_running = False
        # Give the streaming generator thread a moment to exit its loop safely before releasing hardware resource
        await asyncio.sleep(0.5)
        if state.camera:
            state.camera.release()
            state.camera = None
            
        valid_frames_count = state.session_summary.get("valid_frames", 0)
        if valid_frames_count > 0:
            state.session_summary["average_engagement"] = int(math.ceil(state.session_summary["engagement_sum"] / valid_frames_count))
            state.session_summary["average_attention"] = int(math.ceil(state.session_summary["attention_sum"] / valid_frames_count))
        else:
            state.session_summary["average_engagement"] = 0
            state.session_summary["average_attention"] = 0
            
        state.session_summary["end_time"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        if state.session_summary["average_attention"] < 50:
            state.session_summary["warning_triggered"] = True

        final_summary = {
            "session_id": state.session_summary["session_id"],
            "start_time": state.session_summary["start_time"],
            "end_time": state.session_summary["end_time"],
            "average_attention": state.session_summary["average_attention"],
            "average_engagement": state.session_summary["average_engagement"],
            "no_face_events": state.session_summary["no_face_events"],
            "multiple_face_events": state.session_summary["multiple_face_events"],
            "warning_triggered": state.session_summary["warning_triggered"]
        }

        try:
            filename = f"session_{state.session_summary['session_id']}.json"
            with open(filename, "w") as f:
                json.dump(final_summary, f, indent=4)
        except Exception as e:
            print(f"Error writing session summary file: {e}")

        state.session_summary = final_summary
            
    return {"status": "ended", "summary": state.session_summary}

@app.get("/metrics")
def get_metrics():
    return state.current_metrics

def generate_frames():
    while state.is_running and state.camera:
        frame = state.camera.get_frame()
        if frame is None:
            continue

        # 1. Extract Landmarks & Validate Face
        pose_results, face_results = state.detector.extract_landmarks(frame)
        validation_data = state.detector.validate_face_count(face_results)

        # 2. Get Default (Invalid) States
        attention_data = state.attention_analyzer.get_invalid_state(validation_data["error"])
        posture_data = state.posture_analyzer.get_invalid_state()
        
        # 3. Motion Analysis (Independent, always runs)
        motion_data = state.motion_analyzer.analyze(frame)

        if validation_data["valid"]:
            # 4. Attention & Posture Analysis
            attention_data = state.attention_analyzer.analyze(frame, face_results)
            posture_data = state.posture_analyzer.analyze(pose_results)

        # 5. Engagement Scoring
        engagement_data = state.engagement_scorer.calculate(
            validation_data, attention_data, posture_data, motion_data
        )

        # Update session summary metrics
        if state.is_running:
            state.session_summary["total_frames"] += 1
            
            if validation_data.get("valid", False):
                state.session_summary["valid_frames"] = state.session_summary.get("valid_frames", 0) + 1
                state.session_summary["engagement_sum"] += engagement_data.get("score", 0)
                att_val = attention_data.get("attention_score", 0.0) if attention_data else 0.0
                state.session_summary["attention_sum"] += att_val
            
            current_error = validation_data.get("error", "") if not validation_data.get("valid", False) else ""
            
            # Distinct transition counts for events
            if current_error != state.last_error_state:
                if current_error == "multiple_faces":
                    state.session_summary["multiple_face_events"] += 1
                elif current_error == "no_face":
                    state.session_summary["no_face_events"] += 1
                state.last_error_state = current_error

        # Update metrics for frontend
        running_avg_attention = 85  # default human baseline
        valid_frames_count = state.session_summary.get("valid_frames", 0)
        if valid_frames_count > 0:
            running_avg_attention = int(math.ceil(state.session_summary["attention_sum"] / valid_frames_count))
        else:
            # If no valid frames yet, fallback to current attention score
            running_avg_attention = int(math.ceil(attention_data.get("attention_score", 85.0)))

        # Exclude early startup frames to prevent false trigger on camera initialization
        # Also require at least 5 valid frames to declare a warning
        if running_avg_attention < 50 and valid_frames_count > 5:
            state.session_summary["warning_triggered"] = True

        state.current_metrics = {
            "engagement": int(math.ceil(engagement_data.get("score", 0))),
            "attention": attention_data.get("state", "Unknown").title(),
            "posture": posture_data.get("state", "Unknown").title(),
            "motion": motion_data.get("state", "Unknown").title(),
            "valid": validation_data.get("valid", False),
            "error": validation_data.get("error", ""),
            "average_attention": running_avg_attention,
            "warning_triggered": state.session_summary["warning_triggered"]
        }

        # 6. Visualization Overlay
        if validation_data["valid"]:
            frame = state.detector.draw_landmarks(frame, pose_results, face_results)
            
        frame = state.visualizer.draw_overlays(
            frame, validation_data, attention_data, posture_data, motion_data, engagement_data
        )

        # Encode frame to JPEG
        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.get("/video-feed")
def video_feed():
    if not state.is_running:
        return {"error": "Session not started"}
    return StreamingResponse(generate_frames(), media_type="multipart/x-mixed-replace; boundary=frame")
