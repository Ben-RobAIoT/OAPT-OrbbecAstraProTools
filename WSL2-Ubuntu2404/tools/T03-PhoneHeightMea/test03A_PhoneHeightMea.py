import cv2
import numpy as np
from openni import openni2
import sys

# Tham số Calib: Tiêu cự giả định (Bạn hãy tăng/giảm số này để kết quả khớp với thước đo thực tế)
FOCAL_LENGTH_Y = 500.0  

def main():
    openni2_dir = '/home/beniot-phan/APT_AstraProTest/sdk/OpenNI_2.3.0.86_202210111154_4c8f5aa4_beta6_linux/samples/samples/ThirdParty/OpenNI2/linux/x64'
    
    try:
        openni2.initialize(openni2_dir)
    except Exception as e:
        print(f"Lỗi khởi tạo OpenNI2: {e}")
        sys.exit(1)

    dev = None
    depth_stream = None
    cap = None

    try:
        dev = openni2.Device.open_any()
        depth_stream = dev.create_depth_stream()
        depth_stream.start()

        cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        print("Hệ thống sẵn sàng. Đặt điện thoại lên nền trống để đo. Nhấn 'q' hoặc Ctrl+C để thoát.")

        while True:
            ret, color_frame = cap.read() if cap.isOpened() else (False, None)

            depth_frame = depth_stream.read_frame()
            depth_data = np.frombuffer(depth_frame.get_buffer_as_uint16(), dtype=np.uint16)
            depth_image = depth_data.reshape(depth_frame.height, depth_frame.width)

            if ret and color_frame is not None:
                # 1. Tiền xử lý ảnh RGB để tìm cạnh điện thoại
                gray = cv2.cvtColor(color_frame, cv2.COLOR_BGR2GRAY)
                blurred = cv2.GaussianBlur(gray, (5, 5), 0)
                edges = cv2.Canny(blurred, 50, 150)
                
                # 2. Tìm viền (Contours)
                contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                if contours:
                    # Lấy viền lớn nhất (Giả định là điện thoại)
                    largest_contour = max(contours, key=cv2.contourArea)
                    
                    # Lọc nhiễu: Chỉ xử lý nếu diện tích đủ lớn
                    if cv2.contourArea(largest_contour) > 2000:
                        x, y, w, h_pixel = cv2.boundingRect(largest_contour)
                        
                        # Tọa độ tâm điện thoại
                        cx, cy = x + w // 2, y + h_pixel // 2
                        
                        # 3. Lấy độ sâu tại tâm Z (mm)
                        if 0 <= cx < depth_frame.width and 0 <= cy < depth_frame.height:
                            z_mm = depth_image[cy, cx]
                            
                            # 4. Tính toán chiều cao thực tế
                            if z_mm > 0:
                                real_height_mm = (h_pixel * z_mm) / FOCAL_LENGTH_Y
                                
                                # Vẽ Box và Thông tin
                                cv2.rectangle(color_frame, (x, y), (x + w, y + h_pixel), (0, 255, 0), 2)
                                cv2.circle(color_frame, (cx, cy), 5, (0, 0, 255), -1)
                                
                                text_depth = f"Khoang cach: {z_mm} mm"
                                text_height = f"Chieu cao: {real_height_mm:.1f} mm"
                                cv2.putText(color_frame, text_depth, (x, y - 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                                cv2.putText(color_frame, text_height, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

                cv2.imshow('RGB - Phone Measurement', color_frame)

            depth_display = cv2.convertScaleAbs(depth_image, alpha=0.03)
            cv2.imshow('Depth Map', cv2.applyColorMap(depth_display, cv2.COLORMAP_JET))

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    # BẮT SỰ KIỆN CTRL+C ĐỂ KHÔNG BỊ KẸT CAMERA
    except KeyboardInterrupt:
        print("\n[Cảnh báo] Đã nhận lệnh ngắt (Ctrl+C). Bắt đầu quy trình đóng an toàn...")
    except Exception as e:
        print(f"Lỗi Runtime: {e}")
    finally:
        print("Đang giải phóng toàn bộ tài nguyên...")
        if cap: cap.release()
        if depth_stream: depth_stream.stop()
        if dev: dev.close()
        openni2.unload()
        cv2.destroyAllWindows()
        print("Đã dọn dẹp xong. Không còn Zombie Camera!")

if __name__ == '__main__':
    main()