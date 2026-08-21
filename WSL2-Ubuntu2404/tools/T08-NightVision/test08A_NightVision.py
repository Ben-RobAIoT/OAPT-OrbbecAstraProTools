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
from ultralytics import YOLO

def main():
    print("Đang tải AI YOLOv8n (Night Vision Mode)...")
    model = YOLO('yolov8n.pt') 

    print("Đang 'làm nóng' AI...")
    dummy_image = np.zeros((480, 640, 3), dtype=np.uint8)
    model.predict(dummy_image, device='cpu', verbose=False)

    openni2_dir = '/home/beniot-phan/APT_AstraProTest/sdk/OpenNI_2.3.0.86_202210111154_4c8f5aa4_beta6_linux/samples/samples/ThirdParty/OpenNI2/linux/x64'
    try:
        openni2.initialize(openni2_dir)
    except Exception as e:
        print(f"Lỗi: {e}")
        sys.exit(1)

    dev = depth_stream = ir_stream = None
    is_running = True

    try:
        dev = openni2.Device.open_any()
        
        # Bật luồng Depth
        depth_stream = dev.create_depth_stream()
        depth_stream.start()
        
        # Bật luồng IR
        ir_stream = dev.create_ir_stream()
        ir_stream.start()

        # KHÔNG KHỞI TẠO RGB CAPTURE ĐỂ TIẾT KIỆM BĂNG THÔNG

        print("Hệ thống Night Vision sẵn sàng! Hãy tắt đèn để thử nghiệm. Nhấn 'q' để thoát.")

        while is_running:
            # 1. Đọc luồng Depth
            depth_frame = depth_stream.read_frame()
            depth_data = np.frombuffer(depth_frame.get_buffer_as_uint16(), dtype=np.uint16).copy()
            depth_image = depth_data.reshape(depth_frame.height, depth_frame.width)

            # 2. Đọc luồng IR
            ir_frame = ir_stream.read_frame()
            ir_data = np.frombuffer(ir_frame.get_buffer_as_uint16(), dtype=np.uint16).copy()
            ir_image = ir_data.reshape(ir_frame.height, ir_frame.width)

            # 3. Tiền xử lý IR cho YOLO
            # Chuyển IR 16-bit tối thui sang 8-bit sáng rõ (chỉnh alpha để tăng sáng nếu cần)
            ir_8bit = cv2.convertScaleAbs(ir_image, alpha=0.1)
            # "Đánh lừa" YOLO bằng cách biến ảnh xám (1 kênh) thành ảnh màu giả (3 kênh)
            ir_fake_rgb = cv2.cvtColor(ir_8bit, cv2.COLOR_GRAY2BGR)

            # 4. Chạy AI nhận diện Người (class=0) trên ảnh IR
            results = model.predict(ir_fake_rgb, classes=[0], conf=0.4, verbose=False, device='cpu')

            for r in results:
                for box in r.boxes:
                    x1, y1, x2, y2 = box.xyxy[0].int().tolist()
                    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

                    if 0 <= cx < depth_frame.width and 0 <= cy < depth_frame.height:
                        z_mm = depth_image[cy, cx]
                        
                        if z_mm > 0:
                            # Phân tích lệnh hành vi ban đêm
                            warning_text = "NGUOI AN TOAN"
                            box_color = (0, 255, 0)
                            
                            if z_mm < 1000:
                                warning_text = "NGUY HIEM: QUA GAN!"
                                box_color = (0, 0, 255)

                            cv2.rectangle(ir_fake_rgb, (x1, y1), (x2, y2), box_color, 2)
                            cv2.circle(ir_fake_rgb, (cx, cy), 5, (0, 0, 255), -1)
                            cv2.putText(ir_fake_rgb, f"{warning_text}", (x1, y1 - 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, box_color, 2)
                            cv2.putText(ir_fake_rgb, f"Z: {z_mm} mm", (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

            # Hiển thị
            cv2.imshow('IR Night Vision - YOLO', ir_fake_rgb)
            depth_display = cv2.convertScaleAbs(depth_image, alpha=0.03)
            cv2.imshow('Depth Map', cv2.applyColorMap(depth_display, cv2.COLORMAP_JET))

            if cv2.waitKey(1) & 0xFF == ord('q'):
                is_running = False

    except KeyboardInterrupt:
        print("\nĐang đóng an toàn...")
    finally:
        if depth_stream: depth_stream.stop()
        if ir_stream: ir_stream.stop()
        if dev: dev.close()
        openni2.unload()
        cv2.destroyAllWindows()

if __name__ == '__main__':
    main()