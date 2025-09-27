import logging
from flask import Blueprint, request, jsonify, current_app
from models.database import db
from models.student import Student
from services.attendance_service import get_face_embedding_from_image, add_student_to_known_faces

logger = logging.getLogger(__name__)
registration_bp = Blueprint('registration_api', __name__)

def allowed_file(filename):
    """Checks if the file's extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@registration_bp.route('/api/register', methods=['POST'])
def register_student():
    # 1. --- Validate Input ---
    if 'face_image' not in request.files:
        return jsonify({"error": "No image file provided."}), 400

    image_file = request.files['face_image']
    student_code = request.form.get('student_code')
    full_name = request.form.get('full_name')

    if not all([student_code, full_name, image_file]):
        return jsonify({"error": "Missing form data. Please fill out all fields."}), 400
    
    if not allowed_file(image_file.filename):
        return jsonify({"error": "Invalid image format. Please use PNG, JPG, or JPEG."}), 400

    # 2. --- Check for Existing Student ---
    if Student.query.filter_by(student_code=student_code).first():
        return jsonify({"error": f"A student with ID {student_code} already exists"}), 409 # 409 Conflict

    # 3. --- Process Image and Get Embedding ---
    try:
        # Get embedding and check for face detection errors
        embedding, num_faces = get_face_embedding_from_image(image_file)

        if embedding is None:
            if num_faces == 0:
                error_message = "No face could be detected. Please use a clear, forward-facing photo."
            else:
                error_message = f"Multiple ({num_faces}) faces were detected. Please upload an image with only one person."
            return jsonify({"error": error_message}), 400
        
        # Create and save the new student
        new_student = Student(
            student_code=student_code, # type: ignore
            full_name=full_name, # type: ignore
        )
        new_student.set_embedding(embedding)
        db.session.add(new_student)
        db.session.commit()
        
        # Reload known faces in memory to include the new student
        add_student_to_known_faces(new_student)

        logger.info(f"Successfully registered new student: {full_name} ({student_code})")
        return jsonify({
            "message": "Student registered successfully!",
            "student": {"full_name": full_name, "student_code": student_code}
        }), 201 # 201 Created

    except Exception as e:
        db.session.rollback()
        logger.error(f"Database error during registration for student {student_code}: {e}")
        return jsonify({"error": "An unexpected error occurred on the server."}), 500