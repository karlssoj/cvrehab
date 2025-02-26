from ultralytics import YOLO
import cv2
import math
import datetime
import base64
import numpy as np
model = YOLO('yolov8n-pose.pt')  # load an official model

def analyze_frame(frame, shoulder, measuring):
    try:
        #measuring = False
        left = False
        if shoulder == 'left':
            left = True

        def get_vertical_point(frame, shoulder_point):
            vertical_point = [shoulder_point[0], frame.shape[0]]
            return vertical_point


        def get_mid_points(left_shoulder, right_shoulder, left_hip, right_hip):

            if (left_shoulder[0] == 0 or  right_shoulder[0] == 0 or left_hip[0] == 0 or right_hip[0] == 0):
                return [-1, -1], [-1, -1]
            
            ux = int((left_shoulder[0] + right_shoulder[0]) / 2)
            uy = int((left_shoulder[1] + right_shoulder[1]) / 2)
            shoulderMidPoint = [ux, uy]

            dx = int((left_hip[0] + right_hip[0]) / 2)
            dy = int((left_hip[1] + right_hip[1]) / 2)
            hipMidPoint = [dx, dy]

            return shoulderMidPoint, hipMidPoint


        def calculate_angle(line1_start, line1_end, line2_start, line2_end):
            # Calculate the direction vectors of the lines
            vector1 = (line1_end[0] - line1_start[0], line1_end[1] - line1_start[1])
            vector2 = (line2_end[0] - line2_start[0], line2_end[1] - line2_start[1])

            # Calculate the dot product and the cross product of the vectors
            dot_product = vector1[0] * vector2[0] + vector1[1] * vector2[1]
            cross_product = vector1[0] * vector2[1] - vector1[1] * vector2[0]

            # Calculate the angle in radians
            angle_radians = math.atan2(cross_product, dot_product)

            # Convert the angle to degrees
            angle_degrees = math.degrees(angle_radians)

            # Ensure the angle is positive
            if angle_degrees < 0:
                angle_degrees += 360

            return abs(angle_degrees - 180)


        def get_distance(pos1, pos2):
            dist = math.sqrt( (pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2)
            return dist


        '''def choose_side(frame, left_wrist, right_wrist):
            global left

            left_button_pos = [frame.shape[1] - 50, frame.shape[0] - 50]
            right_button_pos = [50, frame.shape[0] - 50]
            
            cv2.circle(frame, left_button_pos, 40, (255, 255, 255), 3)
            cv2.circle(frame, right_button_pos, 40, (255, 255, 255), 3)

            if get_distance(left_wrist, left_button_pos) < 100:
                left = True

            if get_distance(right_wrist, right_button_pos) < 100:
                left = False'''

        def save_value(value, path):
            #timestamp = datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")
            #save_data = timestamp + ': ' + value + '\n'
            shoulder_string = shoulder_string + str(int(angle))+' degrees'
            with open(path, 'a') as file:
                file.write(shoulder_string)

        def draw_cross(image, center, arm_length, color=(255, 255, 255), thickness=1):

            # Convert center point to integers
            center = tuple(map(int, center))

            # Draw horizontal line
            cv2.line(image, (center[0] - arm_length, center[1]), (center[0] + arm_length, center[1]), color, thickness)

            # Draw vertical line
            cv2.line(image, (center[0], center[1] - arm_length), (center[0], center[1] + arm_length), color, thickness)


        def draw_and_calculate(frame, hip, shoulder, elbow, wrist, shoulderMidPoint, hipMidPoint):
            #global measuring
            global angle
            upper_point = [0, 0]
            lower_point = [0, 0]

            
            if shoulderMidPoint[0] == -1 or hipMidPoint[0] == -1:
                upper_point = shoulder
                lower_point = hip

            else:
                upper_point = shoulderMidPoint
                lower_point = hipMidPoint
            
            if elbow[0] != 0 and wrist[0] != 0 and shoulder[0] != 0 and hip[0] != 0:
                cv2.line(frame, shoulder, elbow, (255, 0, 0), 3)
                cv2.line(frame, wrist, elbow, (255, 0, 0), 3)
                        
                cv2.circle(frame, elbow, 3, (0, 0, 0), 3)
                cv2.circle(frame, shoulder, 3, (0, 0, 0), 3)
                cv2.circle(frame, wrist, 2, (255, 0, 0), 3)

                cv2.circle(frame, upper_point, 2, (255, 255, 255), 3)  
                cv2.circle(frame, lower_point, 2, (255, 255, 255), 3) 
                cv2.line(frame, upper_point, lower_point, (255, 255, 255), 3)

                angle = calculate_angle(elbow, shoulder, upper_point, lower_point)                

                #measuring = True    

            return angle

        def save_value(value, path):
            timestamp = datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")
            #save_data = timestamp + ': ' + value + '\n'
            save_data = value + '\n'

            with open(path, 'a') as file:
                file.write(save_data)
            #measuring_state = False

        #while cap.isOpened():
        #ret, frame = cap.read()

        #measuring = True
        
        '''if not ret:
            break'''

        #frame = cv2.resize(frame, None, fx=1.6, fy=1.6, interpolation = cv2.INTER_NEAREST)

        draw_cross(frame, [frame.shape[1]/2, frame.shape[0]/2], 100)
        
        # Predict with the model
        results = model(frame)  # predict on an image
        
        
        for r in results:
            keypoints = r.keypoints.xy.int().numpy()
            left_shoulder = keypoints[0][5]
            right_shoulder = keypoints[0][6]
            left_elbow = keypoints[0][7]
            right_elbow = keypoints[0][8]
            left_wrist = keypoints[0][9]
            right_wrist = keypoints[0][10]
            left_hip = keypoints[0][11]
            right_hip = keypoints[0][12]

            angle = 0
            
            #choose_side(frame, left_wrist, right_wrist)

            shoulderMidPoint, hipMidPoint = get_mid_points(left_shoulder, right_shoulder, left_hip, right_hip)
            
            if left == True:
                if left_elbow[0] != 0 and left_wrist[0] != 0 and left_shoulder[0] != 0:
                    angle = draw_and_calculate(frame, left_hip, left_shoulder, left_elbow, left_wrist, shoulderMidPoint, hipMidPoint)

            if left == False:
                if right_elbow[0] != 0 and right_wrist[0] != 0 and right_shoulder[0] != 0:
                    angle = draw_and_calculate(frame, right_hip, right_shoulder, right_elbow, right_wrist, shoulderMidPoint, hipMidPoint)

        shoulder_string = ''
        
        
        if left == True:
            shoulder_string = 'Left shoulder angle = '
        
        if left == False:
            shoulder_string = 'Right shoulder angle = '

        shoulder_string = shoulder_string + str(int(angle))+' degrees'
        cv2.putText(frame, shoulder_string, (100, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2, cv2.LINE_AA)    
        
        

        #key = cv2.waitKey(1)
        
        if measuring:
            save_value(shoulder_string, './Measurements.txt')
            
        #result = shoulder_string + '\n'
        return frame
    except Exception as e:
        print('Something went wrong with the object detection: ', e)
        # Sends frame unprocessed if no angle could be detected to avoid interruptions on output stream
        return frame


