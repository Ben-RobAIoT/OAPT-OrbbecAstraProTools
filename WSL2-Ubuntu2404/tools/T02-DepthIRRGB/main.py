import cv2
import numpy as np
from openni import openni2
import sys

def main():
    # Giữ nguyên đường dẫn đã chạy thành công của bạn[cite: 2]
    openni2_dir = '/home/beniot-phan/APT_AstraProTest/sdk/OpenNI_2.3.0.86_202210111154_4c8f5aa4_beta6_linux/samples/samples/ThirdParty/OpenNI2/linux/x64'
    
    try:
        openni2.initialize(openni2_dir) #[cite: 2]
        print("Đã khởi tạo OpenNI2 thành công.")
    except Exception as e:
        print(f"Lỗi khởi tạo OpenNI2: {e}")
        sys.exit(1)

    dev = None
    depth_stream = None
    ir_stream = None
    cap = None

    try:
        dev = openni2.Device.open_any() #[cite: 2]
        print("Đã kết nối camera Orbbec qua libusb.")

        # 1. Khởi tạo luồng Depth[cite: 2]
        depth_stream = dev.create_depth_stream()
        depth_stream.start()

        # 2. Khởi tạo luồng IR (Đã bật lại)
        ir_stream = dev.create_ir_stream()
        ir_stream.start()

        # 3. Khởi tạo RGB bằng V4L2[cite: 2]
        cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
        # Ép định dạng nén MJPG để giảm tải[cite: 2]
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640) #[cite: 2]
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480) #[cite: 2]

        if not cap.isOpened(): #[cite: 2]
            print("Không thể mở RGB Camera. Hệ thống sẽ tiếp tục chạy Depth và IR...")

        print("Đã khởi tạo xong 3 luồng. Nhấn 'q' để thoát.")

        while True:
            ret = False
            color_frame = None
            
            # -- ĐỌC RGB --[cite: 2]
            if cap and cap.isOpened():
                ret, color_frame = cap.read()

            # -- ĐỌC DEPTH --[cite: 2]
            depth_frame = depth_stream.read_frame()
            depth_data = np.frombuffer(depth_frame.get_buffer_as_uint16(), dtype=np.uint16)
            depth_image = depth_data.reshape(depth_frame.height, depth_frame.width)
            
            depth_display = cv2.convertScaleAbs(depth_image, alpha=0.03)
            depth_colormap = cv2.applyColorMap(depth_display, cv2.COLORMAP_JET)

            # -- ĐỌC IR --
            ir_frame = ir_stream.read_frame()
            ir_data = np.frombuffer(ir_frame.get_buffer_as_uint16(), dtype=np.uint16)
            ir_image = ir_data.reshape(ir_frame.height, ir_frame.width)
            
            # Dữ liệu IR 16-bit thường khá tối, cần scale alpha để dễ nhìn (bạn có thể tinh chỉnh 0.05 - 0.2)
            ir_display = cv2.convertScaleAbs(ir_image, alpha=0.1) 

            # -- HIỂN THỊ 3 LUỒNG --
            cv2.imshow('Depth Stream', depth_colormap)
            cv2.imshow('IR Stream', ir_display)
            
            if ret and color_frame is not None:
                cv2.imshow('RGB Stream', color_frame)

            if cv2.waitKey(1) & 0xFF == ord('q'): #[cite: 2]
                break

    except Exception as e:
        print(f"Có lỗi xảy ra trong Main Loop: {e}")

    finally:
        print("Đang tiến hành dọn dẹp tài nguyên thiết bị...")
        if cap:
            cap.release() #[cite: 2]
        if depth_stream:
            depth_stream.stop() #[cite: 2]
        if ir_stream:
            ir_stream.stop()
        if dev:
            dev.close() #[cite: 2]
        openni2.unload() #[cite: 2]
        cv2.destroyAllWindows() #[cite: 2]
        print("Đã giải phóng USB và Camera.")

if __name__ == '__main__':
    main() #[cite: 2]
