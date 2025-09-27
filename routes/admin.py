import logging
from flask import Blueprint, current_app, jsonify, render_template, request, redirect, url_for, flash
from flask_login import login_required
from models import Student, AttendanceRecord
from models.database import db
from utils.decorators import admin_required
import datetime

admin_bp = Blueprint('admin_api', __name__, template_folder='../templates')
logger = logging.getLogger(__name__)

@admin_bp.route('/admin/dashboard', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_dashboard():
    """
    Handles the admin dashboard, which includes manually marking attendance 
    and viewing student and attendance data.
    """
    if request.method == 'POST':
        student_id = request.form.get('student_id')
        
        if not student_id:
            flash("No student selected.", "warning")
            return redirect(url_for('admin_api.admin_dashboard'))

        try:
            student = Student.query.get(student_id)
            if student:
                # Create a new attendance record for this student
                new_record = AttendanceRecord(student_id=student.id, timestamp=datetime.datetime.utcnow())
                db.session.add(new_record)
                db.session.commit()
                flash(f"Successfully marked {student.full_name} as present.", "success")
            else:
                flash("Student not found.", "error")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error in manual attendance: {e}")
            flash(f"An error occurred while marking attendance.", "error")
        
        return redirect(url_for('admin_api.admin_dashboard'))

    # For GET requests, fetch data for the dashboard
    students = Student.query.order_by(Student.full_name).all()
    
    # Fetch the 15 most recent attendance records to display on the dashboard
    recent_records = db.session.query(
        AttendanceRecord.timestamp,
        Student.full_name
    ).join(Student, AttendanceRecord.student_id == Student.id).order_by(
        AttendanceRecord.timestamp.desc()
    ).limit(15).all()

    return render_template('admin.html', students=students, recent_records=recent_records)

@admin_bp.route('/admin')
@login_required
@admin_required
def manage_students():
    """Renders the student management page for admins."""
    try:
        students = Student.query.order_by(Student.full_name).all()
        return render_template('admin.html', students=students)
    except Exception as e:
        logger.error(f"Error fetching students for admin page: {e}")
        flash("Error loading student data.", "error")
        return render_template('admin.html', students=[])

@admin_bp.route('/api/students/<int:student_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_student(student_id):
    """API endpoint to delete a student and their attendance records."""
    try:
        student = Student.query.get_or_404(student_id)
        student_name = student.full_name
        
        # Delete associated attendance records first (to avoid foreign key constraints)
        AttendanceRecord.query.filter_by(student_id=student_id).delete()
        
        # Now delete the student
        db.session.delete(student)
        db.session.commit()
        
        # Reload known faces in memory to reflect the deletion
        from services.attendance_service import load_known_faces
        load_known_faces()
        
        logger.info(f"Admin user deleted student: {student_name} (ID: {student_id})")
        return jsonify({
            "message": "Student deleted successfully",
            "deleted_student": student_name
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting student with ID {student_id}: {e}")
        return jsonify({"error": "An error occurred while deleting the student."}), 500

# Optional: Keep the manual attendance functionality if needed elsewhere
@admin_bp.route('/admin/manual-attendance', methods=['POST'])
@login_required
@admin_required
def manual_attendance():
    """Manual attendance endpoint (if you want to keep this functionality)."""
    student_id = request.form.get('student_id')
    
    if not student_id:
        flash("No student selected.", "warning")
        return redirect(url_for('admin_api.manage_students'))

    try:
        student = Student.query.get(student_id)
        if student:
            # Create a new attendance record for this student
            new_record = AttendanceRecord(
                student_id=student.id, 
                timestamp=datetime.datetime.utcnow()
            )
            db.session.add(new_record)
            db.session.commit()
            flash(f"Successfully marked {student.full_name} as present.", "success")
        else:
            flash("Student not found.", "error")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error in manual attendance: {e}")
        flash("An error occurred while marking attendance.", "error")
    
    return redirect(url_for('admin_api.manage_students'))