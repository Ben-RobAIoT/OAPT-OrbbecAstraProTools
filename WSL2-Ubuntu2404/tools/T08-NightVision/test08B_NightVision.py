import os
# --- BỘ KHIÊN CHỐNG CRASH BỘ NHỚ TRÊN WSL2 ---
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

# --- THÔNG SỐ CAMERA INTRINSICS (Orbbec Astra Pro) ---
FX, FY = 570.3, 570.3
CX, CY = 320.0, 240.0

def draw_radar_map(x_mm, z_mm):
    """Vẽ bản đồ Radar 2D (Góc nhìn từ trên cao)"""
    # Tạo bản đồ nền đen kích thước 500x500 pixel
    map_size = 500
    radar_map = np.zeros((map_size, map_size, 3), dtype=np.uint8)
    
    # Vẽ các đường lưới Grid (Mỗi ô tương đương 1 mét = 1000mm)
    for i in range(0, map_size, 100):
        cv2.line(radar_map, (0, i), (map_size, i), (50, 50, 50), 1)
        cv2.line(radar_map, (i, 0), (i, map_size), (50, 50, 50), 1)

    # Tọa độ Camera (Nằm ở cạnh dưới cùng, giữa bản đồ)
    cam_x, cam_y = map_size // 2, map_size - 20
    cv2.circle(radar_map, (cam_x, cam_y), 8, (255, 255, 255), -1)
    cv2.putText(radar_map, "ROBOT", (cam_x - 25, cam_y - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    # Tỷ lệ chuyển đổi: 500 pixel đại diện cho 5000mm (5 mét) -> 1 pixel = 10mm
    scale = 0.1 

    if z_mm > 0:
        # Tính toán tọa độ trên bản đồ
        map_target_x = int(cam_x + (x_mm * scale))
        map_target_y = int(cam_y - (z_mm * scale))

        # Giới hạn điểm vẽ không bị văng ra khỏi cửa sổ màn hình
        map_target_x = max(0, min(map_size, map_target_x))
        map_target_y = max(0, min(map_size, map_target_y))

        # Vẽ đường nối tia laze từ Robot tới Nạn nhân
        cv2.line(radar_map, (cam_x, cam_y), (map_target_x, map_target_y), (0, 100, 0), 1, cv2.LINE_AA)
        
        # Vẽ vị trí Nạn nhân (Chấm đỏ)
        cv2.circle(radar_map, (map_target_x, map_target_y), 6, (0, 0, 255), -1)
        
        # Hiển thị thông số không gian
        info_text = f"X:{int(x_mm)}mm, Z:{int(z_mm)}mm"
        cv2.putText(radar_map, info_text, (map_target_x + 10, map_target_y), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)

    return radar_map

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
        depth_stream = dev.create_depth_stream()
        depth_stream.start()
        
        ir_stream = dev.create_ir_stream()
        ir_stream.start()

        print("Hệ thống SAR Radar (Night Vision) sẵn sàng! Tắt đèn và đi quanh phòng.")
        print("Nhấn 'q' trên cửa sổ bất kỳ để thoát.")

        while is_running:
            depth_frame = depth_stream.read_frame()
            depth_data = np.frombuffer(depth_frame.get_buffer_as_uint16(), dtype=np.uint16).copy()
            depth_image = depth_data.reshape(depth_frame.height, depth_frame.width)

            ir_frame = ir_stream.read_frame()
            ir_data = np.frombuffer(ir_frame.get_buffer_as_uint16(), dtype=np.uint16).copy()
            ir_image = ir_data.reshape(ir_frame.height, ir_frame.width)

            ir_8bit = cv2.convertScaleAbs(ir_image, alpha=0.1)
            ir_fake_rgb = cv2.cvtColor(ir_8bit, cv2.COLOR_GRAY2BGR)

            # Bản đồ rỗng (Phòng trường hợp không thấy ai)
            radar_map_display = draw_radar_map(0, 0)
            
            results = model.predict(ir_fake_rgb, classes=[0], conf=0.4, verbose=False, device='cpu')

            for r in results:
                for box in r.boxes:
                    x1, y1, x2, y2 = box.xyxy[0].int().tolist()
                    # Tọa độ tâm u, v trên ảnh
                    u, v = (x1 + x2) // 2, (y1 + y2) // 2

                    if 0 <= u < depth_frame.width and 0 <= v < depth_frame.height:
                        z_mm = depth_image[v, u]
                        
                        if z_mm > 0:
                            # TÍNH TOÁN TỌA ĐỘ 3D THỰC TẾ
                            x_mm = ((u - CX) * z_mm) / FX
                            
                            # Cập nhật Radar Map
                            radar_map_display = draw_radar_map(x_mm, z_mm)

                            # Vẽ GUI lên màn hình IR
                            warning_text = f"TARGET LOCKED: Z={int(z_mm)}mm"
                            box_color = (0, 0, 255) if z_mm < 1500 else (0, 255, 0)
                            
                            cv2.rectangle(ir_fake_rgb, (x1, y1), (x2, y2), box_color, 2)
                            cv2.circle(ir_fake_rgb, (u, v), 5, (0, 0, 255), -1)
                            cv2.putText(ir_fake_rgb, warning_text, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, box_color, 2)

            # Hiển thị 3 màn hình
            cv2.imshow('1. IR Camera (YOLO)', ir_fake_rgb)
            cv2.imshow('2. 2D Radar Map', radar_map_display)
            
            depth_display = cv2.convertScaleAbs(depth_image, alpha=0.03)
            cv2.imshow('3. Depth Map', cv2.applyColorMap(depth_display, cv2.COLORMAP_JET))

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