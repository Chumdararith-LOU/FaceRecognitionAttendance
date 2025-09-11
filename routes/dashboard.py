# In routes/dashboard.py (create this new file)
import cv2
from flask import Blueprint, render_template, Response
from services.attendance_service import recognize_and_log_attendance
from flask import jsonify
from models import AttendanceRecord, Student
from sqlalchemy import func
from datetime import date
from models.database import db

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
            processed_frame = recognize_and_log_attendance(frame)

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

@dashboard_bp.route('/api/attendance/today', methods=['GET'])
def get_todays_attendance():
    """
    Returns a list of students marked present today.
    """
    today = date.today()
    
    # Query that joins AttendanceRecord with Student and filters for today
    records = db.session.query(
        Student.full_name,
        func.min(AttendanceRecord.timestamp).label('first_seen')
    ).join(Student, AttendanceRecord.student_id == Student.id)\
     .filter(func.date(AttendanceRecord.timestamp) == today)\
     .group_by(Student.full_name)\
     .order_by('first_seen')\
     .all()

    # Format the data for JSON response
    attendance_list = [
        {"full_name": record.full_name, "timestamp": record.first_seen.strftime("%I:%M:%S %p")}
        for record in records
    ]
    
    return jsonify(attendance_list)