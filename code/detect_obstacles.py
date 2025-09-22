import cv2
import numpy as np
import time
from pymavlink import mavutil
import tflite_runtime.interpreter as tflite

# --- 1. INITIALIZATION AND SETUP ---

# --- MAVLink Connection ---
# Connect to the Pixhawk flight controller on the Raspberry Pi's serial port
# Use '/dev/serial0' for GPIO UART pins
# Baud rate must match the Pixhawk's setting (e.g., 921600)
try:
    master = mavutil.mavlink_connection('/dev/serial0', baud=921600)
    # Wait for a heartbeat from the Pixhawk to confirm the connection
    master.wait_heartbeat(timeout=5)
    print("Heartbeat from Pixhawk received! MAVLink connection established.")
except Exception as e:
    print(f"Error connecting to Pixhawk: {e}")
    print("Please check the serial port, baud rate, and physical connection.")
    exit()

# --- Model and Camera Setup ---
# Define the paths to your model and labels files
model_path = 'model.tflite'
labels_path = 'labels.txt'

# Load the TFLite model and allocate tensors.
try:
    interpreter = tflite.Interpreter(model_path=model_path)
    interpreter.allocate_tensors()
except Exception as e:
    print(f"Error loading TFLite model: {e}")
    exit()

# Get model input and output details
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()
height = input_details[0]['shape'][1]
width = input_details[0]['shape'][2]

# Load the labels
with open(labels_path, 'r') as f:
    labels = [line.strip() for line in f.readlines()]

# Initialize the camera
# Use 0 for the default camera (e.g., Pi Camera or first USB webcam)
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Could not open camera.")
    exit()

# --- 2. OBSTACLE AVOIDANCE FUNCTION ---
def send_obstacle_distance_message(distance_cm, angle_deg=0):
    """
    Sends a MAVLink DISTANCE_SENSOR message to the Pixhawk.
    ArduPilot's proximity feature will then use this to avoid obstacles.
    """
    # Angle 0 is straight ahead
    orientation = mavutil.mavlink.MAV_SENSOR_ROTATION_NONE
    master.mav.distance_sensor_send(
        0,              # time_boot_ms (0 for unknown)
        50,             # min_distance cm (vehicle will stop this far from obstacle)
        1000,           # max_distance cm (max range of our "sensor")
        distance_cm,    # current_distance in cm
        0,              # type (0=Laser, 4=MAVLink)
        24,             # id (a unique sensor ID)
        orientation,    # orientation
        255             # covariance (255 for unknown)
    )
    print(f"Sent DISTANCE_SENSOR message: Obstacle at {distance_cm} cm")

# --- 3. MAIN DETECTION LOOP ---
try:
    while True:
        # Capture frame-by-frame
        ret, frame = cap.read()
        if not ret:
            break

        # Prepare image for AI model
        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        imH, imW, _ = frame.shape
        image_resized = cv2.resize(image_rgb, (width, height))
        input_data = np.expand_dims(image_resized, axis=0)

        # Run object detection
        interpreter.set_tensor(input_details[0]['index'], input_data)
        interpreter.invoke()

        # Extract detection results
        boxes = interpreter.get_tensor(output_details[1]['index'])[0] # Bounding box coordinates
        classes = interpreter.get_tensor(output_details[3]['index'])[0] # Class index
        scores = interpreter.get_tensor(output_details[0]['index'])[0] # Confidence scores

        obstacle_detected = False
        
        # --- 4. DECISION LOGIC ---
        for i in range(len(scores)):
            # Check for high-confidence detections
            if scores[i] > 0.6:
                # Get bounding box coordinates and draw box
                ymin = int(max(1, boxes[i][0] * imH))
                xmin = int(max(1, boxes[i][1] * imW))
                ymax = int(min(imH, boxes[i][2] * imH))
                xmax = int(min(imW, boxes[i][3] * imW))
                
                cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), (10, 255, 0), 2)

                # --- Core Avoidance Logic ---
                # Calculate the area of the bounding box as a proxy for proximity
                box_area = (xmax - xmin) * (ymax - ymin)
                
                # If the box area is large (e.g., > 20% of screen), the obstacle is close
                if box_area > (imW * imH * 0.20):
                    obstacle_detected = True
                    # A simple mapping: larger area means smaller distance
                    # This requires tuning for your specific camera/setup!
                    estimated_distance_cm = int(100) # Send a "close" signal
                    send_obstacle_distance_message(estimated_distance_cm)
                    
                    # Stop after the first significant obstacle to avoid spamming messages
                    break

        # If no significant obstacles were detected, send a "clear" message (max range)
        if not obstacle_detected:
            send_obstacle_distance_message(1000)

        # Display the resulting frame (optional, for debugging)
        cv2.imshow('Drone View', frame)
        
        # Small delay to control the message rate
        time.sleep(0.1)

        # Press 'q' to quit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    # Clean up resources
    cap.release()
    cv2.destroyAllWindows()
    print("Script terminated. Camera and windows closed.")
