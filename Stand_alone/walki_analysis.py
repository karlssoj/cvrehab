from ultralytics import YOLO
import cv2
import math
import datetime
import os

# Load the pose model
model = YOLO('yolov8n-pose.pt')
cap = cv2.VideoCapture(0)
# Global variable to determine which mode to display
display_mode = "back"  # default mode

# Global dictionaries to store button positions
button_positions = {}  # For mode buttons ("back", "left", "right")
save_button_pos = ()   # For the "Save" button

# Flag to trigger saving
save_triggered = False
measurement_text = ""

def on_mouse(event, x, y, flags, param):
    global display_mode, button_positions, save_button_pos, save_triggered
    if event == cv2.EVENT_LBUTTONDOWN:
        # Check mode buttons first
        for mode, (x1, y1, x2, y2) in button_positions.items():
            if x1 <= x <= x2 and y1 <= y <= y2:
                display_mode = mode
                return
        # Then check if the Save button was clicked
        if save_button_pos:
            sx1, sy1, sx2, sy2 = save_button_pos
            if sx1 <= x <= sx2 and sy1 <= y <= sy2:
                save_triggered = True

def draw_buttons(frame):
    global button_positions, save_button_pos
    # Compute positions relative to frame size for mode buttons (top-right corner)
    frame_w = frame.shape[1]
    margin = 10
    button_width = 100
    button_height = 40
    spacing = 10

    # x coordinates for all mode buttons
    x1 = frame_w - button_width - margin
    x2 = frame_w - margin

    # y coordinates for mode buttons (order: Back, Left, Right from top)
    y1_back = margin
    y2_back = margin + button_height

    y1_left = y2_back + spacing
    y2_left = y1_left + button_height

    y1_right = y2_left + spacing
    y2_right = y1_right + button_height

    button_positions = {
        "back": (x1, y1_back, x2, y2_back),
        "left": (x1, y1_left, x2, y2_left),
        "right": (x1, y1_right, x2, y2_right)
    }

    # Draw mode buttons in desired order
    for mode in ["back", "left", "right"]:
        bx1, by1, bx2, by2 = button_positions[mode]
        cv2.rectangle(frame, (bx1, by1), (bx2, by2), (200, 200, 200), -1)
        cv2.putText(frame, mode.capitalize(), (bx1 + 5, by2 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2, cv2.LINE_AA)

    # Draw Save button in bottom-right corner
    frame_h = frame.shape[0]
    save_margin = 10
    save_button_width = 100
    save_button_height = 40
    sx2 = frame_w - save_margin
    sx1 = frame_w - save_button_width - save_margin
    sy2 = frame_h - save_margin
    sy1 = frame_h - save_button_height - save_margin
    save_button_pos = (sx1, sy1, sx2, sy2)
    cv2.rectangle(frame, (sx1, sy1), (sx2, sy2), (0, 200, 0), -1)
    cv2.putText(frame, "Save", (sx1 + 10, sy2 - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2, cv2.LINE_AA)

def calculate_angle(vertex, point1, point2):
    """
    Calculate the angle (in degrees) at the vertex point.
    """
    v1 = (point1[0] - vertex[0], point1[1] - vertex[1])
    v2 = (point2[0] - vertex[0], point2[1] - vertex[1])
    dot = v1[0] * v2[0] + v1[1] * v2[1]
    mag1 = math.sqrt(v1[0]**2 + v1[1]**2)
    mag2 = math.sqrt(v2[0]**2 + v2[1]**2)
    if mag1 * mag2 == 0:
        return 0
    angle_rad = math.acos(dot / (mag1 * mag2))
    return math.degrees(angle_rad)

def get_slope_angle(point1, point2):
    """
    Returns the absolute deviation from horizontal (in degrees) for the line 
    connecting point1 and point2. If the line is horizontal, returns 0.
    """
    dx = point2[0] - point1[0]
    dy = point2[1] - point1[1]
    angle = abs(math.degrees(math.atan2(dy, dx)))
    if angle > 90:
        angle = 180 - angle
    return angle

def save_measurement(meas_text, original_frame, save_folder="Measurements"):
    # Create folder if it does not exist
    if not os.path.exists(save_folder):
        os.makedirs(save_folder)
    # Generate file name based on current time
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(save_folder, f"Measurement_{timestamp}")
    # Save text file
    with open(filename + ".txt", 'w') as file:
        file.write(meas_text)
    # Save the original frame as JPEG (without drawn annotations)
    cv2.imwrite(filename + ".jpg", original_frame)

# Set the mouse callback for the main window
cv2.namedWindow('Pose Analysis')
cv2.setMouseCallback('Pose Analysis', on_mouse)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # Preserve the original frame (without drawings)
    original_frame = frame.copy()

    # Resize frame and draw a central cross
    frame = cv2.resize(frame, None, fx=1.1, fy=1.1, interpolation=cv2.INTER_NEAREST)
    original_frame = cv2.resize(original_frame, (frame.shape[1], frame.shape[0]),
                                interpolation=cv2.INTER_NEAREST)
    
    # Draw GUI buttons (mode buttons and Save button)
    draw_buttons(frame)

    # Predict using the pose model
    results = model(frame)

    # Initialize variables for display
    hip_slope_angle = None
    left_knee_angle = None
    right_knee_angle = None
    knee_text = ""
    hip_text = ""
    
    # Reset measurement text for saving
    measurement_text = ""

    for r in results:
        keypoints = r.keypoints.xy.int().numpy()

        # Standard indices:
        # 11: left hip, 12: right hip
        # 13: left knee, 14: right knee
        # 15: left ankle, 16: right ankle
        left_hip = keypoints[0][11]
        right_hip = keypoints[0][12]
        left_knee = keypoints[0][13]
        right_knee = keypoints[0][14]
        left_ankle = keypoints[0][15]
        right_ankle = keypoints[0][16]

        if display_mode == "back":
            # Draw left leg if complete
            if left_hip[0] != 0 and left_knee[0] != 0 and left_ankle[0] != 0:
                cv2.circle(frame, tuple(left_hip), 5, (0, 255, 0), -1)
                cv2.circle(frame, tuple(left_knee), 5, (255, 0, 0), -1)
                cv2.circle(frame, tuple(left_ankle), 5, (0, 0, 255), -1)
                cv2.line(frame, tuple(left_hip), tuple(left_knee), (255, 0, 0), 3)
                cv2.line(frame, tuple(left_knee), tuple(left_ankle), (255, 0, 0), 3)
                # Compute modified knee angle (0 when leg is straight, 180 when fully bent)
                left_knee_angle = 180 - calculate_angle(tuple(left_knee), tuple(left_hip), tuple(left_ankle))
            # Draw right leg if complete
            if right_hip[0] != 0 and right_knee[0] != 0 and right_ankle[0] != 0:
                cv2.circle(frame, tuple(right_hip), 5, (0, 255, 0), -1)
                cv2.circle(frame, tuple(right_knee), 5, (255, 0, 0), -1)
                cv2.circle(frame, tuple(right_ankle), 5, (0, 0, 255), -1)
                cv2.line(frame, tuple(right_hip), tuple(right_knee), (255, 0, 0), 3)
                cv2.line(frame, tuple(right_knee), tuple(right_ankle), (255, 0, 0), 3)
                right_knee_angle = 180 - calculate_angle(tuple(right_knee), tuple(right_hip), tuple(right_ankle))
            # Draw hip line and compute slope only if all joints are visible
            if (left_hip[0] != 0 and right_hip[0] != 0 and 
                left_knee[0] != 0 and right_knee[0] != 0 and 
                left_ankle[0] != 0 and right_ankle[0] != 0):
                cv2.line(frame, tuple(left_hip), tuple(right_hip), (0, 255, 0), 3)
                hip_slope_angle = get_slope_angle(tuple(left_hip), tuple(right_hip))
            # Prepare measurement text (do not display knee angle in "back" mode)
            if hip_slope_angle is not None:
                hip_text = f"Hip line slope: {hip_slope_angle:.1f}°"
            measurement_text = hip_text

        elif display_mode == "left":
            # Only display left side joints and compute left knee angle
            if left_hip[0] != 0 and left_knee[0] != 0 and left_ankle[0] != 0:
                cv2.circle(frame, tuple(left_hip), 5, (0, 255, 0), -1)
                cv2.circle(frame, tuple(left_knee), 5, (255, 0, 0), -1)
                cv2.circle(frame, tuple(left_ankle), 5, (0, 0, 255), -1)
                cv2.line(frame, tuple(left_hip), tuple(left_knee), (255, 0, 0), 3)
                cv2.line(frame, tuple(left_knee), tuple(left_ankle), (255, 0, 0), 3)
                left_knee_angle = 180 - calculate_angle(tuple(left_knee), tuple(left_hip), tuple(left_ankle))
                knee_text = f"Left knee angle: {left_knee_angle:.1f}°"
                measurement_text = knee_text
        elif display_mode == "right":
            # Only display right side joints and compute right knee angle
            if right_hip[0] != 0 and right_knee[0] != 0 and right_ankle[0] != 0:
                cv2.circle(frame, tuple(right_hip), 5, (0, 255, 0), -1)
                cv2.circle(frame, tuple(right_knee), 5, (255, 0, 0), -1)
                cv2.circle(frame, tuple(right_ankle), 5, (0, 0, 255), -1)
                cv2.line(frame, tuple(right_hip), tuple(right_knee), (255, 0, 0), 3)
                cv2.line(frame, tuple(right_knee), tuple(right_ankle), (255, 0, 0), 3)
                right_knee_angle = 180 - calculate_angle(tuple(right_knee), tuple(right_hip), tuple(right_ankle))
                knee_text = f"Right knee angle: {right_knee_angle:.1f}°"
                measurement_text = knee_text

    # Display text on the frame (mode is shown for all modes)
    mode_text = f"Mode: {display_mode.capitalize()}"
    cv2.putText(frame, mode_text, (50, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,0), 2, cv2.LINE_AA)
    if display_mode == "back":
        if hip_text:
            cv2.putText(frame, hip_text, (50, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2, cv2.LINE_AA)
    else:
        if knee_text:
            cv2.putText(frame, knee_text, (50, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2, cv2.LINE_AA)

    cv2.imshow('Pose Analysis', frame)
    key = cv2.waitKey(1)
    if key == 27:  # ESC to exit
        break
    if key == 13:  # Also allow Enter key to trigger saving
        save_triggered = True

    if save_triggered:
        # Save measurements and original image
        save_measurement(measurement_text, original_frame)
        save_triggered = False  # Reset trigger

cap.release()
cv2.destroyAllWindows()
