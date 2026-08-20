import cv2
import numpy as np
from openni import openni2
import sys
import os
import time

def setup_directories(base_dir="dataset"):
    """Tạo cấu trúc thư mục chuẩn để lưu dataset"""
    folders = ['rgb', 'depth_16bit', 'ir']
    for folder in folders:
        os.makedirs(os.path.join(base_dir, folder), exist_ok=True)
    return base_dir

def main():
    dataset_dir = setup_directories()
    
    openni2_dir = '/home/beniot-phan/APT_AstraProTest/sdk/OpenNI_2.3.0.86_202210111154_4c8f5aa4_beta6_linux/samples/samples/ThirdParty/OpenNI2/linux/x64'
    
    try:
        openni2.initialize(openni2_dir)
    except Exception as e:
        print(f"Lỗi khởi tạo OpenNI2: {e}")
        sys.exit(1)

    dev = depth_stream = ir_stream = cap = None
    is_running = True
    is_recording = False
    frame_count = 0

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

        print(f"Hệ thống sẵn sàng!\n - Nhấn 'r' để BẮT ĐẦU / DỪNG ghi dữ liệu.\n - Nhấn 'q' để THOÁT.")

        while is_running:
            ret, color_frame = cap.read() if cap.isOpened() else (False, None)

            depth_frame = depth_stream.read_frame()
            depth_data = np.frombuffer(depth_frame.get_buffer_as_uint16(), dtype=np.uint16)
            depth_image = depth_data.reshape(depth_frame.height, depth_frame.width)
            
            ir_frame = ir_stream.read_frame()
            ir_data = np.frombuffer(ir_frame.get_buffer_as_uint16(), dtype=np.uint16)
            ir_image = ir_data.reshape(ir_frame.height, ir_frame.width)

            if ret and color_frame is not None:
                # -- LOGIC LƯU DỮ LIỆU --
                if is_recording:
                    timestamp = f"{frame_count:06d}"
                    # Lưu RGB dạng JPG
                    cv2.imwrite(os.path.join(dataset_dir, f'rgb/frame_{timestamp}.jpg'), color_frame)
                    # Lưu Depth nguyên bản 16-bit dạng PNG (Quan trọng!)
                    cv2.imwrite(os.path.join(dataset_dir, f'depth_16bit/frame_{timestamp}.png'), depth_image)
                    # Lưu IR dạng JPG (đã scale để dễ nhìn)
                    ir_save = cv2.convertScaleAbs(ir_image, alpha=0.1)
                    cv2.imwrite(os.path.join(dataset_dir, f'ir/frame_{timestamp}.jpg'), ir_save)
                    
                    frame_count += 1
                    cv2.putText(color_frame, f"REC: {frame_count} frames", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

                # -- HIỂN THỊ --
                depth_display = cv2.convertScaleAbs(depth_image, alpha=0.03)
                ir_display = cv2.convertScaleAbs(ir_image, alpha=0.1)

                cv2.imshow('RGB Stream', color_frame)
                cv2.imshow('Depth Stream', cv2.applyColorMap(depth_display, cv2.COLORMAP_JET))
                cv2.imshow('IR Stream', ir_display)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                is_running = False
            elif key == ord('r'):
                is_recording = not is_recording
                print("ĐANG GHI DỮ LIỆU..." if is_recording else f"ĐÃ DỪNG. Tổng frames: {frame_count}")

    except KeyboardInterrupt:
        print("\n[Cảnh báo] Đã nhận lệnh ngắt (Ctrl+C). Bắt đầu quy trình đóng an toàn...")
    except Exception as e:
        print(f"Lỗi Runtime: {e}")
    finally:
        print("Đang giải phóng toàn bộ tài nguyên...")
        if cap: cap.release()
        if depth_stream: depth_stream.stop()
        if ir_stream: ir_stream.stop()
        if dev: dev.close()
        openni2.unload()
        cv2.destroyAllWindows()
        print("Đã giải phóng USB và Camera.")

if __name__ == '__main__':
    main()