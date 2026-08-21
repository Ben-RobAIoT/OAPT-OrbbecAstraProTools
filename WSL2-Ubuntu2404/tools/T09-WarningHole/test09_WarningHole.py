import os
# Bộ khiên chống Crash bộ nhớ đồ họa trên máy ảo WSL2[cite: 6]
os.environ['LIBGL_ALWAYS_SOFTWARE'] = '1'
os.environ['OPENCV_OPENCL_RUNTIME'] = 'disabled'
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'


import cv2
import numpy as np
from openni import openni2
import sys

# --- CẤU HÌNH VÙNG QUÉT (ROI) DƯỚI CHÂN ROBOT ---
# Khung hình chuẩn: 640 (rộng) x 480 (cao)
ROI_X1, ROI_X2 = 220, 420  # Quét một dải rộng 200 pixel ở giữa
ROI_Y1, ROI_Y2 = 380, 480  # Quét 100 pixel ở sát mép dưới màn hình (ngay trước chân chó)

# Nếu độ sâu lớn hơn mức này (hoặc bằng 0), xác định là hố sâu
SAFE_GROUND_MAX_MM = 1200  
DANGER_RATIO = 0.4         # Nếu 40% diện tích ROI là hố sâu -> Báo động

def main():
    openni2_dir = '/home/beniot-phan/APT_AstraProTest/sdk/OpenNI_2.3.0.86_202210111154_4c8f5aa4_beta6_linux/samples/samples/ThirdParty/OpenNI2/linux/x64'
    
    try:
        openni2.initialize(openni2_dir)
    except Exception as e:
        print(f"Lỗi khởi tạo: {e}")
        sys.exit(1)

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

        print("Hệ thống Chống rơi ngã (Cliff Detection) sẵn sàng!")
        print("Hãy thử đưa camera ra mép bàn hoặc cầu thang đi xuống. Nhấn 'q' để thoát.")

        while is_running:
            ret, color_frame = cap.read() if cap.isOpened() else (False, None)
            
            depth_frame = depth_stream.read_frame()
            depth_data = np.frombuffer(depth_frame.get_buffer_as_uint16(), dtype=np.uint16).copy()
            depth_image = depth_data.reshape(depth_frame.height, depth_frame.width)

            # --- THUẬT TOÁN PHÂN TÍCH VỰC SÂU ---
            # Trích xuất dữ liệu độ sâu trong vùng quét
            roi_depth = depth_image[ROI_Y1:ROI_Y2, ROI_X1:ROI_X2]
            total_pixels = roi_depth.size
            
            # Đếm số lượng pixel báo nguy hiểm (Z > 1200mm HOẶC Z == 0)
            danger_pixels = np.sum((roi_depth > SAFE_GROUND_MAX_MM) | (roi_depth == 0))
            
            # Tính tỷ lệ nguy hiểm
            danger_percent = danger_pixels / total_pixels
            
            if ret and color_frame is not None:
                # Giao diện mặc định (An toàn)
                box_color = (0, 255, 0)
                status_text = "AN TOAN: Mat san phang"
                
                # Kích hoạt báo động nếu vượt ngưỡng
                if danger_percent > DANGER_RATIO:
                    box_color = (0, 0, 255)
                    status_text = f"BAO DONG: VUC SAU! ({danger_percent*100:.0f}%)"
                    # Hiệu ứng chớp đỏ toàn màn hình (Mô phỏng phanh gấp)
                    cv2.rectangle(color_frame, (0, 0), (640, 480), (0, 0, 255), 10)

                # Vẽ ROI lên màn hình RGB
                cv2.rectangle(color_frame, (ROI_X1, ROI_Y1), (ROI_X2, ROI_Y2), box_color, 2)
                cv2.putText(color_frame, status_text, (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, box_color, 2)
                
                cv2.imshow('Robot Vision - Cliff Detection', color_frame)

            # Vẽ trực quan hóa lên Depth Map để dễ Debug
            depth_display = cv2.convertScaleAbs(depth_image, alpha=0.03)
            depth_colormap = cv2.applyColorMap(depth_display, cv2.COLORMAP_JET)
            cv2.rectangle(depth_colormap, (ROI_X1, ROI_Y1), (ROI_X2, ROI_Y2), (255, 255, 255), 2)
            cv2.imshow('Depth Map', depth_colormap)

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