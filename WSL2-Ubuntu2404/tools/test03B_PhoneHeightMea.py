import os
# Ép PyTorch chỉ dùng 1-2 luồng CPU để tránh lỗi Deadlock trên WSL2
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'

import cv2
import numpy as np
from openni import openni2
import sys
from ultralytics import YOLO


# Cấu hình Calib
FOCAL_LENGTH_Y = 444.06

def main():
    # Load mô hình YOLOv8 Nano (lần đầu chạy sẽ tự động tải file yolov8n.pt khoảng 6MB)
    print("Đang tải mô hình AI...")
    model = YOLO('yolov8n.pt') 

    # --- BƯỚC WARM-UP QUAN TRỌNG ---
    print("Đang 'làm nóng' AI (Warm-up)... Khúc này có thể mất 5-10 giây...")
    dummy_image = np.zeros((480, 640, 3), dtype=np.uint8)
    model.predict(dummy_image, device='cpu', verbose=False)
    print("AI đã khởi động xong! Chuẩn bị mở Camera...")
    # -------------------------------
    
    openni2_dir = '/home/beniot-phan/APT_AstraProTest/sdk/OpenNI_2.3.0.86_202210111154_4c8f5aa4_beta6_linux/samples/samples/ThirdParty/OpenNI2/linux/x64'
    
    try:
        openni2.initialize(openni2_dir)
    except Exception as e:
        print(f"Lỗi khởi tạo OpenNI2: {e}")
        sys.exit(1)

    dev = None
    depth_stream = None
    cap = None
    
    # Dùng cờ này để quản lý luồng, tránh lỗi Core Dump khi Ctrl+C
    is_running = True 

    try:
        dev = openni2.Device.open_any()
        depth_stream = dev.create_depth_stream()
        depth_stream.start()

        cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        print("Hệ thống sẵn sàng! Đưa điện thoại vào camera. Nhấn 'q' để thoát.")

        while is_running:
            # 1. Kiểm tra luồng RGB
            print("1. Đang đọc RGB...") # Bỏ comment nếu muốn kiểm tra chi tiết
            ret, color_frame = cap.read() if cap.isOpened() else (False, None)

            # 2. Kiểm tra luồng Depth
            print("2. Đang đọc Depth...") # Bỏ comment nếu muốn kiểm tra chi tiết
            depth_frame = depth_stream.read_frame()
            depth_data = np.frombuffer(depth_frame.get_buffer_as_uint16(), dtype=np.uint16)
            depth_image = depth_data.reshape(depth_frame.height, depth_frame.width)

            if ret and color_frame is not None:
                # 3. Kiểm tra YOLO
                print("3. Đang chạy YOLO...") # Bỏ comment nếu muốn kiểm tra chi tiết
                
                # ÉP CHẠY BẰNG CPU ĐỂ TRÁNH LỖI WSL2 CUDA
                results = model.predict(color_frame, classes=[67], conf=0.5, verbose=False, device='cpu')
                
                for r in results:
                    boxes = r.boxes
                    for box in boxes:
                        x1, y1, x2, y2 = box.xyxy[0].int().tolist()
                        h_pixel = y2 - y1
                        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                        
                        if 0 <= cx < depth_frame.width and 0 <= cy < depth_frame.height:
                            z_mm = float(depth_image[cy, cx])
                            if z_mm > 0:
                                real_height_mm = (float(h_pixel) * z_mm) / FOCAL_LENGTH_Y
                                cv2.rectangle(color_frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
                                cv2.circle(color_frame, (cx, cy), 5, (0, 0, 255), -1)
                                cv2.putText(color_frame, f"Z: {z_mm:.0f} mm", (x1, y1 - 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                                cv2.putText(color_frame, f"Cao: {real_height_mm:.1f} mm", (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

                cv2.imshow('YOLO Phone Measure', color_frame)
            else:
                print("Lỗi: Không thể đọc được frame RGB!")

            depth_display = cv2.convertScaleAbs(depth_image, alpha=0.03)
            cv2.imshow('Depth Map', cv2.applyColorMap(depth_display, cv2.COLORMAP_JET))

            if cv2.waitKey(1) & 0xFF == ord('q'):
                is_running = False

    except KeyboardInterrupt:
        print("\n[Cảnh báo] Đã nhận lệnh ngắt (Ctrl+C). Bắt đầu quy trình đóng an toàn...")
    except Exception as e:
        print(f"Lỗi Runtime: {e}")
    finally:
        print("Đang giải phóng toàn bộ tài nguyên...")
        # Quy trình đóng chuẩn không gây invalid pointer
        if cap: cap.release()
        if depth_stream: depth_stream.stop()
        if dev: dev.close()
        openni2.unload()
        cv2.destroyAllWindows()
        print("Đã dọn dẹp xong. Không bị rò rỉ bộ nhớ!")

if __name__ == '__main__':
    main()