
"""
Facial landmarks detection module
"""

import cv2
import mediapipe as mp

from mediapipe.tasks import python
from mediapipe.tasks.python import vision


class LandmarkDetector:
    """Detects pose and face landmarks using MediaPipe Tasks API."""

    def __init__(self):
        # ------------------------------------------------------------------
        # Pose Landmarker
        # ------------------------------------------------------------------
        pose_base_options = python.BaseOptions(
            model_asset_path="models/pose_landmarker_lite.task"
        )

        pose_options = vision.PoseLandmarkerOptions(
            base_options=pose_base_options,
            running_mode=vision.RunningMode.IMAGE,
            min_pose_detection_confidence=0.5,
            min_tracking_confidence=0.5,
            min_pose_presence_confidence=0.5,
            num_poses=1,
        )

        self.pose = vision.PoseLandmarker.create_from_options(
            pose_options
        )

        # ------------------------------------------------------------------
        # Face Landmarker
        # ------------------------------------------------------------------
        face_base_options = python.BaseOptions(
            model_asset_path="models/face_landmarker.task"
        )

        face_options = vision.FaceLandmarkerOptions(
            base_options=face_base_options,
            running_mode=vision.RunningMode.IMAGE,
            num_faces=2,
            min_face_detection_confidence=0.5,
            min_tracking_confidence=0.5,
            min_face_presence_confidence=0.5,
            output_face_blendshapes=False,
            output_facial_transformation_matrixes=False,
        )

        self.face_mesh = vision.FaceLandmarker.create_from_options(
            face_options
        )

        # Drawing utilities removed to avoid matplotlib and solutions module dependency in 0.10.30+

    def extract_landmarks(self, frame):
        """
        Convert BGR frame to RGB, run pose and face detectors,
        and return results.
        """

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb_frame,
        )

        pose_results = self.pose.detect(mp_image)
        face_results = self.face_mesh.detect(mp_image)

        return pose_results, face_results

    def validate_face_count(self, face_results):
        if not face_results or not face_results.face_landmarks:
            return {"valid": False, "face_count": 0, "error": "No Face Detected"}
        
        count = len(face_results.face_landmarks)
        if count > 1:
            return {"valid": False, "face_count": count, "error": "Multiple Faces Detected"}
            
        return {"valid": True, "face_count": 1, "error": ""}

    def draw_landmarks(self, frame, pose_results, face_results):
        """Overlay pose and face landmarks on the frame using pure cv2."""
        ih, iw, _ = frame.shape

        # --------------------------------------------------------------
        # Pose landmarks
        # --------------------------------------------------------------
        if pose_results.pose_landmarks:
            for pose_landmarks in pose_results.pose_landmarks:
                for landmark in pose_landmarks:
                    if landmark.visibility and landmark.visibility > 0.5:
                        x = int(landmark.x * iw)
                        y = int(landmark.y * ih)
                        cv2.circle(frame, (x, y), 3, (0, 255, 0), -1)

        # --------------------------------------------------------------
        # Face landmarks
        # --------------------------------------------------------------
        if face_results.face_landmarks:
            minimal_indices = {1, 33, 263, 61, 291, 152} # Nose, eyes, mouth corners, chin
            for face_landmarks in face_results.face_landmarks:
                for idx, landmark in enumerate(face_landmarks):
                    if idx in minimal_indices:
                        x = int(landmark.x * iw)
                        y = int(landmark.y * ih)
                        cv2.circle(frame, (x, y), 2, (200, 200, 200), -1)

        return frame

