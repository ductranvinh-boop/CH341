import sys
import time
import datetime
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
import json
import glob
import os
import ctypes
import subprocess

from Theme import GiaoDienCH341

CMD_WRITE_ENABLE = 0x06
CMD_WRITE_DISABLE = 0x04
CMD_READ_STATUS_1 = 0x05
CMD_WRITE_STATUS = 0x01
CMD_READ_DATA = 0x03
CMD_PAGE_PROGRAM = 0x02
CMD_SECTOR_ERASE_4K = 0x20
CMD_CHIP_ERASE = 0xC7


class KhoiThucThi:
    def __init__(self):
        self.root = tk.Tk()
        self.kho_ngon_ngu = self.quet_ngon_ngu()
        self.ngon_ngu_hien_tai = self.kho_ngon_ngu.get("Tiếng Việt", {})
        self.gui = GiaoDienCH341(self.root, self.ngon_ngu_hien_tai, trinh_dieu_khien=self)
        self.gui.tao_danh_sach_ngon_ngu(list(self.kho_ngon_ngu.keys()))

        self.ch341_lib = None
        self.du_lieu_bo_dem = "00000000  FF FF FF FF FF FF FF FF  FF FF FF FF FF FF FF FF  |................|\n"
        self.kho_chip = {}

        self.dang_lam_viec = False
        self.cai_dat_toc_do = "nhanh"
        self.cai_dat_kieu_nap = "block"
        self.dung_luong_chip_bytes = 8388608
        self.du_lieu_nhi_phan_goc = bytearray()

        self.lich_su_toc_do = [0] * 50

        self.nap_thu_vien_dll()
        self.khoi_dong_he_thong()

    def nap_thu_vien_dll(self):
        try:
            try:
                self.ch341_lib = ctypes.windll.LoadLibrary("CH341DLLA64.DLL")
            except OSError:
                self.ch341_lib = ctypes.windll.LoadLibrary("CH341DLL.DLL")

            self.ch341_lib.CH341OpenDevice.restype = ctypes.c_void_p
            self.ch341_lib.CH341GetVerIC.restype = ctypes.c_int
            self.ch341_lib.CH341GetDrvVersion.restype = ctypes.c_int

            self.ch341_lib.CH341StreamSPI4.restype = ctypes.c_bool
            self.ch341_lib.CH341StreamSPI4.argtypes = [
                ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_void_p
            ]
        except Exception:
            self.ch341_lib = None

    def quet_ngon_ngu(self):
        du_lieu = {}
        cac_file = glob.glob("*.json")
        for file in cac_file:
            if file in ["Vie.json", "Eng.json"]:
                try:
                    with open(file, 'r', encoding='utf-8-sig') as f:
                        noi_dung = json.load(f)
                        ten = noi_dung.get("ten_ngon_ngu", file)
                        du_lieu[ten] = noi_dung
                except Exception:
                    pass
        return du_lieu

    def xu_ly_chon_ngon_ngu(self, ten_ngon_ngu_chon):
        if ten_ngon_ngu_chon in self.kho_ngon_ngu:
            self.ngon_ngu_hien_tai = self.kho_ngon_ngu[ten_ngon_ngu_chon]
            self.gui.thay_chu_tren_mat(self.ngon_ngu_hien_tai)
            self.gui.hop_thu_bao.delete(1.0, tk.END)
            cau_chao = self.ngon_ngu_hien_tai.get("log_doi_ngon_ngu", f"Đã chuyển sang: {ten_ngon_ngu_chon}")
            self.gui.ghi_log(cau_chao)

    def kiem_tra_ket_noi_ch341(self):
        if self.ch341_lib is None: return "Lỗi DLL"
        try:
            handle = self.ch341_lib.CH341OpenDevice(0)
            if handle == -1 or handle == 0 or handle is None: return "CHƯA CẮM MẠCH"
            ver_ic = self.ch341_lib.CH341GetVerIC(0)
            drv_ver = self.ch341_lib.CH341GetDrvVersion()
            self.ch341_lib.CH341CloseDevice(0)
            return f"000{ver_ic}{drv_ver}"
        except Exception:
            return "Lỗi"

    def tai_thu_vien_chip(self):
        try:
            with open("25_26_LIB.json", "r", encoding="utf-8-sig") as f:
                self.kho_chip = json.load(f)
            danh_sach_hang = ["!ALL"] + list(self.kho_chip.keys())
            self.gui.cap_nhat_danh_sach_hang(danh_sach_hang)
        except Exception as e:
            self.gui.ghi_log(f"[LỖI]: Không đọc được hồ sơ 25_26_LIB.json. Báo trật: {str(e)}")

    def khoi_dong_he_thong(self):
        self.gui.hop_thu_bao.delete(1.0, tk.END)
        trang_thai_phan_cung = self.kiem_tra_ket_noi_ch341()
        self.gui.cap_nhat_so_xe_ri(f"SN:{trang_thai_phan_cung}")
        gio_hien_tai = datetime.datetime.now().strftime("%H:%M:%S")
        log_khoi_dong = self.ngon_ngu_hien_tai.get(
            "log_startup_info",
            "{thoi_gian}: Serial number:{sn}, Programmer firmware version: V1.0 ."
        )
        self.gui.ghi_log(log_khoi_dong.format(thoi_gian=gio_hien_tai, sn=trang_thai_phan_cung))
        self.tai_thu_vien_chip()

    def kiem_tra_da_chon_chip(self):
        ma_chip = self.gui.o_tim_kiem.get().strip()
        if not ma_chip:
            loi_nhac = self.ngon_ngu_hien_tai.get("log_chua_chon_chip",
                                                  "[CẢNH BÁO]: Xin vui lòng chọn lựa linh kiện đặng thao tác.")
            self.gui.ghi_log(loi_nhac)
            return False
        return True

    def xu_ly_bo_dem(self):
        self.gui.mo_cua_so_bo_dem(self.du_lieu_bo_dem)

    def thiet_lap_toc_do(self, toc_do):
        self.cai_dat_toc_do = toc_do

    def thiet_lap_kieu_nap(self, kieu):
        self.cai_dat_kieu_nap = kieu

    def mo_device_manager(self):
        try:
            os.startfile("devmgmt.msc")
        except Exception:
            pass

    def xu_ly_cai_driver(self):
        # Tuyệt chiêu định vị: Phân biệt đang chạy code trần (.py) hay đã ép thành .exe
        if getattr(sys, 'frozen', False):
            # Nếu đã đóng gói cx_Freeze, lấy thư mục gốc chứa file .exe
            thu_muc_goc = os.path.dirname(sys.executable)
        else:
            # Nếu đang xài file .py, lấy thư mục của file code
            thu_muc_goc = os.path.dirname(os.path.abspath(__file__))

        duong_dan_inf = os.path.join(thu_muc_goc, "CH341PAR", "CH341PAR", "CH341WDM.INF")

        if not os.path.exists(duong_dan_inf):
            log_miss = self.ngon_ngu_hien_tai.get("log_install_driver_miss",
                                                  "[LỖI]: Mất tích cái file {file} rồi. Anh coi lại thư mục nghen!")
            self.gui.ghi_log(log_miss.format(file=duong_dan_inf))
            return

        try:
            lenh = ["pnputil.exe", "/add-driver", duong_dan_inf, "/install"]
            # Thêm creationflags=0x08000000 đặng nó giấu cái bảng đen thui lúc chạy lịnh
            ket_qua = subprocess.run(lenh, capture_output=True, text=True, creationflags=0x08000000)

            if ket_qua.returncode == 0:
                log_success = self.ngon_ngu_hien_tai.get("log_install_driver_ok",
                                                         "[THÀNH CÔNG]: Đã nhồi Driver vô Win êm ru!")
                self.gui.ghi_log(log_success)
                log_detail = self.ngon_ngu_hien_tai.get("log_driver_detail", "Chi tiết từ Win: {chi_tiet}")
                self.gui.ghi_log(log_detail.format(chi_tiet=ket_qua.stdout.strip()))
            else:
                loi_chi_tiet = ket_qua.stderr.strip() or ket_qua.stdout.strip()
                log_fail = self.ngon_ngu_hien_tai.get("log_install_driver_fail", "[LỖI WIN]: Báo trật lất: {loi}")
                self.gui.ghi_log(log_fail.format(loi=loi_chi_tiet))
        except Exception as e:
            log_error = self.ngon_ngu_hien_tai.get("log_driver_error", "[LỖI]: Mẻ đồ nghề. Lý do: {loi}")
            self.gui.ghi_log(log_error.format(loi=str(e)))

    def xu_ly_go_driver(self):
        try:
            lenh_ps = "Get-WindowsDriver -Online | Where-Object { $_.OriginalFileName -match 'CH341' } | ForEach-Object { pnputil.exe /delete-driver $_.Driver /uninstall /force }"
            lenh = ["powershell.exe", "-NoProfile", "-Command", lenh_ps]
            ket_qua = subprocess.run(lenh, capture_output=True, text=True, creationflags=0x08000000)

            if ket_qua.returncode == 0:
                log_success = self.ngon_ngu_hien_tai.get("log_uninstall_driver_ok",
                                                         "[THÀNH CÔNG]: Đã nhổ tận rễ Driver CH341 khỏi máy!")
                self.gui.ghi_log(log_success)
            else:
                loi_chi_tiet = ket_qua.stderr.strip() or ket_qua.stdout.strip()
                log_fail = self.ngon_ngu_hien_tai.get("log_uninstall_driver_fail", "[LỖI WIN]: Gỡ không được: {loi}")
                self.gui.ghi_log(log_fail.format(loi=loi_chi_tiet))
        except Exception as e:
            log_error = self.ngon_ngu_hien_tai.get("log_driver_error", "[LỖI]: Mẻ đồ nghề. Lý do: {loi}")
            self.gui.ghi_log(log_error.format(loi=str(e)))

    def _do_ten_chip_tu_ma_hex(self, ma_hex):
        danh_sach_match = []
        for ten_hang, cac_chip in self.kho_chip.items():
            if isinstance(cac_chip, dict):
                for ten_chip, id_chip in cac_chip.items():
                    if id_chip and id_chip.upper() == ma_hex.upper():
                        danh_sach_match.append((ten_hang, ten_chip))
        return danh_sach_match

    def xu_ly_ket_noi(self):
        thoi_gian_hien_tai = datetime.datetime.now().strftime("%H:%M:%S")

        if self.ch341_lib is None:
            self.gui.ghi_log(f"{thoi_gian_hien_tai}: [LỖI]: Chưa nạp được thư viện DLL CH341.")
            return

        handle = self.ch341_lib.CH341OpenDevice(0)
        if not handle or handle == -1:
            self.gui.ghi_log(f"{thoi_gian_hien_tai}: [LỖI]: Không mở được mạch CH341. Coi lại cáp tiếp xúc.")
            return

        try:
            che_do = 0x80 if getattr(self, 'cai_dat_toc_do', 'nhanh') == "nhanh" else 0x82
            self.ch341_lib.CH341SetStream(0, che_do)

            bo_dem = (ctypes.c_ubyte * 4)(0x9F, 0x00, 0x00, 0x00)
            thanh_cong = self.ch341_lib.CH341StreamSPI4(0, 0x80, 4, ctypes.cast(bo_dem, ctypes.c_void_p))

            if thanh_cong:
                ma_hex = f"{bo_dem[1]:02X}{bo_dem[2]:02X}{bo_dem[3]:02X}"
                if ma_hex in ["FFFFFF", "000000", "FF00FF"]:
                    tieu_de = self.ngon_ngu_hien_tai.get("msg_title_loi_vat_ly", "Cảnh báo - Lỗi vật lý")
                    thong_bao = self.ngon_ngu_hien_tai.get("msg_chua_gan_chip", "Chưa gắn chip, cắm ngược chiều...")
                    messagebox.showwarning(tieu_de, thong_bao)
                    self.gui.ghi_log(f"{thoi_gian_hien_tai}: [THẤT BẠI]: Không tìm thấy IC...")
                else:
                    danh_sach_match = self._do_ten_chip_tu_ma_hex(ma_hex)

                    if danh_sach_match:
                        so_luong = len(danh_sach_match)
                        ten_hang, ten_chip = danh_sach_match[0]

                        import re
                        mb_match = re.search(r'\((\d+)[MK]B\)', ten_chip)
                        mbytes = int(mb_match.group(1)) if mb_match else 0
                        mbits = mbytes * 8

                        if mbytes > 0:
                            if "MB" in ten_chip.upper():
                                self.dung_luong_chip_bytes = mbytes * 1024 * 1024
                            else:
                                self.dung_luong_chip_bytes = mbytes * 1024

                        ten_chip_ngan = ten_chip.split(' ')[0]

                        log_match = self.ngon_ngu_hien_tai.get("log_auto_match",
                                                               "{thoi_gian}: Auto identified {count} ID...")
                        log_selected = self.ngon_ngu_hien_tai.get("log_chip_selected",
                                                                  "{thoi_gian}: The currently selected...")

                        self.gui.ghi_log(log_match.format(thoi_gian=thoi_gian_hien_tai, count=so_luong))
                        self.gui.ghi_log(
                            log_selected.format(thoi_gian=thoi_gian_hien_tai, ten_chip=ten_chip_ngan, mbits=mbits,
                                                mbytes=mbytes))

                        cac_hang = self.gui.ds_hang.get(0, tk.END)
                        if ten_hang in cac_hang:
                            vi_tri_hang = cac_hang.index(ten_hang)
                            self.gui.ds_hang.selection_clear(0, tk.END)
                            self.gui.ds_hang.selection_set(vi_tri_hang)
                            self.gui.ds_hang.see(vi_tri_hang)
                            self.xu_ly_chon_hang()

                            cac_ma = self.gui.ds_ma.get(0, tk.END)
                            for vi_tri_ma, ma_trong_list in enumerate(cac_ma):
                                if ten_chip_ngan in ma_trong_list:
                                    self.gui.ds_ma.selection_clear(0, tk.END)
                                    self.gui.ds_ma.selection_set(vi_tri_ma)
                                    self.gui.ds_ma.see(vi_tri_ma)
                                    self.gui.o_tim_kiem.set(ma_trong_list)
                                    break
                    else:
                        self.gui.ghi_log(f"{thoi_gian_hien_tai}: Unrecognized JEDEC ID: {ma_hex}")
                        self.gui.o_tim_kiem.set(ma_hex)
            else:
                self.gui.ghi_log(f"{thoi_gian_hien_tai}: [LỖI]: Giao tiếp SPI rớt đài.")
        finally:
            self.ch341_lib.CH341CloseDevice(0)

    def _gui_linh_wren(self):
        if not self.ch341_lib: return False
        bo_dem = (ctypes.c_ubyte * 1)(CMD_WRITE_ENABLE)
        return self.ch341_lib.CH341StreamSPI4(0, 0x80, 1, ctypes.cast(bo_dem, ctypes.c_void_p))

    def _doi_chip_ranh_roi_wip(self, timeout=2.0):
        if not self.ch341_lib: return False
        bo_dem = (ctypes.c_ubyte * 2)()
        thoi_gian_bat_dau = time.time()
        thoi_gian_nghi = 0.0001 if getattr(self, 'cai_dat_toc_do', 'nhanh') == "nhanh" else 0.002

        while (time.time() - thoi_gian_bat_dau) < timeout:
            if not self.dang_lam_viec: return False
            bo_dem[0] = CMD_READ_STATUS_1
            bo_dem[1] = 0x00
            self.ch341_lib.CH341StreamSPI4(0, 0x80, 2, ctypes.cast(bo_dem, ctypes.c_void_p))
            if (bo_dem[1] & 0x01) == 0:
                return True
            time.sleep(thoi_gian_nghi)
        return False

    def _read_bios_block(self, address, length):
        if not self.ch341_lib or length <= 0: return None
        du_lieu_truyen = bytes(
            [CMD_READ_DATA, (address >> 16) & 0xFF, (address >> 8) & 0xFF, address & 0xFF]) + b'\xFF' * length
        bo_dem = (ctypes.c_ubyte * len(du_lieu_truyen)).from_buffer_copy(du_lieu_truyen)
        if self.ch341_lib.CH341StreamSPI4(0, 0x80, len(du_lieu_truyen), ctypes.cast(bo_dem, ctypes.c_void_p)):
            return bytearray(bo_dem)[4:]
        return None

    def _write_bios_page(self, address, data_256bytes):
        if all(b == 0xFF for b in data_256bytes): return True
        if not self._gui_linh_wren(): return False
        do_dai = len(data_256bytes)
        bo_dem = (ctypes.c_ubyte * (4 + do_dai))()
        bo_dem[0] = CMD_PAGE_PROGRAM
        bo_dem[1] = (address >> 16) & 0xFF
        bo_dem[2] = (address >> 8) & 0xFF
        bo_dem[3] = address & 0xFF
        for i in range(do_dai): bo_dem[4 + i] = data_256bytes[i]
        if self.ch341_lib.CH341StreamSPI4(0, 0x80, 4 + do_dai, ctypes.cast(bo_dem, ctypes.c_void_p)):
            return self._doi_chip_ranh_roi_wip(timeout=0.5)
        return False

    def _erase_bios_sector(self, address):
        if not self._gui_linh_wren(): return False
        bo_dem = (ctypes.c_ubyte * 4)(CMD_SECTOR_ERASE_4K, (address >> 16) & 0xFF, (address >> 8) & 0xFF,
                                      address & 0xFF)
        if self.ch341_lib.CH341StreamSPI4(0, 0x80, 4, ctypes.cast(bo_dem, ctypes.c_void_p)):
            return self._doi_chip_ranh_roi_wip(timeout=1.0)
        return False

    def xu_ly_doc(self):
        if not self.kiem_tra_da_chon_chip(): return
        tg = datetime.datetime.now().strftime('%H:%M:%S')
        msg = self.ngon_ngu_hien_tai.get("log_dang_doc", "{thoi_gian}: Đang đọc ROM trong BIOS...").replace(
            "{thoi_gian}", tg)
        self.gui.ghi_log(msg)
        threading.Thread(target=self._thuc_thi_doc_hardcore, daemon=True).start()

    def _thuc_thi_doc_hardcore(self):
        self.dang_lam_viec = True
        self.gui.cap_nhat_tien_trinh(0)
        handle = self.ch341_lib.CH341OpenDevice(0)
        tg = datetime.datetime.now().strftime('%H:%M:%S')

        if not handle or handle == -1:
            msg = self.ngon_ngu_hien_tai.get("log_loi_ket_noi_mach",
                                             "{thoi_gian}: [LỖI]: Không mở được mạch CH341.").replace("{thoi_gian}", tg)
            self.gui.ghi_log(msg)
            self.dang_lam_viec = False
            return

        try:
            self.ch341_lib.CH341SetStream(0, 0x80)
            tong_kich_thuoc = self.dung_luong_chip_bytes

            kich_thuoc_cuc = 2048
            du_lieu_doc_duoc = bytearray()
            phan_tram_cu = -1
            loi_doc = False

            thoi_gian_bat_dau_do = time.time()
            so_byte_da_nhao = 0

            for dia_chi in range(0, tong_kich_thuoc, kich_thuoc_cuc):
                if not self.dang_lam_viec: break

                do_dai_doc = min(kich_thuoc_cuc, tong_kich_thuoc - dia_chi)
                khuc_doc = self._read_bios_block(dia_chi, do_dai_doc)

                if khuc_doc is not None:
                    du_lieu_doc_duoc.extend(khuc_doc)

                    so_byte_da_nhao += len(khuc_doc)
                    thoi_gian_hien_tai = time.time()
                    khoang_tg = thoi_gian_hien_tai - thoi_gian_bat_dau_do

                    if khoang_tg >= 0.2:
                        toc_do = (so_byte_da_nhao / 1024) / khoang_tg
                        self.root.after(0, lambda t=toc_do: self.cap_nhat_do_thi(t))
                        thoi_gian_bat_dau_do = thoi_gian_hien_tai
                        so_byte_da_nhao = 0

                else:
                    loi_doc = True
                    break

                phan_tram = int((dia_chi + do_dai_doc) / tong_kich_thuoc * 100)
                if phan_tram != phan_tram_cu:
                    self.gui.cap_nhat_tien_trinh(phan_tram)
                    phan_tram_cu = phan_tram

            if self.dang_lam_viec:
                tg = datetime.datetime.now().strftime('%H:%M:%S')
                if loi_doc:
                    dc_hex = f"{dia_chi:06X}"
                    msg = self.ngon_ngu_hien_tai.get("log_loi_doc_dia_chi",
                                                     "{thoi_gian}: [LỖI]: Mất kết nối lúc đang đọc ở địa chỉ {dia_chi}.").replace(
                        "{thoi_gian}", tg).replace("{dia_chi}", dc_hex)
                    self.gui.ghi_log(msg)
                else:
                    chip_trong_rong = len(du_lieu_doc_duoc) > 0 and all(byte == 0xFF for byte in du_lieu_doc_duoc)
                    if chip_trong_rong:
                        msg = self.ngon_ngu_hien_tai.get("log_bios_trong_rong",
                                                         "{thoi_gian}: [THÔNG TIN]: BIOS trống rỗng.").replace(
                            "{thoi_gian}", tg)
                        self.gui.ghi_log(msg)
                    else:
                        msg = self.ngon_ngu_hien_tai.get("log_doc_thanh_cong",
                                                         "{thoi_gian}: [THÀNH CÔNG]: Đọc ROM xong xuôi!").replace(
                            "{thoi_gian}", tg)
                        self.gui.ghi_log(msg)

                    self.root.after(0, lambda: self.cap_nhat_do_thi(0))

                    self.du_lieu_nhi_phan_goc = du_lieu_doc_duoc
                    self.du_lieu_bo_dem = self._dich_nhi_phan_sang_hex(du_lieu_doc_duoc[:65536])

                    if hasattr(self.gui,
                               'cua_so_bo_dem') and self.gui.cua_so_bo_dem is not None and self.gui.cua_so_bo_dem.winfo_exists():
                        self.gui._dien_du_lieu_bo_dem(self.du_lieu_bo_dem)
            else:
                tg = datetime.datetime.now().strftime('%H:%M:%S')
                msg = self.ngon_ngu_hien_tai.get("log_dung_doc", "{thoi_gian}: [THÔNG BÁO]: Đã dừng đọc.").replace(
                    "{thoi_gian}", tg)
                self.gui.ghi_log(msg)
        finally:
            self.ch341_lib.CH341CloseDevice(0)
            self.dang_lam_viec = False
            self.gui.cap_nhat_tien_trinh(0)

    def xu_ly_luu(self):
        tg = datetime.datetime.now().strftime('%H:%M:%S')
        if not hasattr(self, 'du_lieu_nhi_phan_goc') or not self.du_lieu_nhi_phan_goc:
            msg = self.ngon_ngu_hien_tai.get("log_chua_co_du_lieu",
                                             "{thoi_gian}: [CẢNH BÁO]: Chưa có dữ liệu, hãy Bấm 'Đọc' trước!").replace(
                "{thoi_gian}", tg)
            self.gui.ghi_log(msg)
            return

        duong_dan = filedialog.asksaveasfilename(title="Lưu hồ sơ ROM vô máy", defaultextension=".bin",
                                                 filetypes=[("Hồ sơ BIN", "*.bin"), ("Tất cả", "*.*")])
        if duong_dan:
            with open(duong_dan, 'wb') as f: f.write(self.du_lieu_nhi_phan_goc)
            msg = self.ngon_ngu_hien_tai.get("log_luu_thanh_cong",
                                             "Lịnh: Đã chép hồ sơ an toàn xuống: {duong_dan}").replace("{duong_dan}",
                                                                                                       duong_dan)
            self.gui.ghi_log(msg)

    def xu_ly_mo_file(self):
        # Châm thêm cái đuôi .cap vô danh sách chọn lựa
        duong_dan = filedialog.askopenfilename(
            filetypes=[("Hồ sơ BIN", "*.bin"), ("Hồ sơ ROM", "*.rom"), ("Hồ sơ HEX", "*.hex"),
                       ("Hồ sơ CAP (Asus)", "*.cap"), ("Tất cả", "*.*")])
        if duong_dan:
            self.duong_dan_file = duong_dan
            tg = datetime.datetime.now().strftime('%H:%M:%S')

            # TUYỆT CHIÊU CẠO VỎ: Gài biến lưu lại độ dài vỏ bọc cần cắt
            if duong_dan.lower().endswith('.cap'):
                self.offset_file = 2048
                msg = self.ngon_ngu_hien_tai.get("log_da_nap_cap",
                                                 "{thoi_gian}: Đã nạp file Asus CAP: {duong_dan}\n-> Giải mã hoàn tất!").replace(
                    "{thoi_gian}", tg).replace("{duong_dan}", duong_dan)
            else:
                self.offset_file = 0  # Đồ trần trụi thì để nguyên số 0
                msg = self.ngon_ngu_hien_tai.get("log_da_nap_file",
                                                 "{thoi_gian}: Đã nạp hồ sơ vô bộ đệm: {duong_dan}").replace(
                    "{thoi_gian}", tg).replace("{duong_dan}", duong_dan)

            self.gui.ghi_log(msg)

            def nhiem_vu_doc_ngam():
                try:
                    with open(duong_dan, 'rb') as f:
                        f.seek(self.offset_file)  # Chọt dao lam vô đúng cái khớp cần cắt
                        self.du_lieu_bo_dem = self._dich_nhi_phan_sang_hex(
                            f.read(65536))  # Đọc mồi 64KB rải lên giao diện
                except Exception as e:
                    msg_loi = self.ngon_ngu_hien_tai.get("log_loi_mo_file", "-> [LỖI FILE]: {loi}").replace("{loi}",
                                                                                                            str(e))
                    self.gui.ghi_log(msg_loi)

            threading.Thread(target=nhiem_vu_doc_ngam, daemon=True).start()

    def xu_ly_ghi(self):
        if not self.kiem_tra_da_chon_chip(): return
        tg = datetime.datetime.now().strftime('%H:%M:%S')
        if not hasattr(self, 'duong_dan_file') or not self.duong_dan_file:
            msg = self.ngon_ngu_hien_tai.get("log_chua_chon_file_ghi",
                                             "{thoi_gian}: [CẢNH BÁO]: Chưa chọn file!").replace("{thoi_gian}", tg)
            self.gui.ghi_log(msg)
            return
        threading.Thread(target=self._thuc_thi_ghi_hardcore, daemon=True).start()

    def _thuc_thi_ghi_hardcore(self):
        self.dang_lam_viec = True
        self.gui.cap_nhat_tien_trinh(0)

        tg = datetime.datetime.now().strftime('%H:%M:%S')
        msg = self.ngon_ngu_hien_tai.get("log_dang_ghi", "{thoi_gian}: Đang nạp ROM vào BIOS, xin chờ...").replace(
            "{thoi_gian}", tg)
        self.gui.ghi_log(msg)

        handle = self.ch341_lib.CH341OpenDevice(0)
        if not handle or handle == -1:
            msg = self.ngon_ngu_hien_tai.get("log_loi_cap_chua_an", "{thoi_gian}: [LỖI]: Cáp chưa ăn.").replace(
                "{thoi_gian}", tg)
            self.gui.ghi_log(msg)
            self.dang_lam_viec = False
            return

        try:
            with open(self.duong_dan_file, 'rb') as f:
                # Ép con trỏ nhảy qua cái mớ vỏ bọc (nếu có) trước khi hút dữ liệu
                f.seek(getattr(self, 'offset_file', 0))
                du_lieu_file = f.read()

            tong_kich_thuoc = len(du_lieu_file)

            kieu_nap = getattr(self, 'cai_dat_kieu_nap', 'block')
            if kieu_nap == 'bit':
                msg = self.ngon_ngu_hien_tai.get("log_che_do_nap_bit",
                                                 "{thoi_gian}: -> Đang xài chế độ nạp Từng bit/Byte. Sẽ rùa bò lắm nghen anh, ráng chờ!").replace(
                    "{thoi_gian}", tg)
                self.gui.ghi_log(msg)
            else:
                kich_thuoc_trang = 256

            self.ch341_lib.CH341SetStream(0, 0x80 if getattr(self, 'cai_dat_toc_do', 'nhanh') == "nhanh" else 0x82)

            loi_ghi = False
            phan_tram_cu = -1

            thoi_gian_bat_dau_do = time.time()
            so_byte_da_nhao = 0

            for dia_chi in range(0, tong_kich_thuoc, kich_thuoc_trang):
                if not self.dang_lam_viec: break

                khuc_du_lieu = du_lieu_file[dia_chi: dia_chi + kich_thuoc_trang]
                thanh_cong = self._write_bios_page(dia_chi, khuc_du_lieu)

                so_byte_da_nhao += len(khuc_du_lieu)
                thoi_gian_hien_tai = time.time()
                khoang_tg = thoi_gian_hien_tai - thoi_gian_bat_dau_do

                if khoang_tg >= 0.2:
                    toc_do = (so_byte_da_nhao / 1024) / khoang_tg
                    self.root.after(0, lambda t=toc_do: self.cap_nhat_do_thi(t))
                    thoi_gian_bat_dau_do = thoi_gian_hien_tai
                    so_byte_da_nhao = 0

                if not thanh_cong and not all(b == 0xFF for b in khuc_du_lieu):
                    dc_hex = f"{dia_chi:06X}"
                    msg = self.ngon_ngu_hien_tai.get("log_ket_rac_ghi",
                                                     "{thoi_gian}: [LỖI]: Kẹt rác ở trang {dia_chi}. Anh nhớ Xóa (Erase) chip trước khi Ghi nghen!").replace(
                        "{thoi_gian}", tg).replace("{dia_chi}", dc_hex)
                    self.gui.ghi_log(msg)
                    loi_ghi = True
                    break

                phan_tram = int((dia_chi + kich_thuoc_trang) / tong_kich_thuoc * 100)
                if phan_tram != phan_tram_cu:
                    self.gui.cap_nhat_tien_trinh(phan_tram)
                    phan_tram_cu = phan_tram

            if self.dang_lam_viec:
                tg = datetime.datetime.now().strftime('%H:%M:%S')
                if loi_ghi:
                    msg = self.ngon_ngu_hien_tai.get("log_ghi_that_bai",
                                                     "{thoi_gian}: [THẤT BẠI]: Quá trình nạp đứt gánh, chưa vô hết file!").replace(
                        "{thoi_gian}", tg)
                    self.gui.ghi_log(msg)
                else:
                    msg = self.ngon_ngu_hien_tai.get("log_ghi_thanh_cong",
                                                     "{thoi_gian}: [THÀNH CÔNG]: Đã nạp xong file!").replace(
                        "{thoi_gian}", tg)
                    self.gui.ghi_log(msg)
                    self.root.after(0, lambda: self.cap_nhat_do_thi(0))

        except Exception as e:
            tg = datetime.datetime.now().strftime('%H:%M:%S')
            msg = self.ngon_ngu_hien_tai.get("log_loi_may_bao", "{thoi_gian}: [LỖI]: Máy báo trật lất: {loi}").replace(
                "{thoi_gian}", tg).replace("{loi}", str(e))
            self.gui.ghi_log(msg)
        finally:
            self.ch341_lib.CH341CloseDevice(0)
            self.dang_lam_viec = False
            self.gui.cap_nhat_tien_trinh(0)

    def xu_ly_xoa(self):
        if not self.kiem_tra_da_chon_chip(): return
        tg = datetime.datetime.now().strftime('%H:%M:%S')
        msg = self.ngon_ngu_hien_tai.get("log_dang_xoa", "{thoi_gian}: Đang xóa,xin chờ...").replace("{thoi_gian}", tg)
        self.gui.ghi_log(msg)
        threading.Thread(target=self._thuc_thi_xoa_hardcore, daemon=True).start()

    def _thuc_thi_xoa_hardcore(self):
        self.dang_lam_viec = True
        self.gui.cap_nhat_tien_trinh(0)
        handle = self.ch341_lib.CH341OpenDevice(0)
        tg = datetime.datetime.now().strftime('%H:%M:%S')

        if not handle or handle == -1:
            msg = self.ngon_ngu_hien_tai.get("log_loi_ket_noi_mach", "{thoi_gian}: [LỖI]: Mất kết nối mạch.").replace(
                "{thoi_gian}", tg)
            self.gui.ghi_log(msg)
            self.dang_lam_viec = False
            return

        try:
            self.ch341_lib.CH341SetStream(0, 0x80 if getattr(self, 'cai_dat_toc_do', 'nhanh') == "nhanh" else 0x82)
            tong_kich_thuoc = self.dung_luong_chip_bytes
            kich_thuoc_sector = 4096
            loi_xoa = False
            phan_tram_cu = -1

            for dia_chi in range(0, tong_kich_thuoc, kich_thuoc_sector):
                if not self.dang_lam_viec: break

                thanh_cong = self._erase_bios_sector(dia_chi)

                if not thanh_cong:
                    dc_hex = f"{dia_chi:06X}"
                    msg = self.ngon_ngu_hien_tai.get("log_loi_xoa_sector",
                                                     "{thoi_gian}: [LỖI]: Vấp cục đá ở sector {dia_chi}. Xóa thất bại!").replace(
                        "{thoi_gian}", tg).replace("{dia_chi}", dc_hex)
                    self.gui.ghi_log(msg)
                    loi_xoa = True
                    break

                phan_tram = int((dia_chi + kich_thuoc_sector) / tong_kich_thuoc * 100)
                if phan_tram != phan_tram_cu:
                    self.gui.cap_nhat_tien_trinh(phan_tram)
                    phan_tram_cu = phan_tram

            if self.dang_lam_viec:
                tg = datetime.datetime.now().strftime('%H:%M:%S')
                if loi_xoa:
                    msg = self.ngon_ngu_hien_tai.get("log_xoa_that_bai",
                                                     "{thoi_gian}: [THẤT BẠI]: Chip chưa sạch, dọn rác đứt gánh!").replace(
                        "{thoi_gian}", tg)
                    self.gui.ghi_log(msg)
                else:
                    msg = self.ngon_ngu_hien_tai.get("log_xoa_thanh_cong",
                                                     "{thoi_gian}: [THÀNH CÔNG]: Đã xóa xong").replace("{thoi_gian}",
                                                                                                       tg)
                    self.gui.ghi_log(msg)
        except Exception as e:
            tg = datetime.datetime.now().strftime('%H:%M:%S')
            msg = self.ngon_ngu_hien_tai.get("log_loi_xoa_rom",
                                             "{thoi_gian}: [LỖI]: Không xóa được rom: {loi}").replace("{thoi_gian}",
                                                                                                      tg).replace(
                "{loi}", str(e))
            self.gui.ghi_log(msg)
        finally:
            self.ch341_lib.CH341CloseDevice(0)
            self.dang_lam_viec = False
            self.gui.cap_nhat_tien_trinh(0)

    def xu_ly_kiem_tra_trong(self):
        if not self.kiem_tra_da_chon_chip(): return
        tg = datetime.datetime.now().strftime('%H:%M:%S')
        msg = self.ngon_ngu_hien_tai.get("log_dang_kiem_trong",
                                         "{thoi_gian}: Đang rà soát ROM có trống (Blank) không...").replace(
            "{thoi_gian}", tg)
        self.gui.ghi_log(msg)
        threading.Thread(target=self._thuc_thi_kiem_tra_trong_hardcore, daemon=True).start()

    def _thuc_thi_kiem_tra_trong_hardcore(self):
        self.dang_lam_viec = True
        self.gui.cap_nhat_tien_trinh(0)
        handle = self.ch341_lib.CH341OpenDevice(0)
        tg = datetime.datetime.now().strftime('%H:%M:%S')

        if not handle or handle == -1:
            msg = self.ngon_ngu_hien_tai.get("log_loi_ket_noi_mach", "{thoi_gian}: [LỖI]: Mất kết nối mạch.").replace(
                "{thoi_gian}", tg)
            self.gui.ghi_log(msg)
            self.dang_lam_viec = False
            return

        try:
            self.ch341_lib.CH341SetStream(0, 0x80)
            tong_kich_thuoc = self.dung_luong_chip_bytes

            kich_thuoc_cuc = 2048
            phan_tram_cu = -1
            co_rac = False
            dia_chi_co_rac = 0

            for dia_chi in range(0, tong_kich_thuoc, kich_thuoc_cuc):
                if not self.dang_lam_viec: break

                do_dai_doc = min(kich_thuoc_cuc, tong_kich_thuoc - dia_chi)
                khuc_doc = self._read_bios_block(dia_chi, do_dai_doc)

                if khuc_doc is None:
                    dc_hex = f"{dia_chi:06X}"
                    msg = self.ngon_ngu_hien_tai.get("log_loi_doc_dia_chi",
                                                     "{thoi_gian}: [LỖI]: Mất kết nối lúc đọc ở {dia_chi}.").replace(
                        "{thoi_gian}", tg).replace("{dia_chi}", dc_hex)
                    self.gui.ghi_log(msg)
                    break

                if not all(b == 0xFF for b in khuc_doc):
                    co_rac = True
                    for i, b in enumerate(khuc_doc):
                        if b != 0xFF:
                            dia_chi_co_rac = dia_chi + i
                            break
                    dc_hex_rac = f"{dia_chi_co_rac:06X}"
                    msg = self.ngon_ngu_hien_tai.get("log_bios_khong_trong",
                                                     "{thoi_gian}: [THẤT BẠI]: Bios không trống! Còn dữ liệu tại địa chỉ {dia_chi}.").replace(
                        "{thoi_gian}", tg).replace("{dia_chi}", dc_hex_rac)
                    self.gui.ghi_log(msg)
                    break

                phan_tram = int((dia_chi + do_dai_doc) / tong_kich_thuoc * 100)
                if phan_tram != phan_tram_cu:
                    self.gui.cap_nhat_tien_trinh(phan_tram)
                    phan_tram_cu = phan_tram

            if self.dang_lam_viec:
                if not co_rac and khuc_doc is not None:
                    tg = datetime.datetime.now().strftime('%H:%M:%S')
                    msg = self.ngon_ngu_hien_tai.get("log_bios_trong_rong",
                                                     "{thoi_gian}: [THÀNH CÔNG]: IC hoàn toàn trống rỗng (Blank), sạch bách!").replace(
                        "{thoi_gian}", tg)
                    self.gui.ghi_log(msg)
        except Exception as e:
            tg = datetime.datetime.now().strftime('%H:%M:%S')
            msg = self.ngon_ngu_hien_tai.get("log_loi_may_bao", "{thoi_gian}: [LỖI]: Máy báo trật lất: {loi}").replace(
                "{thoi_gian}", tg).replace("{loi}", str(e))
            self.gui.ghi_log(msg)
        finally:
            self.ch341_lib.CH341CloseDevice(0)
            self.dang_lam_viec = False
            self.gui.cap_nhat_tien_trinh(0)

    def xu_ly_bao_ve(self):
        if not self.kiem_tra_da_chon_chip(): return
        tg = datetime.datetime.now().strftime('%H:%M:%S')
        msg = self.ngon_ngu_hien_tai.get("log_dang_khoa", "{thoi_gian}: Đang khóa (Protect) chip...").replace(
            "{thoi_gian}", tg)
        self.gui.ghi_log(msg)
        threading.Thread(target=self._thuc_thi_bao_ve_hardcore, args=(True,), daemon=True).start()

    def xu_ly_huy_bao_ve(self):
        if not self.kiem_tra_da_chon_chip(): return
        tg = datetime.datetime.now().strftime('%H:%M:%S')
        msg = self.ngon_ngu_hien_tai.get("log_dang_mo_khoa", "{thoi_gian}: Đang mở khóa (Unprotect) chip...").replace(
            "{thoi_gian}", tg)
        self.gui.ghi_log(msg)
        threading.Thread(target=self._thuc_thi_bao_ve_hardcore, args=(False,), daemon=True).start()

    def _thuc_thi_bao_ve_hardcore(self, la_khoa):
        self.dang_lam_viec = True
        self.gui.cap_nhat_tien_trinh(0)
        handle = self.ch341_lib.CH341OpenDevice(0)
        tg = datetime.datetime.now().strftime('%H:%M:%S')

        if not handle or handle == -1:
            msg = self.ngon_ngu_hien_tai.get("log_loi_ket_noi_mach", "{thoi_gian}: [LỖI]: Mất kết nối mạch.").replace(
                "{thoi_gian}", tg)
            self.gui.ghi_log(msg)
            self.dang_lam_viec = False
            return

        try:
            self.ch341_lib.CH341SetStream(0, 0x80 if getattr(self, 'cai_dat_toc_do', 'nhanh') == "nhanh" else 0x82)

            if not self._gui_linh_wren():
                msg = self.ngon_ngu_hien_tai.get("log_loi_wren",
                                                 "{thoi_gian}: [LỖI]: Không mở khóa mỏ hàn (WREN) được.").replace(
                    "{thoi_gian}", tg)
                self.gui.ghi_log(msg)
                return

            gia_tri_status = 0x1C if la_khoa else 0x00

            bo_dem = (ctypes.c_ubyte * 2)(CMD_WRITE_STATUS, gia_tri_status)
            thanh_cong = self.ch341_lib.CH341StreamSPI4(0, 0x80, 2, ctypes.cast(bo_dem, ctypes.c_void_p))

            if thanh_cong and self._doi_chip_ranh_roi_wip(timeout=1.0):
                self.gui.cap_nhat_tien_trinh(100)
                tg = datetime.datetime.now().strftime('%H:%M:%S')
                if la_khoa:
                    msg = self.ngon_ngu_hien_tai.get("log_khoa_thanh_cong",
                                                     "{thoi_gian}: [THÀNH CÔNG]: Đã chốt hạ các bit BP. Chip bị khóa cứng!").replace(
                        "{thoi_gian}", tg)
                    self.gui.ghi_log(msg)
                else:
                    msg = self.ngon_ngu_hien_tai.get("log_mo_khoa_thanh_cong",
                                                     "{thoi_gian}: [THÀNH CÔNG]: Đã xả cảng Status Register. Chip cho phép Ghi/Xóa vô tư!").replace(
                        "{thoi_gian}", tg)
                    self.gui.ghi_log(msg)
            else:
                msg = self.ngon_ngu_hien_tai.get("log_loi_status_reg",
                                                 "{thoi_gian}: [THẤT BẠI]: Can thiệp Status Register đứt gánh giữa chừng.").replace(
                    "{thoi_gian}", tg)
                self.gui.ghi_log(msg)

        except Exception as e:
            tg = datetime.datetime.now().strftime('%H:%M:%S')
            msg = self.ngon_ngu_hien_tai.get("log_loi_may_bao", "{thoi_gian}: [LỖI]: Máy báo trật lất: {loi}").replace(
                "{thoi_gian}", tg).replace("{loi}", str(e))
            self.gui.ghi_log(msg)
        finally:
            self.ch341_lib.CH341CloseDevice(0)
            self.dang_lam_viec = False
            self.gui.cap_nhat_tien_trinh(0)

    def xu_ly_huy(self):
        if self.dang_lam_viec:
            msg = self.ngon_ngu_hien_tai.get("log_huy_tien_trinh",
                                             "Lịnh: Đã bóp thắng cái rụp! Dừng khẩn cấp tiến trình (Cancel).")
            self.gui.ghi_log(msg)
            self.dang_lam_viec = False

    def xu_ly_so_sanh(self):
        if not self.kiem_tra_da_chon_chip(): return
        tg = datetime.datetime.now().strftime('%H:%M:%S')
        if not hasattr(self, 'duong_dan_file') or not self.duong_dan_file:
            msg = self.ngon_ngu_hien_tai.get("log_chua_chon_file_so_sanh",
                                             "{thoi_gian}: [CẢNH BÁO]: Chưa có chọn file đặng đem ra đối chiếu!").replace(
                "{thoi_gian}", tg)
            self.gui.ghi_log(msg)
            return

        msg = self.ngon_ngu_hien_tai.get("log_dang_so_sanh",
                                         "{thoi_gian}: Đang đối chiếu (Verify) mã Hex giữa file và ruột ROM...").replace(
            "{thoi_gian}", tg)
        self.gui.ghi_log(msg)
        threading.Thread(target=self._thuc_thi_so_sanh_hardcore, daemon=True).start()

    def _thuc_thi_so_sanh_hardcore(self):
        self.dang_lam_viec = True
        self.gui.cap_nhat_tien_trinh(0)
        handle = self.ch341_lib.CH341OpenDevice(0)
        tg = datetime.datetime.now().strftime('%H:%M:%S')

        if not handle or handle == -1:
            msg = self.ngon_ngu_hien_tai.get("log_loi_ket_noi_mach", "{thoi_gian}: [LỖI]: Mất kết nối mạch.").replace(
                "{thoi_gian}", tg)
            self.gui.ghi_log(msg)
            self.dang_lam_viec = False
            return

        try:
            with open(self.duong_dan_file, 'rb') as f:
                f.seek(getattr(self, 'offset_file', 0)) # Bạt vỏ bọc trước khi đem lên bàn cân
                du_lieu_file = f.read()

            tong_kich_thuoc = len(du_lieu_file)

            if tong_kich_thuoc > self.dung_luong_chip_bytes:
                msg = self.ngon_ngu_hien_tai.get("log_file_bu_hon_rom",
                                                 "{thoi_gian}: [CẢNH BÁO]: File bự hơn con ROM, chỉ rà soát khúc đầu!").replace(
                    "{thoi_gian}", tg)
                self.gui.ghi_log(msg)
                tong_kich_thuoc = self.dung_luong_chip_bytes

            self.ch341_lib.CH341SetStream(0, 0x80)
            kich_thuoc_cuc = 2048
            phan_tram_cu = -1
            loi_so_sanh = False

            for dia_chi in range(0, tong_kich_thuoc, kich_thuoc_cuc):
                if not self.dang_lam_viec: break

                do_dai_doc = min(kich_thuoc_cuc, tong_kich_thuoc - dia_chi)
                khuc_doc = self._read_bios_block(dia_chi, do_dai_doc)

                if khuc_doc is None:
                    dc_hex = f"{dia_chi:06X}"
                    msg = self.ngon_ngu_hien_tai.get("log_loi_doc_dia_chi",
                                                     "{thoi_gian}: [LỖI]: Mất kết nối lúc đọc ở {dia_chi}.").replace(
                        "{thoi_gian}", tg).replace("{dia_chi}", dc_hex)
                    self.gui.ghi_log(msg)
                    loi_so_sanh = True
                    break

                khuc_file = du_lieu_file[dia_chi: dia_chi + do_dai_doc]
                if khuc_doc != bytearray(khuc_file):
                    dc_hex = f"{dia_chi:06X}"
                    msg = self.ngon_ngu_hien_tai.get("log_lech_ma_hex",
                                                     "{thoi_gian}: [THẤT BẠI]: Lệch mã Hex ngay tại địa chỉ {dia_chi}!").replace(
                        "{thoi_gian}", tg).replace("{dia_chi}", dc_hex)
                    self.gui.ghi_log(msg)
                    loi_so_sanh = True
                    break

                phan_tram = int((dia_chi + do_dai_doc) / tong_kich_thuoc * 100)
                if phan_tram != phan_tram_cu:
                    self.gui.cap_nhat_tien_trinh(phan_tram)
                    phan_tram_cu = phan_tram

            if self.dang_lam_viec:
                if not loi_so_sanh:
                    tg = datetime.datetime.now().strftime('%H:%M:%S')
                    msg = self.ngon_ngu_hien_tai.get("log_khop_100",
                                                     "{thoi_gian}: [THÀNH CÔNG]: Dữ liệu file và ruột ROM khớp nhau y boong 100%!").replace(
                        "{thoi_gian}", tg)
                    self.gui.ghi_log(msg)
        except Exception as e:
            tg = datetime.datetime.now().strftime('%H:%M:%S')
            msg = self.ngon_ngu_hien_tai.get("log_loi_may_bao", "{thoi_gian}: [LỖI]: Máy báo trật lất: {loi}").replace(
                "{thoi_gian}", tg).replace("{loi}", str(e))
            self.gui.ghi_log(msg)
        finally:
            self.ch341_lib.CH341CloseDevice(0)
            self.dang_lam_viec = False
            self.gui.cap_nhat_tien_trinh(0)

    def xu_ly_tim_kiem(self):
        ma_chip = self.gui.o_tim_kiem.get().strip()
        if ma_chip:
            lich_su = list(self.gui.o_tim_kiem['values'])
            if ma_chip in lich_su: lich_su.remove(ma_chip)
            lich_su.insert(0, ma_chip)
            self.gui.o_tim_kiem['values'] = lich_su
            self.gui.o_tim_kiem.set(ma_chip)

    def xu_ly_chon_hang(self):
        try:
            vi_tri = self.gui.ds_hang.curselection()
            if not vi_tri: return
            hang_dang_chon = self.gui.ds_hang.get(vi_tri[0])
            self.gui.ds_ma.delete(0, tk.END)

            if hang_dang_chon == "!ALL":
                for ds_chip_cua_hang in self.kho_chip.values():
                    for ten_chip in ds_chip_cua_hang.keys():
                        self.gui.ds_ma.insert(tk.END, ten_chip)
            else:
                ds_chip_cua_hang = self.kho_chip.get(hang_dang_chon, {})
                for ten_chip in ds_chip_cua_hang.keys():
                    self.gui.ds_ma.insert(tk.END, ten_chip)
        except Exception:
            pass

    def _dich_nhi_phan_sang_hex(self, du_lieu_nhi_phan):
        dong_van_ban = []
        for i in range(0, len(du_lieu_nhi_phan), 16):
            khuc = du_lieu_nhi_phan[i:i + 16]
            dia_chi = f"{i:08X}"
            hex_trai = " ".join(f"{b:02X}" for b in khuc[:8])
            hex_phai = " ".join(f"{b:02X}" for b in khuc[8:])
            chuoi_hex = f"{hex_trai:<23}  {hex_phai:<23}"
            ascii_chars = "".join(chr(b) if 32 <= b <= 126 else "." for b in khuc)
            dong_van_ban.append(f"{dia_chi}  {chuoi_hex}  |{ascii_chars}|")
        return "\n".join(dong_van_ban)

    def cap_nhat_do_thi(self, toc_do_kb):
        if hasattr(self.gui, 'canvas_do_thi') and self.gui.canvas_do_thi is not None:
            self.lich_su_toc_do.pop(0)
            self.lich_su_toc_do.append(toc_do_kb)
            self.gui.canvas_do_thi.delete("all")

            chieu_rong = self.gui.canvas_do_thi.winfo_width()
            chieu_cao = self.gui.canvas_do_thi.winfo_height()

            if chieu_rong < 10: chieu_rong = 200
            if chieu_cao < 10: chieu_cao = 80

            dinh_muc_toi_da = max(self.lich_su_toc_do)
            if dinh_muc_toi_da < 10: dinh_muc_toi_da = 10

            khoang_cach_x = chieu_rong / len(self.lich_su_toc_do)

            for i in range(len(self.lich_su_toc_do) - 1):
                x1 = i * khoang_cach_x
                y1 = chieu_cao - (self.lich_su_toc_do[i] / dinh_muc_toi_da) * chieu_cao
                x2 = (i + 1) * khoang_cach_x
                y2 = chieu_cao - (self.lich_su_toc_do[i + 1] / dinh_muc_toi_da) * chieu_cao
                self.gui.canvas_do_thi.create_line(x1, y1, x2, y2, fill="#00FF00", width=1.5)

            chu_thich = f"{toc_do_kb:.1f} KB/s"
            self.gui.canvas_do_thi.create_text(5, 5, anchor=tk.NW, text=chu_thich, fill="#00FF00",
                                               font=("Consolas", 9, "bold"))

    def chay(self):
        self.root.mainloop()


if __name__ == "__main__":
    ung_dung = KhoiThucThi()
    ung_dung.chay()