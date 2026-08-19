import cv2
import numpy as np
# Import mediapipe trực tiếp
from mediapipe.python.solutions import hands as mp_hands
from mediapipe.python.solutions import drawing_utils as mp_drawing
from openni import openni2
import sys

# --- Cấu hình MediaPipe ---
hands = mp_hands.Hands(
    min_detection_confidence=0.7, 
    min_tracking_confidence=0.7, 
    max_num_hands=1
)

def main():
    # CHỈ DÙNG CHUỖI STRING BÌNH THƯỜNG
    openni2_dir = '/home/beniot-phan/APT_AstraProTest/sdk/OpenNI_2.3.0.86_202210111154_4c8f5aa4_beta6_linux/samples/samples/ThirdParty/OpenNI2/linux/x64'
    
    try:
        openni2.initialize(openni2_dir)
        print("Đã khởi tạo OpenNI2 thành công.")
    except Exception as e:
        print(f"Lỗi khởi tạo OpenNI2: {e}")
        sys.exit(1)

    dev = None
    depth_stream = None
    cap = None

    try:
        dev = openni2.Device.open_any()
        print("Đã kết nối camera Orbbec qua libusb.")

        # --- ĐÃ COMMENT ĐỂ FIX LỖI getProperty(5) ---
        # if dev.get_image_registration_mode() != openni2.IMAGE_REGISTRATION_DEPTH_TO_COLOR:
        #     dev.set_image_registration_mode(openni2.IMAGE_REGISTRATION_DEPTH_TO_COLOR)
        # --------------------------------------------

        # Khởi tạo luồng Depth
        depth_stream = dev.create_depth_stream()
        depth_stream.start()

        # --- ĐÃ COMMENT LUỒNG IR ĐỂ TRÁNH NGHẼN BĂNG THÔNG USB WSL2 ---
        # ir_stream = dev.create_ir_stream()
        # ir_stream.start()
        # --------------------------------------------------------------

        # Khởi tạo RGB bằng V4L2. Thử index 0 trước, nếu không được bạn đổi thành 1
        cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
        # Ép định dạng nén MJPG
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        if not cap.isOpened():
            print("Không thể mở RGB Camera. Hệ thống sẽ tiếp tục chạy để kiểm tra luồng Depth...")

        print("Đã khởi tạo xong. Nhấn 'q' để thoát.")

        while True:
            ret = False
            color_frame = None
            
            # -- ĐỌC RGB (Không để lỗi RGB chặn Depth) --
            if cap and cap.isOpened():
                ret, color_frame = cap.read()

            # -- ĐỌC DEPTH --
            depth_frame = depth_stream.read_frame()
            depth_data = np.frombuffer(depth_frame.get_buffer_as_uint16(), dtype=np.uint16)
            depth_image = depth_data.reshape(depth_frame.height, depth_frame.width)

            depth_display = cv2.convertScaleAbs(depth_image, alpha=0.03)
            depth_colormap = cv2.applyColorMap(depth_display, cv2.COLORMAP_JET)

            # Hiển thị Depth Map NGAY LẬP TỨC
            cv2.imshow('Depth Map', depth_colormap)

            # -- XỬ LÝ RGB VÀ MEDIAPIPE --
            if ret and color_frame is not None:
                color_rgb = cv2.cvtColor(color_frame, cv2.COLOR_BGR2RGB)
                results = hands.process(color_rgb)

                if results.multi_hand_landmarks:
                    for hand_landmarks in results.multi_hand_landmarks:
                        mp_drawing.draw_landmarks(color_frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                        
                        h, w, _ = color_frame.shape
                        cx, cy = int(hand_landmarks.landmark[9].x * w), int(hand_landmarks.landmark[9].y * h)
                        
                        if 0 <= cx < depth_frame.width and 0 <= cy < depth_frame.height:
                            distance_mm = depth_image[cy, cx]
                            cv2.circle(color_frame, (cx, cy), 5, (0, 255, 0), cv2.FILLED)
                            cv2.putText(color_frame, f"Distance: {distance_mm} mm", (cx - 50, cy - 20),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

                cv2.imshow('RGB Tracking', color_frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except Exception as e:
        print(f"Có lỗi xảy ra trong Main Loop: {e}")

    finally:
        print("Đang tiến hành dọn dẹp tài nguyên thiết bị...")
        if cap:
            cap.release()
        if depth_stream:
            depth_stream.stop()
        if dev:
            dev.close()
        openni2.unload()
        cv2.destroyAllWindows()
        print("Đã giải phóng USB và Camera.")

if __name__ == '__main__':
    main()