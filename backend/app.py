import sys
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import cv2
import json
import asyncio
import time

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
            "error": "Not started"
        }
        self.session_summary = {
            "session_id": "none",
            "average_engagement": 0,
            "multiple_face_events": 0,
            "face_missing_events": 0,
            "total_frames": 0,
            "engagement_sum": 0
        }

state = SystemState()

@app.post("/start-session")
def start_session():
    if not state.is_running:
        state.camera = Camera()
        state.is_running = True
        state.session_summary = {
            "session_id": "session_" + str(int(time.time())),
            "average_engagement": 0,
            "multiple_face_events": 0,
            "face_missing_events": 0,
            "total_frames": 0,
            "engagement_sum": 0
        }
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
            
        if state.session_summary["total_frames"] > 0:
            state.session_summary["average_engagement"] = int(state.session_summary["engagement_sum"] / state.session_summary["total_frames"])
            
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

        # Update metrics for frontend
        state.current_metrics = {
            "engagement": engagement_data.get("score", 0),
            "attention": attention_data.get("state", "Unknown").title(),
            "posture": posture_data.get("state", "Unknown").title(),
            "motion": motion_data.get("state", "Unknown").title(),
            "valid": validation_data.get("valid", False),
            "error": validation_data.get("error", "")
        }

        # Update session summary
        if state.is_running:
            state.session_summary["total_frames"] += 1
            state.session_summary["engagement_sum"] += engagement_data.get("score", 0)
            if not validation_data.get("valid", False):
                if validation_data.get("error") == "multiple_faces":
                    state.session_summary["multiple_face_events"] += 1
                elif validation_data.get("error") == "no_face":
                    state.session_summary["face_missing_events"] += 1

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
