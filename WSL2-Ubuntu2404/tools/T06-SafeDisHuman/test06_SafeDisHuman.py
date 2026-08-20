import os
# --- BỘ KHIÊN CHỐNG CRASH BỘ NHỚ TRÊN WSL2 ---
# 1. Tắt hoàn toàn GPU Acceleration của thư viện đồ họa Mesa/OpenGL
os.environ['LIBGL_ALWAYS_SOFTWARE'] = '1'
# 2. Vô hiệu hóa OpenCL của OpenCV
os.environ['OPENCV_OPENCL_RUNTIME'] = 'disabled'
# 3. Ép MediaPipe TFLite dùng 1 luồng để tránh đụng độ
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'
# ---------------------------------------------

import cv2
import numpy as np
from openni import openni2
import sys

# Import trực tiếp để né lỗi Ubuntu 24.04[cite: 1]
from mediapipe.python.solutions import pose as mp_pose
from mediapipe.python.solutions import drawing_utils as mp_drawing

# ... (Phần def main() và vòng lặp while giữ nguyên như cũ nhé) ...
def main():
    openni2_dir = '/home/beniot-phan/APT_AstraProTest/sdk/OpenNI_2.3.0.86_202210111154_4c8f5aa4_beta6_linux/samples/samples/ThirdParty/OpenNI2/linux/x64'
    
    try:
        openni2.initialize(openni2_dir)
    except Exception as e:
        print(f"Lỗi khởi tạo OpenNI2: {e}")
        sys.exit(1)

    pose_tracker = mp_pose.Pose(min_detection_confidence=0.7, min_tracking_confidence=0.7)

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

        print("Hệ thống Human Tracking sẵn sàng! Hãy đứng vào khung hình. Nhấn 'q' để thoát.")

        while is_running:
            ret, color_frame = cap.read() if cap.isOpened() else (False, None)
            
            depth_frame = depth_stream.read_frame()
            
            # 2. THÊM .copy() ĐỂ CÁCH LY BỘ NHỚ, CHỐNG LỖI MALLOC INVALID SIZE
            depth_data = np.frombuffer(depth_frame.get_buffer_as_uint16(), dtype=np.uint16).copy()
            depth_image = depth_data.reshape(depth_frame.height, depth_frame.width)

            if ret and color_frame is not None:
                color_rgb = cv2.cvtColor(color_frame, cv2.COLOR_BGR2RGB)
                
                # 3. Ép ảnh RGB thành chuỗi bộ nhớ liên tục (Bắt buộc cho TFLite)
                color_rgb = np.ascontiguousarray(color_rgb)
                
                # Xử lý Pose
                results = pose_tracker.process(color_rgb)

                if results.pose_landmarks:
                    mp_drawing.draw_landmarks(color_frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

                    h, w, _ = color_frame.shape
                    
                    left_shoulder = results.pose_landmarks.landmark[11]
                    right_shoulder = results.pose_landmarks.landmark[12]
                    
                    cx = int(((left_shoulder.x + right_shoulder.x) / 2) * w)
                    cy = int(((left_shoulder.y + right_shoulder.y) / 2) * h)

                    if 0 <= cx < depth_frame.width and 0 <= cy < depth_frame.height:
                        distance_mm = depth_image[cy, cx]
                        
                        if distance_mm > 0:
                            robot_action = ""
                            action_color = (0, 0, 0)
                            
                            if distance_mm < 1000:       
                                robot_action = "CANH BAO: QUA GAN! (Lui lai)"
                                action_color = (0, 0, 255) 
                            elif distance_mm < 2500:     
                                robot_action = "THEO SAU (Giu toc do do)"
                                action_color = (0, 255, 0) 
                            else:                        
                                robot_action = "TANG TOC! (Da mat dau)"
                                action_color = (0, 255, 255) 

                            cv2.circle(color_frame, (cx, cy), 8, (255, 0, 0), cv2.FILLED)
                            cv2.putText(color_frame, f"Z: {distance_mm} mm", (cx - 50, cy - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
                            cv2.putText(color_frame, f"ROBOT: {robot_action}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, action_color, 2)

                cv2.imshow('Robot Vision - Human Tracking', color_frame)

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
        print("Đã giải phóng tài nguyên!")

if __name__ == '__main__':
    main()