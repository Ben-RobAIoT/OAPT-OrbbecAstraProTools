"""
=============================================================================
File Name   : 01_basic_streams_viewer.py
Description : Chương trình testbench cơ bản kèm TRÌNH CHẨN ĐOÁN LỖI .SO (Linux/WSL2).
              Được thiết kế để đọc libOpenNI2.so ngay tại thư mục gốc dự án.
=============================================================================
"""

import os
import sys
import ctypes
import cv2
import numpy as np
from openni import openni2
from openni import _openni2 as c_api

# =====================================================================
# BƯỚC 1: XỬ LÝ MÔI TRƯỜNG & ĐƯỜNG DẪN TẠI THƯ MỤC GỐC
# =====================================================================
# Lấy thư mục chứa file script này (cũng là nơi bạn đang để libOpenNI2.so)
CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))
SO_PATH = os.path.join(CURRENT_DIR, "libOpenNI2.so")

print(f"[*] Thư mục làm việc hiện tại: {CURRENT_DIR}")

# Ép chuyển thư mục làm việc (Working Directory) về đúng gốc
os.chdir(CURRENT_DIR)

# =====================================================================
# BƯỚC 2: BÀI TEST TỬ THẦN - NẠP TRỰC TIẾP .SO BẰNG CTYPES
# =====================================================================
print(f"[*] Đang ép lõi Linux nạp file: {SO_PATH}")
try:
    # Trên Linux, ta dùng cdll.LoadLibrary thay vì CDLL với winmode
    _lib = ctypes.cdll.LoadLibrary(SO_PATH)
    print("[+] KẾT QUẢ: THÀNH CÔNG! Lõi hệ thống Linux đã chấp nhận file .so này.")
except Exception as e:
    print("\n[-] KẾT QUẢ: THẤT BẠI TRÍ MẠNG!")
    print(f"[-] Mã lỗi từ hệ điều hành: {e}")
    print("=====================================================")
    print("=> KẾT LUẬN: Lỗi KHÔNG PHẢI do Python hay code của chúng ta.")
    print("=> NGUYÊN NHÂN: File libOpenNI2.so này đang 'chỏi' với hệ điều hành Ubuntu của bạn.")
    print("   1. Có thể kiến trúc CPU không khớp (ví dụ: arm64 vs x86_64).")
    print("   2. Thiếu các thư viện phụ thuộc (dependencies) như libusb. Hãy thử chạy 'ldd libOpenNI2.so' trong terminal để kiểm tra.")
    print("=====================================================")
    sys.exit(1)

# =====================================================================
# BƯỚC 3: CHẠY CAMERA (Chỉ tới được đây nếu Bước 2 Thành Công)
# =====================================================================
print("\n[*] Đang khởi động thư viện OpenNI Python và kết nối Astra Pro...")

def main():
    try:
        # Khởi tạo OpenNI tại đúng thư mục gốc
        openni2.initialize(CURRENT_DIR)
        print("[+] OpenNI2 Initialize THÀNH CÔNG!")
    except Exception as e:
        print(f"[-] Lỗi khởi tạo OpenNI2: {e}")
        return

    dev = openni2.Device.open_any()
    
    depth_stream = dev.create_depth_stream()
    depth_stream.start()
    depth_stream.set_video_mode(c_api.OniVideoMode(pixelFormat = c_api.OniPixelFormat.ONI_PIXEL_FORMAT_DEPTH_1_MM, resolutionX = 640, resolutionY = 480, fps = 30))
    # Trên Linux/WSL2, dùng V4L2 làm backend thay vì DSHOW của Windows
    rgb_cap = cv2.VideoCapture(0, cv2.CAP_V4L2) 
    if not rgb_cap.isOpened():
        rgb_cap = cv2.VideoCapture(1, cv2.CAP_V4L2)

    print("\n>> CAMERA ĐÃ MỞ! (Nhấn 'q' trên cửa sổ để thoát)")

    while True:
        frame_depth = depth_stream.read_frame()
        frame_depth_data = frame_depth.get_buffer_as_uint16()
        
        depth_array = np.ndarray((frame_depth.height, frame_depth.width), dtype=np.uint16, buffer=frame_depth_data)
        depth_image = cv2.convertScaleAbs(depth_array, alpha=0.03) 
        depth_colormap = cv2.applyColorMap(depth_image, cv2.COLORMAP_JET)

        ret, rgb_frame = rgb_cap.read()

        if ret:
            cv2.imshow("Orbbec Astra Pro - RGB Stream", rgb_frame)
        cv2.imshow("Orbbec Astra Pro - Depth Stream", depth_colormap)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    rgb_cap.release()
    depth_stream.stop()
    openni2.unload()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()