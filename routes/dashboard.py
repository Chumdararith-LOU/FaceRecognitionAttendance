# In routes/dashboard.py (create this new file)

from flask import Blueprint, render_template, Response
import cv2
from services.attendance_service import recognize_faces_in_frame

dashboard_bp = Blueprint('dashboard_api', __name__)

def generate_frames():
    """
    Generator function to capture frames from the camera, process them,
    and yield them as a byte stream.
    """
    camera = cv2.VideoCapture(0) # Use 0 for the default webcam
    if not camera.isOpened():
        raise RuntimeError("Could not start camera.")

    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            # Process the frame (detect faces, etc.)
            processed_frame = recognize_faces_in_frame(frame)

            # Encode the frame in JPEG format
            ret, buffer = cv2.imencode('.jpg', processed_frame)
            frame_bytes = buffer.tobytes()

            # Yield the frame in the multipart format
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@dashboard_bp.route('/dashboard')
def dashboard():
    """Renders the dashboard page."""
    return render_template('dashboard.html')

@dashboard_bp.route('/video_feed')
def video_feed():
    """Video streaming route. Returns a multipart response."""
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')