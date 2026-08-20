import cv2
import numpy as np
from openni import openni2
import sys

# --- THÔNG SỐ CẤU HÌNH ---
DEPTH_THRESHOLD_MM = 50  # Chênh lệch 50mm so với mặt sàn sẽ tính là vật cản
MIN_AREA_PIXELS = 1000   # Bỏ qua các hạt nhiễu nhỏ hơn 1000 pixel vuông

def main():
    openni2_dir = '/home/beniot-phan/APT_AstraProTest/sdk/OpenNI_2.3.0.86_202210111154_4c8f5aa4_beta6_linux/samples/samples/ThirdParty/OpenNI2/linux/x64'
    
    try:
        openni2.initialize(openni2_dir)
    except Exception as e:
        print(f"Lỗi khởi tạo OpenNI2: {e}")
        sys.exit(1)

    dev = depth_stream = ir_stream = cap = None
    is_running = True
    
    # Biến lưu trữ bản đồ mặt sàn trống
    background_depth = None 

    try:
        dev = openni2.Device.open_any()
        depth_stream = dev.create_depth_stream()
        depth_stream.start()
        
        ir_stream = dev.create_ir_stream()
        ir_stream.start()

        cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        print("Hệ thống sẵn sàng!\n - Chỉ camera vào sàn trống và nhấn 'b' để lưu mặt sàn.\n - Nhấn 'q' để thoát.")

        while is_running:
            ret, color_frame = cap.read() if cap.isOpened() else (False, None)

            depth_frame = depth_stream.read_frame()
            depth_data = np.frombuffer(depth_frame.get_buffer_as_uint16(), dtype=np.uint16)
            depth_image = depth_data.reshape(depth_frame.height, depth_frame.width)
            
            ir_frame = ir_stream.read_frame()
            ir_data = np.frombuffer(ir_frame.get_buffer_as_uint16(), dtype=np.uint16)
            ir_image = ir_data.reshape(ir_frame.height, ir_frame.width)

            # -- XỬ LÝ NHẬN DIỆN VẬT CẢN TỪ DEPTH --
            obstacle_mask = np.zeros((480, 640), dtype=np.uint8)
            
            if background_depth is not None:
                # Chỉ tính toán ở những điểm camera đọc được dữ liệu (> 0)
                valid_pixels = (depth_image > 0) & (background_depth > 0)
                
                # Ép kiểu int32 để tránh lỗi tràn số khi trừ
                diff = np.zeros_like(depth_image, dtype=np.int32)
                diff[valid_pixels] = np.abs(background_depth[valid_pixels].astype(np.int32) - depth_image[valid_pixels].astype(np.int32))
                
                # Tạo mặt nạ nhị phân: Điểm nào chênh lệch > 50mm thì thành màu trắng (255)
                obstacle_mask[diff > DEPTH_THRESHOLD_MM] = 255
                
                # Lọc nhiễu (Dùng Morphology để xóa các đốm trắng li ti)
                kernel = np.ones((5,5), np.uint8)
                obstacle_mask = cv2.morphologyEx(obstacle_mask, cv2.MORPH_OPEN, kernel)
                
                # Tìm viền các vật cản
                contours, _ = cv2.findContours(obstacle_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                for cnt in contours:
                    if cv2.contourArea(cnt) > MIN_AREA_PIXELS:
                        x, y, w, h = cv2.boundingRect(cnt)
                        # Vẽ Box lên luồng Depth để dễ nhìn
                        cv2.rectangle(depth_image, (x, y), (x+w, y+h), (0, 0, 0), 3)
                        # Trải nghiệm vẽ đè lên luồng RGB (Lưu ý: Sẽ bị lệch một chút do chưa đồng bộ vật lý)
                        if ret and color_frame is not None:
                            cv2.rectangle(color_frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                            cv2.putText(color_frame, "Obstacle", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            # -- HIỂN THỊ --
            depth_display = cv2.convertScaleAbs(depth_image, alpha=0.03)
            cv2.imshow('Depth Stream', cv2.applyColorMap(depth_display, cv2.COLORMAP_JET))
            
            ir_display = cv2.convertScaleAbs(ir_image, alpha=0.1)
            cv2.imshow('IR Stream', ir_display)
            cv2.imshow('Obstacle Mask (Trang=Vat Can)', obstacle_mask)
            
            if ret and color_frame is not None:
                cv2.imshow('RGB Stream', color_frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                is_running = False
            elif key == ord('b'):
                # Lưu lại khung hình nền
                background_depth = depth_image.copy()
                print("ĐÃ LƯU BẢN ĐỒ MẶT SÀN! Hãy đưa vật cản vào.")

    except KeyboardInterrupt:
        print("\nĐang đóng an toàn...")
    finally:
        if cap: cap.release()
        if depth_stream: depth_stream.stop()
        if ir_stream: ir_stream.stop()
        if dev: dev.close()
        openni2.unload()
        cv2.destroyAllWindows()

if __name__ == '__main__':
    main()