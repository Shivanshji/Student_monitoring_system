# Student Monitoring System

## Overview
A real-time computer vision system designed to monitor student engagement, attention, posture, and motion during online sessions or classroom environments. It utilizes MediaPipe Tasks API for robust tracking and OpenCV for rendering a clean, lightweight HUD. 

The system acts as a probabilistic, continuous human behavior model, ensuring stability and realistic tracking without aggressive binary penalties.

## Features
* **Face Validation**: Gatekeeps processing by ensuring exactly one face is detected. Warns on multiple faces or absence.
* **Attention Estimation**: Analyzes facial geometry (yaw and pitch via 2D landmarks) to score gaze alignment smoothly over time.
* **Posture Analysis**: Evaluates shoulder and neck alignment to detect slouching and contribute to the engagement score.
* **Motion Tracking**: Determines inactivity or high movement status.
* **Engagement Scoring**: Weighs attention (55%), posture (30%), and motion (15%) into a stabilized, continuous percentage.
* **Compact HUD Visualization**: Clean overlaid UI with color-coded alerts and minimalistic landmark tracking to reduce visual clutter.

## Requirements
* Python 3.11+
* OpenCV (opencv-python)
* MediaPipe (mediapipe)
* NumPy (numpy)

## Setup Instructions
1. Clone the repository to your local machine.
2. Initialize a Python virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application
Make sure you have your webcam accessible and your virtual environment activated, then run:

```bash
python main.py
```

Press `q` on your keyboard while the window is focused to exit the application.
