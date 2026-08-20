# main_robot_vision.py

import os
# Khiên chống Crash cho WSL2
os.environ['LIBGL_ALWAYS_SOFTWARE'] = '1'
os.environ['OPENCV_OPENCL_RUNTIME'] = 'disabled'
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'

import cv2
import numpy as np
from openni import openni2
import sys

from mediapipe.python.solutions import hands as mp_hands
from mediapipe.python.solutions import drawing_utils as mp_drawing

# --- IMPORT DATASET CỬ CHỈ ---
from ds_gesture_dataset import ROBOT_GESTURES

def get_finger_states(hand_landmarks, hand_label):
    """Phân tích bàn tay thành mảng [Cái, Trỏ, Giữa, Áp út, Út] (1=Mở, 0=Gập)"""
    fingers = []
    tip_ids = [4, 8, 12, 16, 20]
    mcp_ids = [3, 6, 10, 14, 18]
    
    # 1. Ngón cái (Phụ thuộc vào tay Trái/Phải để so sánh trục X)
    # MediaPipe camera selfie thường bị ngược gương, nên "Left" của MP là tay Phải của bạn
    if hand_label == "Left": 
        fingers.append(1 if hand_landmarks.landmark[tip_ids[0]].x > hand_landmarks.landmark[mcp_ids[0]].x else 0)
    else:
        fingers.append(1 if hand_landmarks.landmark[tip_ids[0]].x < hand_landmarks.landmark[mcp_ids[0]].x else 0)
        
    # 2. Bốn ngón còn lại (So sánh trục Y)
    for id in range(1, 5):
        fingers.append(1 if hand_landmarks.landmark[tip_ids[id]].y < hand_landmarks.landmark[mcp_ids[id]].y else 0)
            
    return fingers

def match_gesture(current_left, current_right):
    """Khớp trạng thái tay hiện tại với Dataset"""
    for gesture_name, config in ROBOT_GESTURES.items():
        match = True
        # Kiểm tra tay trái
        for i in range(5):
            if config["left"][i] != -1 and config["left"][i] != current_left[i]:
                match = False
                break
        # Kiểm tra tay phải
        for i in range(5):
            if match and config["right"][i] != -1 and config["right"][i] != current_right[i]:
                match = False
                break
        
        if match:
            return gesture_name, config["color"]
            
    return "KHONG XAC DINH", (150, 150, 150)

def main():
    openni2_dir = '/home/beniot-phan/APT_AstraProTest/sdk/OpenNI_2.3.0.86_202210111154_4c8f5aa4_beta6_linux/samples/samples/ThirdParty/OpenNI2/linux/x64'
    try:
        openni2.initialize(openni2_dir)
    except Exception as e:
        print(f"Lỗi: {e}")
        sys.exit(1)

    # Nâng max_num_hands lên 2 để nhận diện 2 tay
    hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7, max_num_hands=2)

    dev = openni2.Device.open_any()
    depth_stream = dev.create_depth_stream()
    depth_stream.start()

    cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    is_running = True
    print("Hệ thống Đa cử chỉ 2 tay đã sẵn sàng! Đưa tay vào vùng < 1.5m...")

    try:
        while is_running:
            ret, color_frame = cap.read() if cap.isOpened() else (False, None)
            
            depth_frame = depth_stream.read_frame()
            depth_data = np.frombuffer(depth_frame.get_buffer_as_uint16(), dtype=np.uint16).copy()
            depth_image = depth_data.reshape(depth_frame.height, depth_frame.width)

            if ret and color_frame is not None:
                color_rgb = np.ascontiguousarray(cv2.cvtColor(color_frame, cv2.COLOR_BGR2RGB))
                results = hands.process(color_rgb)

                # Mặc định: [-1,-1,-1,-1,-1] nghĩa là không thấy tay
                state_left = [-1, -1, -1, -1, -1]
                state_right = [-1, -1, -1, -1, -1]
                min_z_mm = 9999 # Tìm khoảng cách tay gần nhất
                center_x, center_y = 0, 0

                if results.multi_hand_landmarks:
                    h, w, _ = color_frame.shape
                    
                    for idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
                        mp_drawing.draw_landmarks(color_frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                        
                        # Xác định tay Trái/Phải từ MediaPipe
                        hand_label = results.multi_handedness[idx].classification[0].label
                        fingers = get_finger_states(hand_landmarks, hand_label)
                        
                        if hand_label == "Left":
                            state_left = fingers
                        else:
                            state_right = fingers

                        # Lấy Z tại lòng bàn tay để kiểm tra Interaction Zone
                        cx = int(hand_landmarks.landmark[9].x * w)
                        cy = int(hand_landmarks.landmark[9].y * h)
                        if 0 <= cx < depth_frame.width and 0 <= cy < depth_frame.height:
                            z = depth_image[cy, cx]
                            if 0 < z < min_z_mm:
                                min_z_mm = z
                                center_x, center_y = cx, cy

                # Quyết định hành động dựa trên 2 tay & Depth
                if min_z_mm < 1500:
                    command, color = match_gesture(state_left, state_right)
                    cv2.putText(color_frame, f"Lenh: {command}", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 3)
                    if center_x != 0:
                        cv2.circle(color_frame, (center_x, center_y), 15, color, cv2.FILLED)
                elif min_z_mm != 9999:
                    cv2.putText(color_frame, f"Nguoi qua xa ({min_z_mm}mm)", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (100,100,100), 2)

                cv2.imshow('Robot Command Vision', color_frame)

            depth_display = cv2.convertScaleAbs(depth_image, alpha=0.03)
            cv2.imshow('Depth Map', cv2.applyColorMap(depth_display, cv2.COLORMAP_JET))

            if cv2.waitKey(1) & 0xFF == ord('q'):
                is_running = False

    except KeyboardInterrupt:
        print("\nĐang đóng an toàn...")
    finally:
        if cap: cap.release()
        if depth_stream: depth_stream.stop()
        if dev: dev.close()
        openni2.unload()
        cv2.destroyAllWindows()

if __name__ == '__main__':
    main()