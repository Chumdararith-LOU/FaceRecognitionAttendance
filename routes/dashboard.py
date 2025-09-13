# In routes/dashboard.py (create this new file)
import cv2
from flask import Blueprint, render_template, Response
from services.attendance_service import recognize_and_log_attendance
from flask import jsonify
from models import AttendanceRecord, Student
from sqlalchemy import func
from datetime import date
from models.database import db
from flask_login import login_required
from utils.exporter import generate_attendance_csv
from flask import make_response

dashboard_bp = Blueprint('dashboard_api', __name__)

def generate_frames():
    """
    Generator function to capture frames from the camera, process them,
    and yield them as a byte stream.
    """
    from app import app

    camera = cv2.VideoCapture(0) # Use 0 for the default webcam
    if not camera.isOpened():
        raise RuntimeError("Could not start camera.")
    frame_count = 0
    while True:
        success, frame = camera.read()
        if not success:
            break

        frame_count += 1
        if frame_count % 5 == 0:
            # Process the frame (detect faces, etc.)
            with app.app_context():
                processed_frame = recognize_and_log_attendance(frame)

            # Encode the frame in JPEG format
            ret, buffer = cv2.imencode('.jpg', processed_frame)
            frame_bytes = buffer.tobytes()

            # Yield the frame in the multipart format
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@dashboard_bp.route('/dashboard')
@login_required
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
    Returns a list of students marked present today, showing the most recent time.
    """
    today = date.today()

    # --- REVISED AND MORE ROBUST QUERY ---
    try:
        # Using func.cast for safer date comparison and ordering by the aggregate function
        records = db.session.query(
            Student.full_name,
            func.max(AttendanceRecord.timestamp).label('last_seen')
        ).join(Student, AttendanceRecord.student_id == Student.id)\
         .filter(func.cast(AttendanceRecord.timestamp, db.Date) == today)\
         .group_by(Student.id, Student.full_name)\
         .order_by(func.max(AttendanceRecord.timestamp).desc())\
         .all()

        attendance_list = [
            {"full_name": record.full_name, "timestamp": record.last_seen.strftime("%I:%M:%S %p")}
            for record in records
        ]
        
        return jsonify(attendance_list)

    except Exception as e:
        # Log the actual error to the server console for debugging
        print(f"!!! DATABASE ERROR in get_todays_attendance: {e}")
        # Return a proper JSON error response to the frontend
        return jsonify({"error": "An internal server error occurred."}), 500

@dashboard_bp.route('/api/export/csv')
@login_required
def export_csv():
    """
    Generates and serves a CSV file of today's attendance records.
    """
    today = date.today()
    
    # This is the same query from our get_todays_attendance route
    records = db.session.query(
        Student.full_name,
        func.max(AttendanceRecord.timestamp).label('last_seen')
    ).join(Student, AttendanceRecord.student_id == Student.id)\
     .filter(func.cast(AttendanceRecord.timestamp, db.Date) == today)\
     .group_by(Student.id, Student.full_name)\
     .order_by(func.max(AttendanceRecord.timestamp).desc())\
     .all()
    
    csv_data = generate_attendance_csv(records)
    
    # Create a Flask response object
    response = make_response(csv_data)
    
    # Set headers to trigger a file download
    filename = f"attendance_{today.strftime('%Y-%m-%d')}.csv"
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"
    response.headers["Content-Type"] = "text/csv"
    
    return response