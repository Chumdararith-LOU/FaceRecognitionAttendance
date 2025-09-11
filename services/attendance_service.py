import cv2
import face_recognition

def process_video_frame(frame):
    """
    Detects faces in a single video frame and draws rectangles around them.
    """
    # Find all face locations in the current frame
    face_locations = face_recognition.face_locations(frame)

    # Draw a rectangle around each detected face
    for top, right, bottom, left in face_locations:
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
    
    return frame