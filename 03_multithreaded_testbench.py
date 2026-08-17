"""
=============================================================================
File Name   : 03_multithreaded_testbench.py
Description : Testbench TỐI ƯU ĐA LUỒNG - Giải quyết dứt điểm giật lag WSL2.
=============================================================================
"""

import os
import sys
import ctypes
import cv2
import numpy as np
import threading
import time
from openni import openni2

CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))
SO_PATH = os.path.join(CURRENT_DIR, "libOpenNI2.so")
os.chdir(CURRENT_DIR)

try:
    ctypes.cdll.LoadLibrary(SO_PATH)
except Exception as e:
    print(f"[-] Lỗi nạp libOpenNI2.so: {e}")
    sys.exit(1)

# =====================================================================
# BIẾN TOÀN CỤC & KHÓA (LOCK) CHO MULTI-THREADING
# =====================================================================
latest_rgb = None
latest_depth = None
latest_ir = None
running = True
frame_lock = threading.Lock()

# =====================================================================
# LUỒNG 1: ĐỌC DỮ LIỆU TỪ OPENCV (RGB) - CẬP NHẬT RADAR DÒ TÌM
# =====================================================================
def capture_rgb():
    global latest_rgb, running
    cap = None
    
    # 1. Dò quét từ cổng video0 đến video5 để tìm camera UVC
    for i in range(6):
        print(f"[*] Đang thử kết nối RGB tại /dev/video{i}...")
        temp_cap = cv2.VideoCapture(i, cv2.CAP_V4L2)
        
        if temp_cap.isOpened():
            # Ép cấu hình MJPG để tránh nghẽn timeout trên WSL2
            temp_cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
            temp_cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            temp_cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            temp_cap.set(cv2.CAP_PROP_FPS, 30)
            temp_cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            # Đọc thử 1 frame xem có nhận được dữ liệu không
            ret, _ = temp_cap.read()
            if ret:
                cap = temp_cap
                print(f"[+] BINGOOOO! Đã tìm thấy luồng RGB tại /dev/video{i}")
                break
            else:
                temp_cap.release()
                
    if cap is None:
        print("[-] Cảnh báo: Không tìm thấy camera RGB nào phản hồi dữ liệu!")
        return

    # 2. Vòng lặp lấy khung hình liên tục
    while running and cap.isOpened():
        ret, frame = cap.read()
        if ret:
            with frame_lock:
                latest_rgb = frame.copy()
        else:
            time.sleep(0.01) # Nghỉ một chút nếu bị nghẽn để tránh cháy CPU
            
    if cap and cap.isOpened():
        cap.release()

# =====================================================================
# LUỒNG 2: ĐỌC DỮ LIỆU TỪ OPENNI2 (DEPTH & IR)
# =====================================================================
def capture_openni(dev):
    global latest_depth, latest_ir, running
    
    depth_stream = dev.create_depth_stream()
    ir_stream = dev.create_ir_stream()
    
    depth_stream.start()
    ir_stream.start()
    
    while running:
        try:
            # Đọc Depth
            frame_d = depth_stream.read_frame()
            d_data = frame_d.get_buffer_as_uint16()
            d_array = np.ndarray((frame_d.height, frame_d.width), dtype=np.uint16, buffer=d_data)
            
            # Đọc IR (Astra Pro dùng chung cảm biến CMOS cho Depth và IR)
            frame_i = ir_stream.read_frame()
            i_data = frame_i.get_buffer_as_uint16()
            i_array = np.ndarray((frame_i.height, frame_i.width), dtype=np.uint16, buffer=i_data)
            
            with frame_lock:
                latest_depth = d_array.copy()
                latest_ir = i_array.copy()
        except Exception as e:
            time.sleep(0.01)
            
    depth_stream.stop()
    ir_stream.stop()

# =====================================================================
# LUỒNG CHÍNH: HIỂN THỊ GIAO DIỆN & TÍNH FPS (ĐÃ NÂNG CẤP CHỐNG KẸT USB)
# =====================================================================
def main():
    global running, latest_rgb, latest_depth, latest_ir
    
    print("[*] Đang khởi tạo OpenNI2...")
    openni2.initialize(CURRENT_DIR)
    dev = openni2.Device.open_any()
    
    print("[*] Kích hoạt hệ thống Đa luồng (Multi-threading)...")
    t_rgb = threading.Thread(target=capture_rgb, daemon=True)
    t_openni = threading.Thread(target=capture_openni, args=(dev,), daemon=True)
    
    t_rgb.start()
    t_openni.start()
    
    print("\n>> TESTBENCH ĐA LUỒNG ĐÃ MỞ! (Nhấn 'q' hoặc Ctrl+C để thoát)")
    
    prev_time = time.time()
    
    try:
        while running:
            # Lấy bản sao frame mới nhất từ các luồng
            with frame_lock:
                r_frame = latest_rgb
                d_frame = latest_depth
                i_frame = latest_ir
                
            # Tính toán FPS mượt mà
            curr_time = time.time()
            fps = 1.0 / (curr_time - prev_time + 1e-5) 
            prev_time = curr_time
            fps_text = f"FPS: {int(fps)}"

            # Render RGB
            if r_frame is not None:
                cv2.putText(r_frame, fps_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                cv2.imshow("Astra Pro - RGB", r_frame)
                
            # Render Depth
            if d_frame is not None:
                depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(d_frame, alpha=0.03), cv2.COLORMAP_JET)
                cv2.putText(depth_colormap, fps_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                cv2.imshow("Astra Pro - Depth", depth_colormap)

            # Render IR
            if i_frame is not None:
                ir_image = cv2.convertScaleAbs(i_frame, alpha=0.15)
                cv2.putText(ir_image, fps_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                cv2.imshow("Astra Pro - IR", ir_image)

            # Cập nhật GUI mỗi 30ms (~33 FPS max cho phần hiển thị)
            if cv2.waitKey(30) & 0xFF == ord('q'):
                running = False
                break

    except KeyboardInterrupt:
        # Sự kiện này sẽ được kích hoạt ngay khi bạn bấm Ctrl + C
        print("\n[!] NHẬN ĐƯỢC LỆNH NGẮT TỪ BÀN PHÍM (Ctrl+C)!")
        running = False
        
    finally:
        # Mọi con đường đều phải đi qua đây trước khi sập nguồn
        print("[*] Đang đóng luồng và giải phóng kết nối USB...")
        running = False
        t_rgb.join(timeout=1.0)
        t_openni.join(timeout=1.0)
        
        try:
            openni2.unload()
        except Exception as e:
            print(f"[-] Lỗi khi unload OpenNI: {e}")
            
        cv2.destroyAllWindows()
        print("[+] Đã trả lại tự do cho Camera! Hoàn tất thoái lui an toàn.")

if __name__ == "__main__":
    main()