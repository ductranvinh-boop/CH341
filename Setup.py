import sys
from cx_Freeze import setup, Executable

# 1. Kê khai đồ tể, xách vở cần lùa vô file cài đặt
build_exe_options = {
    # Mấy thư viện chuẩn có thể khỏi ghi, nhưng để vậy cho chắc cú cũng không sao
    "packages": ["os", "tkinter", "json", "ctypes", "subprocess", "threading", "time", "datetime", "glob"],
    "include_files": [
        "Vie.json",
        "Eng.json",
        "25_26_LIB.json",
        "CH341DLL.DLL",
        "CH341DLLA64.DLL",
        ("CH341PAR", "CH341PAR"), # Hốt trọn ổ thư mục Driver
        "SOP8.ico"
    ]
}

# 2. ÉP UỔNG ĐƯỜNG DẪN CÀI ĐẶT & ĐÓNG MỘC VÔ CONTROL PANEL
bdist_msi_options = {
    # Đưa vô thư mục chuẩn của Windows đặng né vụ đòi quyền Admin cự cãi
    "initial_target_dir": r"C:\Program Files\CH341_TranVinhDuc",
    "install_icon": "SOP8.ico"
}

# 3. Lịnh giấu cái bảng đen thui (console)
base = None
if sys.platform == "win32":
    base = "GUI" # Xài chữ Win32GUI cho nó tương thích tốt nhất với cx_Freeze

# 4. CHỐT HẠ TẠO LỐI TẮT RA DESKTOP VÀ ĐÓNG MỘC TRIỆN
phim_tat_desktop = Executable(
    script="Logic.py",
    base=base,
    target_name="CH341_Programmer.exe",
    icon="SOP8.ico",
    shortcut_name="CH341 Programmer",
    shortcut_dir="DesktopFolder"
)

# 5. Đóng mộc xuất xưởng
setup(
    name="CH341_TranVinhDuc",
    version="1.0",
    description="Công Cụ Điều Khiển CH341 - Trần Vĩnh Đức",
    author="Trần Vĩnh Đức",
    options={
        "build_exe": build_exe_options,
        "bdist_msi": bdist_msi_options
    },
    executables=[phim_tat_desktop]
)