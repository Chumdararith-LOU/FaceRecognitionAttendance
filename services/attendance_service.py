import os
import cv2
import numpy as np
import logging 
from datetime import datetime, timedelta, date
import openvino.runtime as ov
from scipy.spatial.distance import cosine
from flask import current_app
from extensions import socketio
from models.attendance import AttendanceRecord
from models.student import Student
from models.database import db
from sqlalchemy import func, distinct

logger = logging.getLogger(__name__)

# Get the absolute path of the directory where this file is located 
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Go up one level to the project root 
PROJECT_ROOT = os.path.dirname(BASE_DIR)
# --- OpenVINO Model and App Configuration ---
core = ov.Core()

# Define model variables as None initially. They will be loaded by initialize_models().
compiled_face_detection_model = None
compiled_face_embedding_model = None
detection_input_layer = None
detection_output_layer = None
embedding_input_layer = None
embedding_output_layer = None

def initialize_models():
    """Loads and compiles models from paths specified in the app config."""
    global compiled_face_detection_model, compiled_face_embedding_model
    global detection_input_layer, detection_output_layer, embedding_input_layer, embedding_output_layer
    
    # Check if models are already loaded to prevent re-initialization
    if compiled_face_detection_model is not None:
        return

    try:
        # Read model paths directly from the Flask app's configuration
        detection_model_path = current_app.config['FACE_DETECTION_MODEL']
        embedding_model_path = current_app.config['FACE_EMBEDDING_MODEL']
        
        logger.info(f"Loading detection model from: {detection_model_path}")
        face_detection_model = core.read_model(model=detection_model_path)
        compiled_face_detection_model = core.compile_model(model=face_detection_model, device_name="CPU")
        
        # Get input and output layers for detection model
        detection_input_layer = compiled_face_detection_model.input(0)
        detection_output_layer = compiled_face_detection_model.output(0)

        logger.info(f"Loading embedding model from: {embedding_model_path}")
        face_embedding_model = core.read_model(model=embedding_model_path)
        compiled_face_embedding_model = core.compile_model(model=face_embedding_model, device_name="CPU")

        # Get input and output layers for embedding model
        embedding_input_layer = compiled_face_embedding_model.input(0)
        embedding_output_layer = compiled_face_embedding_model.output(0)
        
        logger.info("OpenVINO models initialized successfully.")

    except Exception as e:
        logger.error(f"Failed to initialize OpenVINO models: {e}")

# In-memory cache for known faces
known_face_encodings = []
known_face_metadata = []

# Cooldown tracking for attendance logging
last_seen_students = {}
ATTENDANCE_COOLDOWN = timedelta(seconds=10) # Reduced cooldown for testing performance
RECOGNITION_THRESHOLD = 0.4 # Cosine distance threshold (lower is stricter)

def load_known_faces():
    """Loads all student face embeddings from the database into memory."""
    global known_face_encodings, known_face_metadata
    known_face_encodings.clear()
    known_face_metadata.clear()

    with current_app.app_context():
        students = Student.query.filter(Student.face_embedding.isnot(None)).all()
        for student in students:
            known_face_encodings.append(student.get_embedding())
            known_face_metadata.append({
                'student_id': student.id,
                'full_name': student.full_name
            })
    print(f"Loaded {len(known_face_encodings)} known faces.")

def preprocess_frame(frame, target_shape):
    """Preprocesses a frame to the model's required input shape."""
    n, c, h, w = target_shape
    resized_frame = cv2.resize(frame, (w, h))
    transposed_frame = resized_frame.transpose(2, 0, 1) # HWC to CHW
    input_tensor = np.expand_dims(transposed_frame, 0).astype(np.float32) # Add batch dimension
    return input_tensor

