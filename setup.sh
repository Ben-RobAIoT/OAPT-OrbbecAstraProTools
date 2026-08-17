#!/bin/bash
echo "========================================================="
echo " BẮT ĐẦU CÀI ĐẶT MÔI TRƯỜNG CHO ORBBEC ASTRA PRO (LINUX)"
echo "========================================================="

echo "[1/3] Cập nhật hệ thống & cài các công cụ cần thiết (usbutils, fonts...)"
sudo apt update
sudo apt install -y python3-venv linux-tools-virtual hwdata usbutils fonts-dejavu fontconfig libusb-1.0-0

echo "[2/3] Khởi tạo môi trường ảo (venv)..."
python3 -m venv venv

echo "[3/3] Cài đặt các thư viện Python (OpenCV, OpenNI...)"
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt

echo "========================================================="
echo "[+] HOÀN TẤT TUYỆT ĐỐI! Môi trường đã sẵn sàng."
echo "[!] Cách chạy Testbench Đa Luồng:"
echo "    sudo ./venv/bin/python3 03_multithreaded_testbench.py"
echo "========================================================="