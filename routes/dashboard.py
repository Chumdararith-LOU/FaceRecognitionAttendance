import cv2
import logging
from flask import Blueprint, render_template, Response, jsonify, make_response, current_app
from flask_login import login_required
from utils.exporter import generate_attendance_csv
from extensions import socketio
from services.attendance_service import recognize_and_log_attendance, get_attendance_summary



dashboard_bp = Blueprint('dashboard_api', __name__, template_folder='../templates')
logger = logging.getLogger(__name__)

def generate_frames(app):
    """
    Generator function to capture frames from the camera, process them,
    and yield them as a byte stream.
    """

    camera = cv2.VideoCapture(0) # Use 0 for the default webcam
    if not camera.isOpened():
        raise RuntimeError("Could not start camera.")
    
    frame_count = 0
    while True:
        success, frame = camera.read()
        if not success:
            break

        frame_count += 1
        # Process every 5th frame to save resources
        if frame_count % 5 == 0:
            # 2. Use the passed 'app' object for the context
            with app.app_context():
                processed_frame = recognize_and_log_attendance(frame)

            # Encode the frame in JPEG format
            ret, buffer = cv2.imencode('.jpg', processed_frame)
            if not ret:
                continue
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
    """Route to stream video frames."""
    # 3. Pass the actual application object to the generator
    app = current_app._get_current_object()
    return Response(generate_frames(app),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

# --- Simplify the get_dashboard_data() function ---
@dashboard_bp.route('/api/dashboard_data')
@login_required
def get_dashboard_data():
    """
    API endpoint to fetch dashboard data.
    Calls the attendance service to get the data and returns it as JSON.
    """
    try:
        data = get_attendance_summary()
        return jsonify(data)
    except Exception as e:
        logger.error(f"Error fetching dashboard data: {e}")
        return jsonify({"error": "Could not retrieve dashboard data"}), 500

@dashboard_bp.route('/api/export/csv', methods=['GET', 'POST'])
@login_required
def export_csv():
    """
    Generates and serves a CSV file of today's attendance records.
    """
    try:
        # Get data from the service
        data = get_attendance_summary()
        
        # Extract today's attendance records
        todays_attendance = data.get('todays_attendance', [])
        
        # Debug: Print the structure of the first record
        if todays_attendance:
            print(f"First record type: {type(todays_attendance[0])}")
            print(f"First record: {todays_attendance[0]}")
        
        # Generate CSV data
        csv_data = generate_attendance_csv(todays_attendance)
        
        # Create a Flask response object
        response = make_response(csv_data)
        
        # Set headers to trigger a file download
        from datetime import date
        today = date.today()
        filename = f"attendance_{today.strftime('%Y-%m-%d')}.csv"
        response.headers["Content-Disposition"] = f"attachment; filename={filename}"
        response.headers["Content-Type"] = "text/csv"
        
        return response
        
    except Exception as e:
        logger.error(f"Error generating CSV: {e}")
        return jsonify({"error": "Could not generate CSV file"}), 500

# --- SocketIO event handler (updated to use service) ---
@socketio.on('connect')
def handle_connect():
    """Send initial dashboard data to a newly connected client."""
    print('Client connected')
    try:
        initial_data = get_attendance_summary()
        socketio.emit('initial_state', initial_data)
    except Exception as e:
        logger.error(f"Error sending initial data via SocketIO: {e}")