"""
=============================================================================
File Name   : 02_advanced_testbench.py
Description : Testbench ĐA LUỒNG (Depth, IR, RGB) đã tối ưu chống giật lag.
=============================================================================
"""

import os
import sys
import ctypes
import cv2
import numpy as np
from openni import openni2

CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))
SO_PATH = os.path.join(CURRENT_DIR, "libOpenNI2.so")
os.chdir(CURRENT_DIR)

# Nạp thư viện lõi
try:
    ctypes.cdll.LoadLibrary(SO_PATH)
except Exception as e:
    print(f"[-] Lỗi nạp libOpenNI2.so: {e}")
    sys.exit(1)

def main():
    openni2.initialize(CURRENT_DIR)
    dev = openni2.Device.open_any()
    
    print("[*] Đang khởi tạo luồng Depth...")
    depth_stream = dev.create_depth_stream()
    depth_stream.start()

    print("[*] Đang khởi tạo luồng Hồng ngoại (IR)...")
    ir_stream = dev.create_ir_stream()
    ir_stream.start()

    print("[*] Đang tìm kiếm luồng RGB (V4L2)...")
    # Thử kết nối camera RGB. Nếu video0 bị nghẽn, bạn có thể đổi thành 1 hoặc 2
    rgb_cap = cv2.VideoCapture(0, cv2.CAP_V4L2) 
    
    if rgb_cap.isOpened():
        # TỐI ƯU CHỐNG LAG: Ép OpenCV chỉ lưu 1 frame mới nhất, bỏ qua frame cũ
        rgb_cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        print("[+] Đã kết nối RGB thành công!")
    else:
        print("[-] Không tìm thấy UVC Camera cho luồng RGB.")

    print("\n>> ĐANG CHẠY TESTBENCH! (Nhấn 'q' để thoát)")

    while True:
        # 1. Xử lý luồng Depth (Bản đồ chiều sâu)
        frame_depth = depth_stream.read_frame()
        depth_data = frame_depth.get_buffer_as_uint16()
        depth_array = np.ndarray((frame_depth.height, frame_depth.width), dtype=np.uint16, buffer=depth_data)
        depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(depth_array, alpha=0.03), cv2.COLORMAP_JET)
        cv2.imshow("1. Astra Pro - Depth (OpenNI2)", depth_colormap)

        # 2. Xử lý luồng IR (Hồng ngoại)
        frame_ir = ir_stream.read_frame()
        ir_data = frame_ir.get_buffer_as_uint16()
        ir_array = np.ndarray((frame_ir.height, frame_ir.width), dtype=np.uint16, buffer=ir_data)
        # Chuyển đổi dải màu 16-bit xuống 8-bit để hiển thị trắng đen
        ir_image = cv2.convertScaleAbs(ir_array, alpha=0.15)
        cv2.imshow("2. Astra Pro - Infrared (OpenNI2)", ir_image)

        # 3. Xử lý luồng RGB (Màu)
        if rgb_cap.isOpened():
            # Grab() thay vì read() giúp giảm thiểu tối đa việc block luồng chính
            if rgb_cap.grab():
                ret, rgb_frame = rgb_cap.retrieve()
                if ret:
                    cv2.imshow("3. Astra Pro - RGB (OpenCV V4L2)", rgb_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Dọn dẹp tài nguyên
    if rgb_cap.isOpened():
        rgb_cap.release()
    depth_stream.stop()
    ir_stream.stop()
    openni2.unload()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()