import os
os.environ['LIBGL_ALWAYS_SOFTWARE'] = '1'
os.environ['OPENCV_OPENCL_RUNTIME'] = 'disabled'
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'

import cv2
import numpy as np
from openni import openni2
import sys

# Import MediaPipe Hands để nhận diện bàn tay
from mediapipe.python.solutions import hands as mp_hands
from mediapipe.python.solutions import drawing_utils as mp_drawing

def count_fingers(hand_landmarks):
    """Hàm đếm số ngón tay đang giơ lên"""
    fingers = []
    # Các điểm ngọn ngón tay (Tips) và khớp (MCP) theo chuẩn MediaPipe
    tip_ids = [4, 8, 12, 16, 20]
    mcp_ids = [3, 6, 10, 14, 18]
    
    # Ngón cái (Tính theo trục X để phân biệt trái/phải - Code này làm đơn giản hóa)
    if hand_landmarks.landmark[tip_ids[0]].x < hand_landmarks.landmark[mcp_ids[0]].x:
        fingers.append(1)
    else:
        fingers.append(0)
        
    # 4 ngón còn lại (Tính theo trục Y: ngọn cao hơn khớp là đang giơ lên)
    for id in range(1, 5):
        if hand_landmarks.landmark[tip_ids[id]].y < hand_landmarks.landmark[mcp_ids[id]].y:
            fingers.append(1)
        else:
            fingers.append(0)
            
    return fingers.count(1)

def main():
    openni2_dir = '/home/beniot-phan/APT_AstraProTest/sdk/OpenNI_2.3.0.86_202210111154_4c8f5aa4_beta6_linux/samples/samples/ThirdParty/OpenNI2/linux/x64'
    
    try:
        openni2.initialize(openni2_dir)
    except Exception as e:
        print(f"Lỗi: {e}")
        sys.exit(1)

    # Khởi tạo thuật toán nhận diện bàn tay, chỉ bắt 1 tay để tối ưu Edge Computing
    hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7, max_num_hands=1)

    dev = depth_stream = cap = None
    is_running = True

    try:
        dev = openni2.Device.open_any()
        depth_stream = dev.create_depth_stream()
        depth_stream.start()

        cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        print("Hệ thống Lệnh Cử chỉ 3D đã sẵn sàng! Đưa tay vào màn hình...")

        while is_running:
            ret, color_frame = cap.read() if cap.isOpened() else (False, None)
            
            depth_frame = depth_stream.read_frame()
            depth_data = np.frombuffer(depth_frame.get_buffer_as_uint16(), dtype=np.uint16).copy()
            depth_image = depth_data.reshape(depth_frame.height, depth_frame.width)

            if ret and color_frame is not None:
                color_rgb = cv2.cvtColor(color_frame, cv2.COLOR_BGR2RGB)
                color_rgb = np.ascontiguousarray(color_rgb)
                
                results = hands.process(color_rgb)

                if results.multi_hand_landmarks:
                    for hand_landmarks in results.multi_hand_landmarks:
                        mp_drawing.draw_landmarks(color_frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                        h, w, _ = color_frame.shape
                        # Lấy tọa độ điểm giữa lòng bàn tay (Landmark số 9)
                        cx = int(hand_landmarks.landmark[9].x * w)
                        cy = int(hand_landmarks.landmark[9].y * h)

                        if 0 <= cx < depth_frame.width and 0 <= cy < depth_frame.height:
                            z_mm = depth_image[cy, cx]
                            
                            # KHOANH VÙNG TƯƠNG TÁC (INTERACTION ZONE: < 1500 mm)
                            if 0 < z_mm < 1500:
                                fingers_up = count_fingers(hand_landmarks)
                                command = "CHUA RO LENH"
                                color = (255, 255, 255)

                                if fingers_up == 0:
                                    command = "LENH: NGOI XUONG!"
                                    color = (0, 165, 255)
                                elif fingers_up == 5:
                                    command = "LENH: DUNG LAI!"
                                    color = (0, 0, 255)
                                elif fingers_up == 1 or fingers_up == 2:
                                    command = "LENH: DI TOI!"
                                    color = (0, 255, 0)

                                cv2.putText(color_frame, command, (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 3)
                                cv2.circle(color_frame, (cx, cy), 10, color, cv2.FILLED)
                            elif z_mm >= 1500:
                                cv2.putText(color_frame, "Bypass: Nguoi dung o qua xa", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (100, 100, 100), 2)

                            cv2.putText(color_frame, f"Z: {z_mm} mm", (cx - 50, cy - 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

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