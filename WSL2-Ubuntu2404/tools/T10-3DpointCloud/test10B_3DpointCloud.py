import os
import copy
# Khiên chống Crash trên WSL2
os.environ['LIBGL_ALWAYS_SOFTWARE'] = '1'
os.environ['OPENCV_OPENCL_RUNTIME'] = 'disabled'

import cv2
import numpy as np
from openni import openni2
import sys
import open3d as o3d

# Thông số Camera
FX, FY = 570.3, 570.3
CX, CY = 320.0, 240.0

def process_3d_point_cloud(rgb_frames, depth_frames, intrinsic):
    """Hàm xử lý ghép 3D tách biệt khỏi vòng lặp Camera"""
    print("\n[+] Đang xử lý và ghép nối 3D... Vui lòng đợi...")
    
    global_pcd = o3d.geometry.PointCloud()
    current_pose = np.eye(4)
    odo_option = o3d.pipelines.odometry.OdometryOption()
    odo_option.depth_max = 1.5

    prev_rgbd = None
    success_count = 0

    for i in range(len(rgb_frames)):
        o3d_color = o3d.geometry.Image(rgb_frames[i])
        o3d_depth = o3d.geometry.Image(depth_frames[i])
        
        rgbd_image = o3d.geometry.RGBDImage.create_from_color_and_depth(
            o3d_color, o3d_depth, 
            depth_scale=1000.0, depth_trunc=1.5, convert_rgb_to_intensity=False)

        if prev_rgbd is None:
            prev_rgbd = rgbd_image
            global_pcd = o3d.geometry.PointCloud.create_from_rgbd_image(rgbd_image, intrinsic)
            success_count += 1
            continue

        # Tính toán chuyển động
        success, trans_color, _ = o3d.pipelines.odometry.compute_rgbd_odometry(
            rgbd_image, prev_rgbd, intrinsic, np.eye(4),
            o3d.pipelines.odometry.RGBDOdometryJacobianFromHybridTerm(), odo_option)

        if success:
            current_pose = np.dot(current_pose, trans_color)
            new_pcd = o3d.geometry.PointCloud.create_from_rgbd_image(rgbd_image, intrinsic)
            new_pcd.transform(current_pose)
            
            global_pcd += new_pcd
            global_pcd = global_pcd.voxel_down_sample(voxel_size=0.005) # Lọc nhiễu
            prev_rgbd = rgbd_image
            success_count += 1
            
        sys.stdout.write(f"\rTiến độ: {i+1}/{len(rgb_frames)} khung hình (Thành công: {success_count})")
        sys.stdout.flush()

    print("\n[V] Hoàn tất! Đang mở giao diện 3D...")
    
    # Lật trục để không bị ngược
    flip_transform = [[1, 0, 0, 0], [0, -1, 0, 0], [0, 0, -1, 0], [0, 0, 0, 1]]
    global_pcd.transform(flip_transform)
    
    # Bung cửa sổ 3D tĩnh (Cực kỳ ổn định)
    o3d.visualization.draw_geometries([global_pcd], window_name="Ket Qua 3D", width=800, height=600)
    return global_pcd

def main():
    openni2_dir = '/home/beniot-phan/APT_AstraProTest/sdk/OpenNI_2.3.0.86_202210111154_4c8f5aa4_beta6_linux/samples/samples/ThirdParty/OpenNI2/linux/x64'
    try:
        openni2.initialize(openni2_dir)
    except Exception as e:
        print(f"Lỗi khởi tạo: {e}")
        sys.exit(1)

    dev = openni2.Device.open_any()
    depth_stream = dev.create_depth_stream()
    depth_stream.start()

    cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))

    intrinsic = o3d.camera.PinholeCameraIntrinsic(640, 480, FX, FY, CX, CY)
    
    is_scanning = False
    captured_rgb = []
    captured_depth = []

    print("========================================")
    print(" [r] - BẮT ĐẦU GHI HÌNH (Di chuyển chậm quanh vật thể)")
    print(" [t] - DỪNG VÀ BẮT ĐẦU DỰNG 3D")
    print(" [q] - THOÁT")
    print("========================================")

    while True:
        ret, color_frame = cap.read() if cap.isOpened() else (False, None)
        depth_frame = depth_stream.read_frame()
        depth_data = np.frombuffer(depth_frame.get_buffer_as_uint16(), dtype=np.uint16).copy()
        depth_image = depth_data.reshape(depth_frame.height, depth_frame.width)

        if ret and color_frame is not None:
            display_frame = color_frame.copy()

            if is_scanning:
                # Lưu dữ liệu siêu tốc vào RAM
                color_rgb = cv2.cvtColor(color_frame, cv2.COLOR_BGR2RGB)
                captured_rgb.append(color_rgb)
                captured_depth.append(depth_image)
                
                cv2.putText(display_frame, f"DANG GHI: {len(captured_rgb)} Frames", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)

            cv2.imshow('Camera RGB', display_frame)

        cv2.imshow('Camera Depth', cv2.applyColorMap(cv2.convertScaleAbs(depth_image, alpha=0.03), cv2.COLORMAP_JET))

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('r'):
            print("\n[+] BẮT ĐẦU GHI HÌNH!")
            is_scanning = True
            captured_rgb.clear()
            captured_depth.clear()
        elif key == ord('t'):
            if is_scanning and len(captured_rgb) > 0:
                is_scanning = False
                print(f"\n[!] Đã dừng ghi. Tổng số khung hình: {len(captured_rgb)}")
                
                # Gọi hàm dựng 3D (Sẽ chặn luồng camera để dồn toàn bộ CPU cho Open3D)
                final_pcd = process_3d_point_cloud(captured_rgb, captured_depth, intrinsic)
                
                # Lưu file sau khi xem xong
                o3d.io.write_point_cloud("astra_offline_scan.ply", final_pcd)
                print("\n[V] Đã lưu file 'astra_offline_scan.ply'")
                print("\nTrở lại chế độ camera trực tiếp...")

    cap.release()
    depth_stream.stop()
    dev.close()
    openni2.unload()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()