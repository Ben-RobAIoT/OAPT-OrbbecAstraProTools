import cv2
import numpy as np
from openni import openni2
import platform
import sys
import os
import time # THÊM THƯ VIỆN NÀY ĐỂ XỬ LÝ DELAY PHẦN CỨNG

OS_TYPE = platform.system()
print(f"[*] Hệ điều hành được phát hiện: {OS_TYPE}")

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

if OS_TYPE == "Windows":
    OPENNI2_DIR = os.path.join(CURRENT_DIR, "OpenNI2_Win")
    
    if hasattr(os, "add_dll_directory"):
        os.add_dll_directory(OPENNI2_DIR)
        os.add_dll_directory(os.path.join(OPENNI2_DIR, "OpenNI2", "Drivers"))
        
    os.environ["PATH"] = OPENNI2_DIR + os.pathsep + os.environ["PATH"]
    os.environ["PATH"] = os.path.join(OPENNI2_DIR, "OpenNI2", "Drivers") + os.pathsep + os.environ["PATH"]
    
    # SỬA DSHOW THÀNH MSMF ĐỂ ỔN ĐỊNH TRÊN WINDOWS 11
    CV_BACKEND = cv2.CAP_MSMF 
elif OS_TYPE == "Linux":
    OPENNI2_DIR = "/usr/lib/"     
    CV_BACKEND = cv2.CAP_V4L2      
else:
    print("[!] Hệ điều hành không được hỗ trợ.")
    sys.exit(1)

def main():
    dev = None
    depth_stream = None
    cap = None

    try:
        # ==========================================
        # 1. KHỞI TẠO OPENNI2
        # ==========================================
        openni2.initialize(OPENNI2_DIR)
        print("[*] Đã nạp thư viện OpenNI2 thành công.")
        
        dev = openni2.Device.open_any()
        depth_stream = dev.create_depth_stream()
        depth_stream.start()
        print("[*] Luồng Depth đã sẵn sàng.")

        # Nghỉ ngơi 1.5s để chống "ngợp" băng thông USB
        print("[*] Đang đợi phần cứng ổn định luồng USB...")
        time.sleep(1.5)

        # ==========================================
        # 2. KHỞI TẠO OPENCV TỰ DÒ INDEX
        # ==========================================
        cap = cv2.VideoCapture(0, CV_BACKEND) # Giữ nguyên số 1 hoặc 0 tùy máy bạn

        if cap is None:
            print("[!] Không thể tìm thấy luồng RGB khả dụng.")
            return

        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)

        print("[*] Đang chạy... Nhấn 'q' hoặc 'Ctrl+C' để thoát.")

        # ==========================================
        # 3. VÒNG LẶP CHÍNH
        # ==========================================
        while True:
            ret, color_frame = cap.read()
            
            depth_frame = depth_stream.read_frame()
            depth_data = depth_frame.get_buffer_as_uint16()
            
            depth_matrix = np.ndarray((depth_frame.height, depth_frame.width), dtype=np.uint16, buffer=depth_data)
            depth_8bit = cv2.normalize(depth_matrix, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
            depth_color_map = cv2.applyColorMap(depth_8bit, cv2.COLORMAP_JET)

            if ret:
                cv2.imshow("RGB Stream (OpenCV UVC)", color_frame)
            cv2.imshow("Depth Stream (OpenNI2)", depth_color_map)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except KeyboardInterrupt:
        print("\n[*] Đã nhận lệnh ngắt từ bàn phím (Ctrl+C).")
    except Exception as e:
        print(f"\n[!] Có lỗi xảy ra trong lúc chạy: {e}")
    finally:
        # ==========================================
        # 4. BỘ DỌN DẸP TUYỆT ĐỐI (LUÔN ĐƯỢC GỌI)
        # ==========================================
        print("\n[*] Đang kích hoạt tiến trình xả cổng USB (Software Reset)...")
        if cap is not None:
            cap.release()
            print("  - Đã giải phóng Camera RGB.")
            
        if depth_stream is not None:
            depth_stream.stop()
            print("  - Đã dừng luồng Depth.")
            
        if dev is not None:
            dev.close()  # LỆNH MẤU CHỐT: Yêu cầu nhả phần cứng
            print("  - Đã ngắt kết nối vật lý với Astra Pro.")
            
        openni2.unload()
        cv2.destroyAllWindows()
        print("[*] Hoàn tất xả tài nguyên. Sẵn sàng cho lần chạy tiếp theo!")

if __name__ == "__main__":
    main()