import os
# --- BỘ KHIÊN CHỐNG CRASH BỘ NHỚ TRÊN WSL2 ---[cite: 6]
os.environ['LIBGL_ALWAYS_SOFTWARE'] = '1'
os.environ['OPENCV_OPENCL_RUNTIME'] = 'disabled'
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'

import cv2
import numpy as np
from openni import openni2
import sys
import open3d as o3d

# --- THÔNG SỐ CAMERA INTRINSICS (Orbbec Astra Pro - Cấu hình chuẩn) ---
FX, FY = 570.3, 570.3
CX, CY = 320.0, 240.0

def main():
    openni2_dir = '/home/beniot-phan/APT_AstraProTest/sdk/OpenNI_2.3.0.86_202210111154_4c8f5aa4_beta6_linux/samples/samples/ThirdParty/OpenNI2/linux/x64'
    
    try:
        openni2.initialize(openni2_dir)
    except Exception as e:
        print(f"Lỗi khởi tạo OpenNI2: {e}")
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

        # --- KHỞI TẠO OPEN3D VISUALIZER ---
        vis = o3d.visualization.Visualizer()
        vis.create_window(window_name='Orbbec Astra 3D Scanner', width=800, height=600)
        
        # Khởi tạo khung Point Cloud rỗng
        pcd = o3d.geometry.PointCloud()
        is_first_frame = True

        # Đối tượng Intrinsic của Open3D
        intrinsic = o3d.camera.PinholeCameraIntrinsic(640, 480, FX, FY, CX, CY)

        print("Hệ thống 3D Point Cloud đã sẵn sàng! Chĩa camera vào vật thể...")
        print("Nhấn 'q' trên cửa sổ OpenCV để thoát.")

        while is_running:
            ret, color_frame = cap.read() if cap.isOpened() else (False, None)
            
            # Đọc luồng Depth và copy để cách ly bộ nhớ[cite: 2]
            depth_frame = depth_stream.read_frame()
            depth_data = np.frombuffer(depth_frame.get_buffer_as_uint16(), dtype=np.uint16).copy()
            depth_image = depth_data.reshape(depth_frame.height, depth_frame.width)

            if ret and color_frame is not None:
                # Chuyển BGR (OpenCV) sang RGB (Open3D)
                color_rgb = cv2.cvtColor(color_frame, cv2.COLOR_BGR2RGB)
                
                # Chuyển đổi dữ liệu Numpy sang định dạng Image của Open3D
                o3d_color = o3d.geometry.Image(color_rgb)
                o3d_depth = o3d.geometry.Image(depth_image)

                # Căn chỉnh RGB và Depth lại với nhau
                rgbd_image = o3d.geometry.RGBDImage.create_from_color_and_depth(
                    o3d_color, 
                    o3d_depth, 
                    depth_scale=1000.0, # Đổi từ mm sang hệ mét cho 3D
                    depth_trunc=1.5,    # Chỉ render các vật thể trong cự ly 1.5m (giảm tải CPU/Edge computing)
                    convert_rgb_to_intensity=False
                )

                # Tạo Point Cloud từ ảnh RGB-D
                temp_pcd = o3d.geometry.PointCloud.create_from_rgbd_image(rgbd_image, intrinsic)
                
                # Lật ngược trục Y và Z để Point Cloud không bị lộn ngược (do hệ tọa độ camera khác không gian 3D)
                temp_pcd.transform([[1, 0, 0, 0], [0, -1, 0, 0], [0, 0, -1, 0], [0, 0, 0, 1]])

                # Cập nhật Visualizer
                if is_first_frame:
                    pcd.points = temp_pcd.points
                    pcd.colors = temp_pcd.colors
                    vis.add_geometry(pcd)
                    is_first_frame = False
                else:
                    pcd.points = temp_pcd.points
                    pcd.colors = temp_pcd.colors
                    vis.update_geometry(pcd)
                
                vis.poll_events()
                vis.update_renderer()

                # Hiển thị 2D để đối chiếu
                cv2.imshow('2D RGB Reference', color_frame)

            depth_display = cv2.convertScaleAbs(depth_image, alpha=0.03)
            cv2.imshow('2D Depth Map', cv2.applyColorMap(depth_display, cv2.COLORMAP_JET))

            if cv2.waitKey(1) & 0xFF == ord('q'):
                is_running = False

    except KeyboardInterrupt:
        print("\nĐang đóng an toàn...")
    finally:
        if cap: cap.release()
        if depth_stream: depth_stream.stop()
        if dev: dev.close()
        openni2.unload()
        vis.destroy_window()
        cv2.destroyAllWindows()
        print("Đã giải phóng tài nguyên!")

if __name__ == '__main__':
    main()