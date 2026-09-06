import os
import sys
import threading
import time
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageDraw
import pystray
from pystray import MenuItem as item
from warp_api import WarpAPI, CONF_FILE
from tunnel_manager import TunnelManager

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class DiscordWarpApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Discord WARP Bypass")
        self.geometry("460x700")
        self.resizable(False, False)
        self.configure(fg_color="#0F172A")  # Modern Dark Theme

        # Set Window Icon
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            bundled_icon = os.path.join(sys._MEIPASS, "icon.ico")
            if os.path.exists(bundled_icon):
                icon_path = bundled_icon
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass

        self.warp_api = WarpAPI()
        self.tunnel = TunnelManager(CONF_FILE)
        
        self.is_connected = False
        self.is_connecting = False
        self.health_thread = None
        self.running = True
        self.tray_icon = None

        self.build_ui()
        self.protocol("WM_DELETE_WINDOW", self.on_window_close)

        # Initialize Warp Discord config
        self.init_warp()

        # Start periodic health check in background
        self.start_health_checker()

        # Setup System Tray in background thread
        self.setup_tray_icon()

    def build_ui(self):
        # Header
        self.header_frame = ctk.CTkFrame(self, fg_color="#1E293B", corner_radius=0, height=65)
        self.header_frame.pack(fill="x", side="top")

        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="🎮 Discord WARP",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#FFFFFF"
        )
        self.title_label.pack(side="left", padx=20, pady=16)

        self.badge_label = ctk.CTkLabel(
            self.header_frame,
            text="DEVRE DIŞI",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#94A3B8",
            fg_color="#334155",
            corner_radius=8,
            padx=10,
            pady=4
        )
        self.badge_label.pack(side="right", padx=20, pady=16)

        # Main Body
        self.body_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.body_frame.pack(fill="both", expand=True, padx=22, pady=14)

        # Split Tunneling Information Box
        self.info_box = ctk.CTkFrame(self.body_frame, fg_color="#1E1B4B", border_color="#4338CA", border_width=1, corner_radius=10)
        self.info_box.pack(fill="x", pady=(0, 12))

        self.info_title = ctk.CTkLabel(
            self.info_box,
            text="ℹ️ Sadece Discord Trafiği Tünellenir",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#C7D2FE"
        )
        self.info_title.pack(anchor="w", padx=12, pady=(8, 2))

        self.info_text = ctk.CTkLabel(
            self.info_box,
            text="Bu tünel tüm sistemi etkilemez. Yalnızca Discord ses ve mesaj sunucuları Cloudflare ile şifrelenir. Oyunlarınız, tarayıcınız ve diğer tüm uygulamalar normal yerel internetinizden çalışır.",
            font=ctk.CTkFont(size=11),
            text_color="#A5B4FC",
            justify="left",
            wraplength=390
        )
        self.info_text.pack(anchor="w", padx=12, pady=(0, 8))

        # Big Discord Shield Icon / Status Indicator
        self.shield_frame = ctk.CTkFrame(
            self.body_frame,
            width=90,
            height=90,
            corner_radius=45,
            fg_color="#1E293B"
        )
        self.shield_frame.pack(pady=(2, 8))
        self.shield_frame.pack_propagate(False)

        self.shield_icon = ctk.CTkLabel(
            self.shield_frame,
            text="🎮",
            font=ctk.CTkFont(size=40)
        )
        self.shield_icon.pack(expand=True)

        self.status_title = ctk.CTkLabel(
            self.body_frame,
            text="Discord Koruması Kapalı",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#F8FAFC"
        )
        self.status_title.pack(pady=(0, 2))

        self.status_desc = ctk.CTkLabel(
            self.body_frame,
            text="Discord'u engelsiz kullanmak için şalteri açın",
            font=ctk.CTkFont(size=11),
            text_color="#94A3B8"
        )
        self.status_desc.pack(pady=(0, 14))

        # Big Toggle Switch
        self.switch_var = ctk.StringVar(value="off")
        self.switch = ctk.CTkSwitch(
            self.body_frame,
            text="",
            variable=self.switch_var,
            onvalue="on",
            offvalue="off",
            command=self.toggle_vpn,
            width=65,
            height=34,
            switch_width=30,
            switch_height=26,
            progress_color="#5865F2",  # Discord Blurple
            button_color="#FFFFFF",
            button_hover_color="#E2E8F0"
        )
        self.switch.pack(pady=(0, 14))

        # Details Card
        self.details_card = ctk.CTkFrame(
            self.body_frame,
            fg_color="#1E293B",
            corner_radius=12
        )
        self.details_card.pack(fill="x", pady=(0, 12), padx=2)

        # Card Rows
        self.row_target = self.create_detail_row(self.details_card, "Kapsam:", "Yalnızca Discord (Oyunlar Etkilenmez)")
        self.row_proto = self.create_detail_row(self.details_card, "Protokol:", "WireGuard® (ChaCha20)")
        self.row_endpoint = self.create_detail_row(self.details_card, "Uç Nokta:", "engage.cloudflareclient.com:2408")
        self.row_ping = self.create_detail_row(self.details_card, "Discord Gecikmesi:", "-")

        # Bottom Action Buttons
        self.btn_frame = ctk.CTkFrame(self.body_frame, fg_color="transparent")
        self.btn_frame.pack(fill="x", side="bottom", pady=(0, 2))

        # Minimize to Tray Button
        self.tray_btn = ctk.CTkButton(
            self.btn_frame,
            text="📥 Arka Plana Al (Saatin Yanına Küçült)",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#5865F2",
            hover_color="#4752C4",
            text_color="#FFFFFF",
            height=34,
            corner_radius=8,
            command=self.hide_to_tray
        )
        self.tray_btn.pack(fill="x", pady=(0, 6))

        # Secondary Actions
        self.sec_btn_frame = ctk.CTkFrame(self.btn_frame, fg_color="transparent")
        self.sec_btn_frame.pack(fill="x")

        self.reset_btn = ctk.CTkButton(
            self.sec_btn_frame,
            text="🔄 Anahtarları Yenile",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#334155",
            hover_color="#475569",
            text_color="#38BDF8",
            height=30,
            corner_radius=8,
            command=self.reset_keys
        )
        self.reset_btn.pack(side="left", fill="x", expand=True, padx=(0, 3))

        # Uninstall / Cleanup Button
        self.uninstall_btn = ctk.CTkButton(
            self.sec_btn_frame,
            text="🗑️ Tünel Servisini Kaldır",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#7F1D1D",
            hover_color="#991B1B",
            text_color="#FECACA",
            height=30,
            corner_radius=8,
            command=self.uninstall_service
        )
        self.uninstall_btn.pack(side="right", fill="x", expand=True, padx=(3, 0))

        # Open Source GitHub Button
        self.github_btn = ctk.CTkButton(
            self.btn_frame,
            text="🐙 Kaynak Kodunu Görüntüle (GitHub)",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#0F172A",
            hover_color="#1E293B",
            text_color="#94A3B8",
            height=28,
            corner_radius=8,
            command=self.open_github
        )
        self.github_btn.pack(fill="x", pady=(8, 0))

    def create_detail_row(self, parent, label_text, val_text):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=14, pady=3)

        lbl = ctk.CTkLabel(row, text=label_text, font=ctk.CTkFont(size=11), text_color="#94A3B8")
        lbl.pack(side="left")

        val = ctk.CTkLabel(row, text=val_text, font=ctk.CTkFont(size=11, weight="bold"), text_color="#38BDF8")
        val.pack(side="right")
        return val

    def init_warp(self):
        try:
            creds = self.warp_api.register(force_new=False, mode="discord")
            self.row_endpoint.configure(text=creds.get("peer_endpoint", "engage.cloudflareclient.com:2408"))
            
            if self.tunnel.is_tunnel_running():
                self.set_connected_state(True)
        except Exception as e:
            self.status_desc.configure(text=f"Kayıt Hatası: {str(e)}")

    def toggle_vpn(self):
        if self.switch_var.get() == "on":
            self.connect()
        else:
            self.disconnect()

    def connect(self):
        if not self.tunnel.is_installed():
            # Prompt user to automatically download and install WireGuard
            answer = messagebox.askyesno(
                "WireGuard Sürücüsü Gerekli",
                "DiscordWARP tünelinin çalışabilmesi için WireGuard Windows sürücüsü gereklidir.\n\n"
                "WireGuard sisteminizde bulunamadı.\n"
                "Şimdi resmi sunuculardan otomatik olarak indirilip kurulsun mu?",
                icon="question"
            )
            if answer:
                self.set_connecting_state()
                self.status_title.configure(text="Sürücü Yükleniyor...")
                self.status_desc.configure(text="WireGuard kurulumu başlatılıyor...", text_color="#FDE68A")
                threading.Thread(target=self._async_install_wireguard_and_connect, daemon=True).start()
            else:
                self.switch_var.set("off")
            return

        self.set_connecting_state()
        threading.Thread(target=self._async_connect, daemon=True).start()

    def _async_install_wireguard_and_connect(self):
        def update_progress(msg):
            self.after(0, lambda: self.status_desc.configure(text=msg, text_color="#FDE68A"))

        success, msg = self.tunnel.install_wireguard(progress_callback=update_progress)
        if success:
            self.after(0, lambda: self.status_desc.configure(text="WireGuard kuruldu! Tünel başlatılıyor...", text_color="#34D399"))
            time.sleep(1.0)
            self._async_connect()
        else:
            def show_fail_dialog():
                self.set_error_state("WireGuard kurulamadı.")
                if messagebox.askyesno(
                    "Kurulum Başarısız",
                    f"{msg}\n\nResmi WireGuard indirme sitesi tarayıcınızda açılsın mı?"
                ):
                    import webbrowser
                    webbrowser.open("https://www.wireguard.com/install/")
            self.after(0, show_fail_dialog)

    def _async_connect(self):
        try:
            # Quick check: if tunnel is already running, just update UI
            if self.tunnel.is_tunnel_running():
                self.after(0, lambda: self.status_desc.configure(text="Servis zaten çalışıyor, durum güncelleniyor...", text_color="#FDE68A"))
                time.sleep(0.3)
                health = self.warp_api.check_health()
                if health["success"]:
                    self.after(0, lambda: self.row_ping.configure(text=f"{health['ping_ms']} ms (Aktif)", text_color="#10B981"))
                self.after(0, lambda: self.set_connected_state(True))
                return

            # Step 1: Check admin
            self.after(0, lambda: self.status_desc.configure(text="[1/5] Yönetici yetkileri kontrol ediliyor...", text_color="#FDE68A"))
            if not self.tunnel.is_admin():
                self.after(0, lambda: self.set_error_state("Yönetici yetkisi gerekiyor! Uygulamayı sağ tık → 'Yönetici olarak çalıştır' ile açın."))
                return
            time.sleep(0.3)

            # Step 2: Register with Cloudflare
            self.after(0, lambda: self.status_desc.configure(text="[2/5] Cloudflare WARP'a kaydolunuyor...", text_color="#FDE68A"))
            self.warp_api.register(force_new=False, mode="discord")
            time.sleep(0.3)

            # Step 3: Resolve Discord domains via DoH (bypass ISP DNS)
            self.after(0, lambda: self.status_desc.configure(text="[3/5] Discord DNS adresleri çözümleniyor (DoH)...", text_color="#FDE68A"))
            # (This is done inside start_tunnel automatically)
            time.sleep(0.2)

            # Step 4: Start WireGuard tunnel + hosts file
            self.after(0, lambda: self.status_desc.configure(text="[4/5] WireGuard tüneli başlatılıyor...", text_color="#FDE68A"))
            self.tunnel.start_tunnel()
            time.sleep(0.5)

            # Step 5: Health check
            self.after(0, lambda: self.status_desc.configure(text="[5/5] Bağlantı doğrulanıyor...", text_color="#FDE68A"))
            health = self.warp_api.check_health()
            if health["success"]:
                self.after(0, lambda: self.row_ping.configure(text=f"{health['ping_ms']} ms (Aktif)", text_color="#10B981"))

            self.after(0, lambda: self.set_connected_state(True))
        except Exception as e:
            self.after(0, lambda: self.set_error_state(str(e)))

    def disconnect(self):
        self.set_connecting_state()
        threading.Thread(target=self._async_disconnect, daemon=True).start()

    def _async_disconnect(self):
        try:
            self.tunnel.stop_tunnel()
            self.after(500, lambda: self.set_connected_state(False))
        except Exception as e:
            self.after(0, lambda: self.set_error_state(str(e)))

    def set_connected_state(self, connected):
        self.is_connected = connected
        self.is_connecting = False

        if connected:
            self.switch_var.set("on")
            self.shield_frame.configure(fg_color="#312E81")
            self.shield_icon.configure(text="🎮")
            self.status_title.configure(text="Discord Açık & Aktif", text_color="#818CF8")
            self.status_desc.configure(
                text="Yalnızca Discord tünelde. Oyunlarınız ve tarayıcınız normal hızında!",
                text_color="#C7D2FE"
            )
            self.badge_label.configure(text="BAĞLANDI", text_color="#10B981", fg_color="#064E3B")
        else:
            self.switch_var.set("off")
            self.shield_frame.configure(fg_color="#1E293B")
            self.shield_icon.configure(text="🎮")
            self.status_title.configure(text="Discord Koruması Kapalı", text_color="#F8FAFC")
            self.status_desc.configure(
                text="Discord'u engelsiz kullanmak için şalteri açın",
                text_color="#94A3B8"
            )
            self.badge_label.configure(text="DEVRE DIŞI", text_color="#94A3B8", fg_color="#334155")
            self.row_ping.configure(text="-", text_color="#94A3B8")

    def set_connecting_state(self):
        self.is_connecting = True
        self.shield_frame.configure(fg_color="#78350F")
        self.status_title.configure(text="Bağlanıyor...", text_color="#F59E0B")
        self.status_desc.configure(text="WireGuard Discord tüneli kuruluyor...", text_color="#FDE68A")
        self.badge_label.configure(text="BAĞLANIYOR", text_color="#F59E0B", fg_color="#78350F")

    def set_error_state(self, error_msg):
        self.is_connected = False
        self.is_connecting = False
        self.switch_var.set("off")
        self.shield_frame.configure(fg_color="#7F1D1D")
        self.status_title.configure(text="Hata Oluştu", text_color="#EF4444")
        self.status_desc.configure(text=error_msg[:60] + "..." if len(error_msg) > 60 else error_msg, text_color="#FECACA")
        self.badge_label.configure(text="HATA", text_color="#EF4444", fg_color="#7F1D1D")

    def start_health_checker(self):
        def loop():
            while self.running:
                if self.is_connected:
                    health = self.warp_api.check_health()
                    if health["success"] and health["ping_ms"] > 0:
                        ping_str = f"{health['ping_ms']} ms (Aktif)"
                        color = "#10B981"
                    else:
                        ping_str = "Kontrol ediliyor..."
                        color = "#F59E0B"
                    self.after(0, lambda p=ping_str, c=color: self.row_ping.configure(text=p, text_color=c))
                time.sleep(5)

        self.health_thread = threading.Thread(target=loop, daemon=True)
        self.health_thread.start()

    # --- System Tray Integration ---
    def create_tray_image(self):
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.png")
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            bundled_icon = os.path.join(sys._MEIPASS, "icon.png")
            if os.path.exists(bundled_icon):
                icon_path = bundled_icon
        if os.path.exists(icon_path):
            try:
                return Image.open(icon_path).resize((64, 64))
            except Exception:
                pass

        img = Image.new('RGBA', (64, 64), color=(0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.ellipse((4, 4, 60, 60), fill='#5865F2', outline='#FFFFFF', width=2)
        d.rectangle((20, 26, 44, 38), fill='#FFFFFF')
        d.rectangle((28, 18, 36, 46), fill='#FFFFFF')
        return img

    def setup_tray_icon(self):
        tray_image = self.create_tray_image()
        menu = (
            item('Discord WARP Aç', self.show_from_tray, default=True),
            item('Bağlan / Bağlantıyı Kes', lambda: self.after(0, self.toggle_vpn)),
            item('Çıkış', self.quit_app),
        )
        self.tray_icon = pystray.Icon("DiscordWARP", tray_image, "Discord WARP", menu)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def hide_to_tray(self):
        self.withdraw()

    def show_from_tray(self, icon=None, item=None):
        self.after(0, self._restore_window)

    def _restore_window(self):
        self.deiconify()
        self.lift()
        self.focus_force()

    def on_window_close(self):
        self.quit_app()

    def quit_app(self, icon=None, item=None):
        """Exits the app with status notification. VPN service keeps running."""
        self.running = False

        # Show notification based on service status
        if self.tunnel.is_tunnel_running():
            if self.tray_icon:
                self.tray_icon.notify(
                    "Discord VPN arka planda çalışmaya devam ediyor.\nKapatmak için uygulamayı açıp 'Tünel Servisini Kaldır' butonunu kullanın.",
                    "Discord WARP Aktif ✅"
                )
                import time
                time.sleep(2)
        else:
            if self.tray_icon:
                self.tray_icon.notify(
                    "VPN servisi aktif değil. Discord koruması kapalı.",
                    "Discord WARP Kapalı"
                )
                import time
                time.sleep(1.5)

        if self.tray_icon:
            self.tray_icon.stop()
        self.after(0, self.destroy)
        sys.exit(0)

    def uninstall_service(self):
        if messagebox.askyesno("Tünel Servisini Kaldır", "WireGuard tünel servisi tamamen durdurulsun ve sistemden silinsin mi?"):
            self.set_connecting_state()
            def _async_uninstall():
                self.tunnel.clean_uninstall_all()
                self.after(0, lambda: [
                    self.set_connected_state(False),
                    messagebox.showinfo("Başarılı", "WireGuard tünel servisi sistemden tamamen kaldırıldı. Ağınız orijinal durumuna döndü.")
                ])
            threading.Thread(target=_async_uninstall, daemon=True).start()

    def reset_keys(self):
        if messagebox.askyesno("Anahtarları Sıfırla", "Yeni Cloudflare WARP anahtarları oluşturulsun ve kayıt yenilensin mi?"):
            self.disconnect()
            try:
                creds = self.warp_api.register(force_new=True, mode="discord")
                self.row_endpoint.configure(text=creds.get("peer_endpoint", "engage.cloudflareclient.com:2408"))
                messagebox.showinfo("Başarılı", "Yeni WARP anahtarları başarıyla oluşturuldu ve kaydedildi!")
            except Exception as e:
                messagebox.showerror("Hata", f"Yenileme başarısız: {str(e)}")

    def open_github(self):
        import webbrowser
        webbrowser.open("https://github.com/metehanguner/DiscordWARP")

if __name__ == "__main__":
    import ctypes
    import sys
    import os
    
    # Auto-elevate to Administrator if not already
    if not ctypes.windll.shell32.IsUserAnAdmin():
        if getattr(sys, 'frozen', False):
            # Running as PyInstaller executable
            try:
                ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, None, None, 1)
            except Exception:
                pass
            sys.exit(0)
        else:
            # Running as python script
            script = os.path.abspath(__file__)
            try:
                ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{script}"', None, 1)
            except Exception:
                pass
            sys.exit(0)

    app = DiscordWarpApp()
    app.mainloop()
