import tkinter as tk
from tkinter import scrolledtext
from tkinter import ttk


class GiaoDienCH341:
    def __init__(self, root, ngon_ngu_dict, trinh_dieu_khien=None):
        self.root = root
        self.nn = ngon_ngu_dict
        self.dk = trinh_dieu_khien

        self.root.title(self.nn.get("tieu_de", "Công Cụ Điều Khiển CH341 - Trần Vĩnh Đức"))
        self.root.geometry("850x650")
        self.root.configure(bg="#D4E6F1")

        self.menu_ngon_ngu = None
        self.menu_cai_dat = None
        self.submenu_nap = None
        self.cua_so_bo_dem = None

        self.var_toc_do = tk.StringVar(value="nhanh")
        self.var_kieu_nap = tk.StringVar(value="block")

        self._dung_thanh_cong_cu()
        self._dung_thanh_trang_thai()
        self._dung_khung_ben_trai()
        self._dung_khung_ben_phai()

    def _dung_thanh_cong_cu(self):
        khung_menu = tk.Frame(self.root, bg="#D4E6F1", bd=1, relief=tk.RAISED)
        khung_menu.pack(side=tk.TOP, fill=tk.X)

        self.nut_bo_dem = tk.Button(khung_menu, text=self.nn.get("menu_bo_dem", "Bộ đệm (Buffer)"),
                                    bg="#D4E6F1", relief=tk.FLAT, overrelief=tk.RAISED,
                                    command=lambda: self.dk.xu_ly_bo_dem() if self.dk else None)
        self.nut_bo_dem.pack(side=tk.LEFT, padx=5, pady=2)

        self.btn_cai_dat = tk.Menubutton(khung_menu, text=self.nn.get("menu_cai_dat", "Cài đặt (Setting)"),
                                         bg="#D4E6F1", relief=tk.FLAT)
        self.btn_cai_dat.pack(side=tk.LEFT, padx=5, pady=2)
        self.btn_cai_dat.bind("<Button-1>", lambda e: self.btn_cai_dat.config(relief=tk.SUNKEN))
        self.btn_cai_dat.bind("<ButtonRelease-1>", lambda e: self.btn_cai_dat.config(relief=tk.FLAT))
        self.btn_cai_dat.bind("<Enter>", lambda e: self.btn_cai_dat.config(relief=tk.RAISED))
        self.btn_cai_dat.bind("<Leave>", lambda e: self.btn_cai_dat.config(relief=tk.FLAT))

        self.menu_cai_dat = tk.Menu(self.btn_cai_dat, tearoff=0)
        self.btn_cai_dat.config(menu=self.menu_cai_dat)
        self._tao_danh_sach_cai_dat()

        self.btn_ngon_ngu = tk.Menubutton(khung_menu, text=self.nn.get("menu_ngon_ngu", "Ngôn ngữ (Language)"),
                                          bg="#D4E6F1", relief=tk.FLAT)
        self.btn_ngon_ngu.pack(side=tk.LEFT, padx=5, pady=2)
        self.btn_ngon_ngu.bind("<Button-1>", lambda e: self.btn_ngon_ngu.config(relief=tk.SUNKEN))
        self.btn_ngon_ngu.bind("<ButtonRelease-1>", lambda e: self.btn_ngon_ngu.config(relief=tk.FLAT))
        self.btn_ngon_ngu.bind("<Enter>", lambda e: self.btn_ngon_ngu.config(relief=tk.RAISED))
        self.btn_ngon_ngu.bind("<Leave>", lambda e: self.btn_ngon_ngu.config(relief=tk.FLAT))

        self.menu_ngon_ngu = tk.Menu(self.btn_ngon_ngu, tearoff=0)
        self.btn_ngon_ngu.config(menu=self.menu_ngon_ngu)

    def tao_danh_sach_ngon_ngu(self, danh_sach_ten):
        self.menu_ngon_ngu.delete(0, tk.END)
        for ten in danh_sach_ten:
            self.menu_ngon_ngu.add_command(label=ten,
                                           command=lambda t=ten: self.dk.xu_ly_chon_ngon_ngu(t) if self.dk else None)

    def _tao_danh_sach_cai_dat(self):
        self.menu_cai_dat.delete(0, tk.END)
        self.submenu_nap = tk.Menu(self.menu_cai_dat, tearoff=0)

        self.sub_toc_do = tk.Menu(self.submenu_nap, tearoff=0)
        self.sub_toc_do.add_radiobutton(label=self.nn.get("menu_speed_fast", "Nhanh (Fast)"),
                                        variable=self.var_toc_do, value="nhanh",
                                        command=lambda: self.dk.thiet_lap_toc_do("nhanh") if self.dk else None)
        self.sub_toc_do.add_radiobutton(label=self.nn.get("menu_speed_slow", "Chậm (Slow)"),
                                        variable=self.var_toc_do, value="cham",
                                        command=lambda: self.dk.thiet_lap_toc_do("cham") if self.dk else None)

        self.sub_kieu = tk.Menu(self.submenu_nap, tearoff=0)
        self.sub_kieu.add_radiobutton(label=self.nn.get("menu_mode_bit", "Từng bit (Bit-by-bit)"),
                                      variable=self.var_kieu_nap, value="bit",
                                      command=lambda: self.dk.thiet_lap_kieu_nap("bit") if self.dk else None)
        self.sub_kieu.add_radiobutton(label=self.nn.get("menu_mode_block", "Từng khối (Block)"),
                                      variable=self.var_kieu_nap, value="block",
                                      command=lambda: self.dk.thiet_lap_kieu_nap("block") if self.dk else None)

        self.submenu_nap.add_cascade(label=self.nn.get("menu_opt_1_sub1", "Tốc độ nạp"), menu=self.sub_toc_do)
        self.submenu_nap.add_cascade(label=self.nn.get("menu_opt_1_sub2", "Kiểu nạp (Từng bit / Từng khối)"),
                                     menu=self.sub_kieu)

        self.menu_cai_dat.add_cascade(label=self.nn.get("menu_opt_1", "Tùy chọn thiết lập nạp (O)"),
                                      menu=self.submenu_nap)
        self.menu_cai_dat.add_separator()
        self.menu_cai_dat.add_command(label=self.nn.get("menu_opt_2", "Gỡ cài đặt USB Driver (U)"),
                                      command=lambda: getattr(self.dk, 'xu_ly_go_driver', lambda: None)())
        self.menu_cai_dat.add_command(label=self.nn.get("menu_opt_3", "Cài lại USB Driver (D)"),
                                      command=lambda: getattr(self.dk, 'xu_ly_cai_driver', lambda: None)())
        self.menu_cai_dat.add_separator()
        self.menu_cai_dat.add_command(label=self.nn.get("menu_opt_4", "Quản lý thiết bị (M)"),
                                      command=lambda: getattr(self.dk, 'mo_device_manager', lambda: None)())

    def _dung_thanh_trang_thai(self):
        khung_day = tk.Frame(self.root, bg="#D4E6F1")
        khung_day.pack(side=tk.BOTTOM, fill=tk.X, pady=(0, 5))

        khung_nhan_trai = tk.Frame(khung_day, bg="#D4E6F1")
        khung_nhan_trai.pack(side=tk.LEFT, padx=(15, 10))

        self.nhan_sn = tk.Label(khung_nhan_trai, text="Đang dò tìm...", anchor="w", font=("Arial", 9),
                                bg="#D4E6F1", relief=tk.SUNKEN, bd=1, padx=5)
        self.nhan_sn.pack(side=tk.TOP, fill=tk.X, pady=(0, 2), ipady=2)

        self.nhan_ngay_thang = tk.Label(khung_nhan_trai, text=self.nn.get("nhan_ngay_hoan_thanh", "Hoàn thành: 05/03/2026"),
                                        anchor="w", font=("Arial", 9), bg="#D4E6F1", relief=tk.SUNKEN, bd=1, padx=5)
        self.nhan_ngay_thang.pack(side=tk.BOTTOM, fill=tk.X, ipady=2)

        self.thanh_tien_trinh = ttk.Progressbar(khung_day, orient=tk.HORIZONTAL, mode='determinate')
        self.thanh_tien_trinh.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(35, 15))

    def cap_nhat_tien_trinh(self, phan_tram):
        if hasattr(self, 'thanh_tien_trinh'):
            self.thanh_tien_trinh['value'] = phan_tram
            self.root.update()

    def _dung_khung_ben_trai(self):
        khung_trai = tk.Frame(self.root, bg="#D4E6F1", width=165)
        khung_trai.pack_propagate(False)
        khung_trai.pack(side=tk.LEFT, fill=tk.Y, padx=15, pady=15)
        self.cac_nut = {}

        cau_hinh_nut = [
            ("nut_dinh_danh", self.nn.get("nut_dinh_danh", "Đinh Danh (SmartID)"),
             lambda: self.dk.xu_ly_ket_noi() if self.dk else None),
            ("nut_doc", self.nn.get("nut_doc", "Đọc (Read)"), lambda: self.dk.xu_ly_doc() if self.dk else None),
            ("nut_luu", self.nn.get("nut_luu", "Lưu (Save)"), lambda: self.dk.xu_ly_luu() if self.dk else None),
            ("nut_mo", self.nn.get("nut_mo", "Mở file (Open)"), lambda: self.dk.xu_ly_mo_file() if self.dk else None),
            ("nut_ghi", self.nn.get("nut_ghi", "Viết (Write)"), lambda: self.dk.xu_ly_ghi() if self.dk else None),
            ("nut_so_sanh", self.nn.get("nut_so_sanh", "So sánh (Verify)"),
             lambda: self.dk.xu_ly_so_sanh() if self.dk else None),
            ("nut_xoa", self.nn.get("nut_xoa", "Xóa (Erase)"), lambda: self.dk.xu_ly_xoa() if self.dk else None),
            ("nut_rom_trong", self.nn.get("nut_rom_trong", "ROM trống? (Blank)"),
             lambda: self.dk.xu_ly_kiem_tra_trong() if self.dk else None),
            ("nut_bao_ve", self.nn.get("nut_bao_ve", "Bảo vệ (Protect)"),
             lambda: self.dk.xu_ly_bao_ve() if self.dk else None),
            ("nut_huy_bao_ve", self.nn.get("nut_huy_bao_ve", "Hủy bảo vệ (Unprotect)"),
             lambda: self.dk.xu_ly_huy_bao_ve() if self.dk else None),
            ("nut_huy", self.nn.get("nut_huy", "Huỷ (Cancel)"), lambda: self.dk.xu_ly_huy() if self.dk else None)
        ]
        phong_cach = ttk.Style()
        phong_cach.configure("NutBam.TButton", font=("Arial", 9, "bold"))

        for ma_nut, text_hien_thi, lenh in cau_hinh_nut:
            btn = ttk.Button(khung_trai, text=text_hien_thi, style="NutBam.TButton", command=lenh)
            btn.pack(pady=5, expand=True, fill=tk.X, ipady=4)
            self.cac_nut[ma_nut] = btn

    def _dung_khung_ben_phai(self):
        khung_phai = tk.Frame(self.root, bg="#D4E6F1")
        khung_phai.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        khung_tim_kiem = tk.Frame(khung_phai, bg="#D4E6F1")
        khung_tim_kiem.pack(side=tk.TOP, fill=tk.X, pady=(0, 5))

        khung_trai_tim = tk.Frame(khung_tim_kiem, bg="#D4E6F1")
        khung_trai_tim.pack(side=tk.LEFT, fill=tk.X, expand=True)

        khung_nhan = tk.Frame(khung_trai_tim, bg="#D4E6F1")
        khung_nhan.pack(fill=tk.X)
        self.nhan_tim = tk.Label(khung_nhan, text=self.nn.get("nhan_tim_kiem", "Gõ mã số chip:"), bg="#D4E6F1")
        self.nhan_tim.pack(side=tk.LEFT)
        self.nhan_lich_su = tk.Label(khung_nhan, text=self.nn.get("nhan_lich_su", "Lịch sử (History)"), bg="#D4E6F1")
        self.nhan_lich_su.pack(side=tk.RIGHT)

        self.o_tim_kiem = ttk.Combobox(khung_trai_tim, values=[])
        self.o_tim_kiem.pack(fill=tk.X, pady=(2, 0))

        btn_ok = tk.Button(khung_tim_kiem, text="OK", width=10,
                           command=lambda: self.dk.xu_ly_tim_kiem() if self.dk else None)
        btn_ok.pack(side=tk.RIGHT, padx=(10, 0), anchor="s")

        khung_thu_vien = tk.Frame(khung_phai, bg="#D4E6F1")
        khung_thu_vien.pack(side=tk.TOP, fill=tk.X, expand=False, pady=5)

        self.khung_hang = tk.LabelFrame(khung_thu_vien, text=self.nn.get("nhan_hang", "Hãng sản xuất"), bg="#D4E6F1")
        self.khung_hang.pack(side=tk.LEFT, fill=tk.Y, expand=False, padx=(0, 5))
        self.ds_hang = tk.Listbox(self.khung_hang, width=20, height=14)
        self.ds_hang.pack(side=tk.LEFT, fill=tk.Y, expand=False)
        cuon_hang = tk.Scrollbar(self.khung_hang, command=self.ds_hang.yview)
        cuon_hang.pack(side=tk.RIGHT, fill=tk.Y)
        self.ds_hang.config(yscrollcommand=cuon_hang.set)
        self.ds_hang.bind('<<ListboxSelect>>', lambda e: self.dk.xu_ly_chon_hang() if self.dk else None)

        self.khung_ma = tk.LabelFrame(khung_thu_vien, text=self.nn.get("nhan_ma", "Mã số linh kiện"), bg="#D4E6F1")
        self.khung_ma.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 0))
        self.ds_ma = tk.Listbox(self.khung_ma, height=14)
        self.ds_ma.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        cuon_ma = tk.Scrollbar(self.khung_ma, command=self.ds_ma.yview)
        cuon_ma.pack(side=tk.RIGHT, fill=tk.Y)
        self.ds_ma.config(yscrollcommand=cuon_ma.set)

        self.khung_do_thi = tk.LabelFrame(khung_phai, text=self.nn.get("nhan_do_thi", "Đo tốc độ (KB/s)"), bg="#D4E6F1")
        self.khung_do_thi.pack(side=tk.TOP, fill=tk.X, expand=False, pady=(0, 5))

        self.canvas_do_thi = tk.Canvas(self.khung_do_thi, bg="black", height=65, highlightthickness=1, highlightbackground="gray")
        self.canvas_do_thi.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        self.canvas_do_thi.create_text(5, 5, anchor=tk.NW, text="0.0 KB/s  |  READY", fill="#00FF00", font=("Consolas", 10, "bold"))

        khung_log = tk.Frame(khung_phai, bg="#D4E6F1")
        khung_log.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True, pady=(0, 0))

        self.hop_thu_bao = scrolledtext.ScrolledText(khung_log)
        self.hop_thu_bao.pack(fill=tk.BOTH, expand=True)

    def mo_cua_so_bo_dem(self, chuoi_hex=""):
        if self.cua_so_bo_dem is not None and self.cua_so_bo_dem.winfo_exists():
            self.cua_so_bo_dem.lift()
            self._dien_du_lieu_bo_dem(chuoi_hex)
            return
        self.cua_so_bo_dem = tk.Toplevel(self.root)
        self.cua_so_bo_dem.title("Buffer view")
        self.cua_so_bo_dem.geometry("750x500")
        self.cua_so_bo_dem.configure(bg="#F0F0F0")

        # --- Dời mấy khung dưới đáy lên Pack trước đặng tụi nó neo cứng ---
        khung_nut_bo_dem = tk.Frame(self.cua_so_bo_dem, bg="#F0F0F0")
        khung_nut_bo_dem.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

        khung_info = tk.Frame(self.cua_so_bo_dem, bg="#F0F0F0")
        khung_info.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)

        # --- Tiếp tới phần nóc ---
        khung_header = tk.Frame(self.cua_so_bo_dem, bg="#F0F0F0")
        khung_header.pack(side=tk.TOP, fill=tk.X, padx=10, pady=(10, 0))
        tk.Label(khung_header, text="Address", width=12, relief="groove", bg="white").pack(side=tk.LEFT)
        tk.Label(khung_header, text="HEX", relief="groove", bg="white").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        tk.Label(khung_header, text="ASCII", width=20, relief="groove", bg="white").pack(side=tk.RIGHT)

        # --- Hộp văn bản vô sau cùng đặng nhồi đầy phần đất còn dư ---
        self.hop_hex = scrolledtext.ScrolledText(self.cua_so_bo_dem, font=("Courier New", 10), bg="white")
        self.hop_hex.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=5)
        self._dien_du_lieu_bo_dem(chuoi_hex)

        tk.Label(khung_info, text="Current address: 00000000H", relief="groove", bg="white", anchor="w").pack(
            side=tk.LEFT, ipadx=10, ipady=8)
        tk.Label(khung_info, text="Data buffer range: 00000000H - FFFFFFFFH", relief="groove", bg="white",
                 anchor="w").pack(side=tk.RIGHT, ipadx=10, ipady=8)

        # Đã quét sạch đám nút kiểng, chỉ để lại mỗi cái chốt an toàn đặng đóng cửa!
        tk.Button(khung_nut_bo_dem, text="OK", width=12, command=self.cua_so_bo_dem.destroy).pack(side=tk.RIGHT, padx=3)

    def _dien_du_lieu_bo_dem(self, chuoi_hex):
        self.hop_hex.config(state=tk.NORMAL)
        self.hop_hex.delete(1.0, tk.END)
        self.hop_hex.insert(tk.END, chuoi_hex)
        self.hop_hex.config(state=tk.DISABLED)

    def thay_chu_tren_mat(self, tu_vung_moi):
        self.nn = tu_vung_moi

        self.root.title(tu_vung_moi.get("tieu_de", "Công Cụ Điều Khiển CH341 - Trần Vĩnh Đức"))
        for ma_nut, btn in self.cac_nut.items():
            if ma_nut in tu_vung_moi:
                btn.config(text=tu_vung_moi[ma_nut])

        self.nhan_tim.config(text=tu_vung_moi.get("nhan_tim_kiem", "Gõ mã số chip:"))
        self.nhan_lich_su.config(text=tu_vung_moi.get("nhan_lich_su", "Lịch sử (History)"))
        self.khung_hang.config(text=tu_vung_moi.get("nhan_hang", "Hãng sản xuất"))
        self.khung_ma.config(text=tu_vung_moi.get("nhan_ma", "Mã số linh kiện"))

        if hasattr(self, 'khung_do_thi'):
            self.khung_do_thi.config(text=tu_vung_moi.get("nhan_do_thi", "Đo tốc độ (KB/s)"))

        if hasattr(self, 'nut_bo_dem'):
            self.nut_bo_dem.config(text=tu_vung_moi.get("menu_bo_dem", "Bộ đệm (Buffer)"))
        if hasattr(self, 'btn_cai_dat'):
            self.btn_cai_dat.config(text=tu_vung_moi.get("menu_cai_dat", "Cài đặt (Setting)"))
        if hasattr(self, 'btn_ngon_ngu'):
            self.btn_ngon_ngu.config(text=tu_vung_moi.get("menu_ngon_ngu", "Ngôn ngữ (Language)"))

        if hasattr(self, 'nhan_ngay_thang'):
            self.nhan_ngay_thang.config(text=tu_vung_moi.get("nhan_ngay_hoan_thanh", "Hoàn thành: 05/03/2026"))

        if hasattr(self, 'menu_cai_dat'):
            self._tao_danh_sach_cai_dat()

    def ghi_log(self, thong_diep):
        self.hop_thu_bao.insert(tk.END, thong_diep + "\n")
        self.hop_thu_bao.see(tk.END)

    def cap_nhat_so_xe_ri(self, chuoi_sn):
        self.nhan_sn.config(text=chuoi_sn)

    def cap_nhat_danh_sach_hang(self, danh_sach):
        self.ds_hang.delete(0, tk.END)
        for hang in danh_sach:
            self.ds_hang.insert(tk.END, hang)

    def cap_nhat_danh_sach_ma(self, danh_sach):
        self.ds_ma.delete(0, tk.END)
        for ma in danh_sach:
            self.ds_ma.insert(tk.END, ma)