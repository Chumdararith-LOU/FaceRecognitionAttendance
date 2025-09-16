# In find_camera.py (new file)
import cv2

def find_camera_indexes():
    """
    Checks for available camera indexes and displays them.
    Press any key to move to the next camera.
    """
    print("Checking camera indexes... Press any key to cycle through cameras. Press 'q' to quit.")
    index = 0
    while True:
        cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
        if not cap.read()[0]:
            print(f"No camera found at index {index}.")
            break
        
        print(f"Showing camera at index {index}. Is this your physical webcam?")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Display the index on the frame
            cv2.putText(frame, f"Index: {index}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.imshow("Camera Check - Press 'q' to quit, any other key for next camera", frame)
            
            key = cv2.waitKey(1)
            if key != -1: # If any key is pressed
                break
        
        cap.release()
        cv2.destroyAllWindows()

        if key == ord('q'):
            break
            
        index += 1

if __name__ == '__main__':
    find_camera_indexes()