def recognize_and_log_attendance(frame):

    if compiled_face_detection_model is None or compiled_face_embedding_model is None:
        logger.warning("Models not initialized, skipping frame processing.")
        return frame
        
    initialize_models()
    original_h, original_w = frame.shape[:2]
    
    # Preprocess and detect faces
    input_tensor = preprocess_frame(frame, detection_input_layer.shape)
    detection_results = compiled_face_detection_model([input_tensor])[detection_output_layer]

    current_time = datetime.now()

    for detection in detection_results[0][0]:
        confidence = float(detection[2])
        if confidence > 0.8:
            xmin = int(detection[3] * original_w)
            ymin = int(detection[4] * original_h)
            xmax = int(detection[5] * original_w)
            ymax = int(detection[6] * original_h)

            # Crop the face from the original frame
            face_crop = frame[ymin:ymax, xmin:xmax]
            if face_crop.size == 0: continue

            # Preprocess and get embedding for the cropped face
            embedding_tensor = preprocess_frame(face_crop, embedding_input_layer.shape)
            face_embedding_raw = compiled_face_embedding_model([embedding_tensor])[embedding_output_layer]
            
            face_embedding = face_embedding_raw.flatten()
            
            name = "Unknown"
            if known_face_encodings:
                distances = [cosine(face_embedding, known_embedding) for known_embedding in known_face_encodings]
                best_match_index = np.argmin(distances)
                
                if distances[best_match_index] < RECOGNITION_THRESHOLD:
                    metadata = known_face_metadata[best_match_index]
                    name = metadata['full_name']
                    student_id = metadata['student_id']

                    # --- ATTENDANCE LOGIC ---
                    last_seen_time = last_seen_students.get(student_id)
                    if last_seen_time is None or (current_time - last_seen_time) > ATTENDANCE_COOLDOWN:
                        with current_app.app_context():
                            try:
                                new_record = AttendanceRecord(student_id=student_id)
                                db.session.add(new_record)
                                db.session.commit()
                                last_seen_students[student_id] = current_time
                                logger.info(f"Logged attendance for {name} at {current_time}")

                                # --- ADDED WEBSOCKET BLOCK ---
                                student = Student.query.get(student_id)
                                if student:
                                    try:
                                        # 1. Prepare the data for the new check-in
                                        new_check_in_data = {
                                            'full_name': student.full_name,
                                            'student_code': student.student_code,
                                            'timestamp': new_record.timestamp.strftime('%I:%M:%S %p')
                                        }
                                        
                                        # 2. Get the updated dashboard stats
                                        updated_dashboard_data = get_attendance_summary()
                                        
                                        # 3. Emit the event with both pieces of data
                                        socketio.emit('attendance_update', {
                                            'new_check_in': new_check_in_data,
                                            'dashboard_data': updated_dashboard_data
                                        })
                                        logger.info(f"Sent 'attendance_update' for {student.full_name}")

                                    except Exception as e:
                                        logger.error(f"Error emitting socket event for attendance update: {e}")
                                else:
                                    logger.warning(f"Could not find student with ID {student_id} to emit socket event.")
                                # --- END OF ADDED WEBSOCKET BLOCK ---

                            except Exception as e:
                                db.session.rollback()
                                logger.error(f"Error logging attendance for student_id {student_id}: {e}")

            # Draw bounding box and name
            cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), (0, 255, 0), 2)
            cv2.putText(frame, name, (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
            
    return frame

def get_face_embedding_from_image(image_file):
    """
    Finds a single face in an image and returns its OpenVINO embedding.
    This function is now used by the registration route.
    """
    initialize_models()

    if compiled_face_detection_model is None or embedding_input_layer is None:
         logger.error("Models failed to initialize. Cannot get embedding.")
         return None, 0

    image_data = np.frombuffer(image_file.read(), np.uint8)
    frame = cv2.imdecode(image_data, cv2.IMREAD_COLOR)

    if frame is None:
        print("ERROR: The uploaded image could not be decoded by OpenCV.")
        return None, 0
    
    original_h, original_w = frame.shape[:2]

    input_tensor = preprocess_frame(frame, detection_input_layer.shape)
    detection_results = compiled_face_detection_model([input_tensor])[detection_output_layer]

    detections = [d for d in detection_results[0][0] if d[2] > 0.8]

    if len(detections) != 1:
        return None, len(detections) # Ensure only one face for registration

    detection = detections[0]
    xmin = int(detection[3] * original_w)
    ymin = int(detection[4] * original_h)
    xmax = int(detection[5] * original_w)
    ymax = int(detection[6] * original_h)
    
    face_crop = frame[ymin:ymax, xmin:xmax]
    if face_crop.size == 0: return None, 1
    
    embedding_tensor = preprocess_frame(face_crop, embedding_input_layer.shape)
    face_embedding = compiled_face_embedding_model([embedding_tensor])[embedding_output_layer][0]
    
    return face_embedding.flatten(), 1

def mark_attendance(student_id):
    time_threshold = datetime.utcnow() - timedelta(minutes=1) # Check for attendance in the last minute
    recent_attendance = AttendanceRecord.query.filter(
        AttendanceRecord.student_id == student_id,
        AttendanceRecord.timestamp > time_threshold
    ).first()

    # This block should already exist
    if not recent_attendance:
        new_record = AttendanceRecord(student_id=student_id)
        db.session.add(new_record)
        db.session.commit()
        
        student = Student.query.get(student_id)
        logger.info(f"Attendance marked for {student.full_name}")

        dashboard_data = get_attendance_summary()

        # Create the payload for the new check-in
        new_check_in = {
            'full_name': student.full_name,
            'timestamp': new_record.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Emit a single event with all the data
        socketio.emit('attendance_update', {
            'new_check_in': new_check_in,
            'dashboard_data': dashboard_data
        })

        return True
    return False

def add_student_to_known_faces(student):
    """
    Dynamically adds a newly registered student's face embedding and metadata
    to the in-memory cache without reloading the entire database.
    """
    global known_face_encodings, known_face_metadata
    
    embedding = student.get_embedding()
    if embedding is not None:
        known_face_encodings.append(embedding)
        known_face_metadata.append({
            'student_id': student.id,
            'full_name': student.full_name
        })
        logger.info(f"Appended new student {student.full_name} to in-memory cache.")

def get_attendance_summary():
    """
    Fetches attendance statistics and records for the dashboard,
    returning them in the nested format expected by the frontend.
    """
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())

    # --- Part 1: Calculate Statistics ---
    total_students = db.session.query(func.count(Student.id)).scalar() or 0
    
    # Students present today (counting distinct students)
    students_present_today_count = db.session.query(func.count(distinct(AttendanceRecord.student_id))).\
        filter(func.date(AttendanceRecord.timestamp) == today).\
        scalar() or 0
    
    # Students absent today
    absent_count = total_students - students_present_today_count
    
    # Weekly attendance percentage
    weekly_records = db.session.query(distinct(AttendanceRecord.student_id), func.date(AttendanceRecord.timestamp)).\
        filter(func.date(AttendanceRecord.timestamp) >= start_of_week).count()
    
    days_passed_this_week = today.weekday() + 1
    potential_attendance_slots = total_students * days_passed_this_week if total_students else 0
    weekly_attendance_percentage = (weekly_records / potential_attendance_slots) * 100 if potential_attendance_slots > 0 else 0

    # --- Part 2: Fetch Today's Attendance Records ---
    todays_attendance_records = db.session.query(
        Student.full_name,
        AttendanceRecord.timestamp
    ).join(Student, Student.id == AttendanceRecord.student_id)\
     .filter(func.date(AttendanceRecord.timestamp) == today)\
     .order_by(AttendanceRecord.timestamp.desc())\
     .all()

    todays_attendance = [
        {"full_name": name, "timestamp": ts.strftime('%I:%M:%S %p')}
        for name, ts in todays_attendance_records
    ]

    # --- Part 3: Return in Nested Format ---
    stats = {
        "total_students": total_students,
        "present_today": students_present_today_count,
        "absent_today": absent_count,
        "weekly_attendance_percentage": round(weekly_attendance_percentage, 2)
    }

    return {
        "stats": stats,
        "todays_attendance": todays_attendance
    }