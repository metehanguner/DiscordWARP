import os
import subprocess
import shutil
import ctypes
import sys
import time
import json
import urllib.request

import tempfile
import winreg

CREATE_NO_WINDOW = 0x08000000
HOSTS_PATH = r"C:\Windows\System32\drivers\etc\hosts"
HOSTS_MARKER_START = "# === DISCORD WARP START ==="
HOSTS_MARKER_END = "# === DISCORD WARP END ==="

# Discord domains that need DNS bypass
DISCORD_DOMAINS = [
    "discord.com",
    "www.discord.com",
    "gateway.discord.gg",
    "discord.gg",
    "discordapp.com",
    "www.discordapp.com",
    "cdn.discordapp.com",
    "media.discordapp.net",
    "images-ext-1.discordapp.net",
    "images-ext-2.discordapp.net",
    "discord.media",
    "discordcdn.com",
    "dis.gd",
    "discord-attachments-uploads-prd.storage.googleapis.com",
    "dl.discordapp.net",
    "status.discord.com",
    "support.discord.com",
    "hammerandchisel.ssl.zendesk.com",
    "discord.design",
    "discordstatus.com",
    "latency.discord.media",
    "router.discordapp.net",
    "gateway.discord.gg",
    "api.discord.com",
    "updates.discord.com",
]


class TunnelManager:
    def __init__(self, conf_path):
        self.conf_path = conf_path
        self.tunnel_name = os.path.splitext(os.path.basename(conf_path))[0]
        self.wireguard_exe = self.find_wireguard()

    def is_admin(self):
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False

    def find_wireguard(self):
        """Locates the official WireGuard executable on Windows."""
        candidate_paths = []

        # Check standard ProgramFiles environment variables
        for env_var in ("ProgramFiles", "ProgramFiles(x86)", "ProgramW6432"):
            base = os.environ.get(env_var)
            if base:
                candidate_paths.append(os.path.join(base, "WireGuard", "wireguard.exe"))

        # Check explicit common drives
        sys_drive = os.environ.get("SystemDrive", "C:")
        for drive in (sys_drive, "C:", "D:", "E:"):
            candidate_paths.append(os.path.join(f"{drive}\\", "Program Files", "WireGuard", "wireguard.exe"))
            candidate_paths.append(os.path.join(f"{drive}\\", "Program Files (x86)", "WireGuard", "wireguard.exe"))

        # Check Local AppData
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            candidate_paths.append(os.path.join(local_app_data, "Programs", "WireGuard", "wireguard.exe"))

        # Check all candidate paths
        for p in candidate_paths:
            if p and os.path.exists(p):
                return os.path.normpath(p)

        # Check system PATH
        for name in ("wireguard", "wireguard.exe"):
            which_path = shutil.which(name)
            if which_path and os.path.exists(which_path):
                return os.path.normpath(which_path)

        return None

    def is_installed(self):
        self.wireguard_exe = self.find_wireguard()
        return self.wireguard_exe is not None

    def install_wireguard(self, progress_callback=None):
        """
        Installs WireGuard on Windows using a multi-stage approach:
        1. Attempts silent install via Windows Package Manager (winget).
        2. Fallback: Downloads official installer from wireguard.com and runs silent install.
        3. Fallback: Launches interactive installer if silent mode fails.
        Returns: (success: bool, message: str)
        """
        def report(msg):
            if progress_callback:
                progress_callback(msg)

        # Already installed?
        found = self.find_wireguard()
        if found:
            self.wireguard_exe = found
            return True, "WireGuard zaten sisteminizde yüklü."

        # Method 0: Check if installer already exists in the application folder
        local_candidates = [
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "wireguard-installer.exe"),
            os.path.join(os.getcwd(), "wireguard-installer.exe"),
        ]
        if getattr(sys, 'frozen', False):
            local_candidates.append(os.path.join(os.path.dirname(sys.executable), "wireguard-installer.exe"))
            if hasattr(sys, '_MEIPASS'):
                local_candidates.append(os.path.join(sys._MEIPASS, "wireguard-installer.exe"))

        for local_installer in local_candidates:
            if os.path.exists(local_installer):
                report("Klasördeki WireGuard yükleyicisi kuruluyor...")
                try:
                    subprocess.run(
                        [local_installer, "/quiet"],
                        capture_output=True,
                        timeout=90,
                        creationflags=CREATE_NO_WINDOW
                    )
                    for _ in range(10):
                        time.sleep(2)
                        found = self.find_wireguard()
                        if found:
                            self.wireguard_exe = found
                            return True, "WireGuard yerel klasörden başarıyla kuruldu."
                    
                    # If quiet install didn't complete, try interactive
                    report("WireGuard kurulum sihirbazı başlatılıyor...")
                    subprocess.run([local_installer], timeout=120)
                    time.sleep(2)
                    found = self.find_wireguard()
                    if found:
                        self.wireguard_exe = found
                        return True, "WireGuard başarıyla kuruldu."
                except Exception:
                    pass

        # Method 1: Try winget if available
        winget_path = shutil.which("winget")
        if winget_path:
            report("[1/2] WinGet ile WireGuard yükleniyor...")
            try:
                cmd = "winget install -e --id WireGuard.WireGuard --silent --accept-package-agreements --accept-source-agreements"
                subprocess.run(
                    ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", cmd],
                    capture_output=True,
                    text=True,
                    timeout=90,
                    creationflags=CREATE_NO_WINDOW
                )
                time.sleep(2)
                found = self.find_wireguard()
                if found:
                    self.wireguard_exe = found
                    return True, "WireGuard başarıyla yüklendi."
            except Exception:
                pass

        # Method 2: Direct download from official WireGuard website
        report("[2/2] Resmi siteden WireGuard indiriliyor...")
        installer_url = "https://download.wireguard.com/windows-client/wireguard-installer.exe"
        app_dir = os.path.dirname(os.path.abspath(__file__))
        installer_path = os.path.join(app_dir, "wireguard-installer.exe")
        try:
            with open(installer_path, "ab") as _:
                pass
        except Exception:
            installer_path = os.path.join(tempfile.gettempdir(), "wireguard-installer.exe")

        try:
            req = urllib.request.Request(
                installer_url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) DiscordWARP/1.0"}
            )
            with urllib.request.urlopen(req, timeout=30) as response:
                with open(installer_path, "wb") as out_file:
                    out_file.write(response.read())

            report("WireGuard sürücüsü kuruluyor...")
            # Run installer quietly with administrative rights
            subprocess.run(
                [installer_path, "/quiet"],
                capture_output=True,
                timeout=90,
                creationflags=CREATE_NO_WINDOW
            )

            # Poll for installation completion up to 20 seconds
            for _ in range(10):
                time.sleep(2)
                found = self.find_wireguard()
                if found:
                    self.wireguard_exe = found
                    return True, "WireGuard başarıyla indirildi ve kuruldu."

            # If silent install didn't complete, launch installer GUI
            report("WireGuard kurulum sihirbazı başlatılıyor...")
            subprocess.run([installer_path], timeout=120)
            time.sleep(2)
            found = self.find_wireguard()
            if found:
                self.wireguard_exe = found
                return True, "WireGuard başarıyla kuruldu."

        except Exception as e:
            return False, f"WireGuard otomatik kurulamadı: {str(e)}"

        found = self.find_wireguard()
        if found:
            self.wireguard_exe = found
            return True, "WireGuard başarıyla kuruldu."

        return False, "WireGuard kurulumu tamamlanamadı. Lütfen resmi siteden indirip kurun."

    def is_tunnel_running(self):
        """Checks if the WireGuard tunnel service is active without console popup."""
        try:
            cmd = f"Get-Service -Name 'WireGuardTunnel${self.tunnel_name}' -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Status"
            res = subprocess.run(
                ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", cmd],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=CREATE_NO_WINDOW
            )
            status = res.stdout.strip()
            return status.lower() == "running"
        except Exception:
            return False

    def resolve_discord_domains_via_doh(self):
        """Resolves Discord domains using Cloudflare DoH (DNS over HTTPS) to bypass ISP DNS blocking."""
        import requests
        resolved = {}
        for domain in DISCORD_DOMAINS:
            try:
                resp = requests.get(
                    f"https://cloudflare-dns.com/dns-query?name={domain}&type=A",
                    headers={"Accept": "application/dns-json"},
                    timeout=5
                )
                data = resp.json()
                answers = data.get("Answer", [])
                for ans in answers:
                    if ans.get("type") == 1:  # A record
                        resolved[domain] = ans["data"]
                        break
            except Exception:
                pass
        return resolved

    def add_discord_to_hosts(self):
        """Adds Discord domain→IP mappings to Windows hosts file using DoH resolution."""
        resolved = self.resolve_discord_domains_via_doh()
        if not resolved:
            # Fallback: use known Cloudflare IPs for Discord
            fallback_ip = "162.159.128.233"
            resolved = {domain: fallback_ip for domain in DISCORD_DOMAINS}

        # Read current hosts file
        try:
            with open(HOSTS_PATH, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            content = ""

        # Remove old Discord entries if any
        content = self._strip_discord_entries(content)

        # Build new Discord block
        discord_block = f"\n{HOSTS_MARKER_START}\n"
        for domain, ip in resolved.items():
            discord_block += f"{ip} {domain}\n"
        discord_block += f"{HOSTS_MARKER_END}\n"

        content += discord_block

        try:
            with open(HOSTS_PATH, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception:
            pass

        # Flush DNS cache
        subprocess.run(
            ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", "ipconfig /flushdns"],
            capture_output=True, text=True, timeout=5, creationflags=CREATE_NO_WINDOW
        )

    def remove_discord_from_hosts(self):
        """Removes Discord entries from Windows hosts file."""
        try:
            with open(HOSTS_PATH, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            return

        content = self._strip_discord_entries(content)

        try:
            with open(HOSTS_PATH, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception:
            pass

        # Flush DNS cache
        subprocess.run(
            ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", "ipconfig /flushdns"],
            capture_output=True, text=True, timeout=5, creationflags=CREATE_NO_WINDOW
        )

    def _strip_discord_entries(self, content):
        """Removes the Discord marker block from hosts file content."""
        lines = content.split("\n")
        new_lines = []
        inside_block = False
        for line in lines:
            if HOSTS_MARKER_START in line:
                inside_block = True
                continue
            if HOSTS_MARKER_END in line:
                inside_block = False
                continue
            if not inside_block:
                new_lines.append(line)
        return "\n".join(new_lines)

    def start_tunnel(self):
        """Starts the WireGuard tunnel and adds Discord DNS entries. Skips if already running."""
        if not self.is_installed():
            raise Exception("WireGuard Windows sürücüsü bulunamadı. Lütfen önce WireGuard'ı yükleyin.")

        # If tunnel is already running, just ensure hosts file is up to date
        if self.is_tunnel_running():
            self.add_discord_to_hosts()
            return True

        if not os.path.exists(self.conf_path):
            raise Exception("warp.conf dosyası bulunamadı.")

        # Step 1: Add Discord domains to hosts file (bypass DNS blocking)
        self.add_discord_to_hosts()

        # Step 2: Start WireGuard tunnel
        cmd = f'& "{self.wireguard_exe}" /installtunnelservice "{self.conf_path}"'
        res = subprocess.run(
            ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", cmd],
            capture_output=True,
            text=True,
            timeout=10,
            creationflags=CREATE_NO_WINDOW
        )
        
        time.sleep(1.2)
        if self.is_tunnel_running():
            return True
        else:
            if not self.is_admin():
                raise Exception("Tüneli başlatmak için uygulamanın Yönetici Olarak çalıştırılması gerekir.")
            raise Exception(f"Tünel başlatılamadı: {res.stderr or res.stdout or 'Servis yanıt vermedi'}")

    def stop_tunnel(self):
        """Stops the WireGuard tunnel and removes Discord DNS entries."""
        # Remove Discord from hosts
        self.remove_discord_from_hosts()

        if not self.is_installed():
            return True

        cmd = f'& "{self.wireguard_exe}" /uninstalltunnelservice "{self.tunnel_name}"'
        subprocess.run(
            ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", cmd],
            capture_output=True,
            text=True,
            timeout=10,
            creationflags=CREATE_NO_WINDOW
        )
        return True

    def clean_uninstall_all(self):
        """Forcefully stops and uninstalls all running WireGuard tunnel services."""
        self.stop_tunnel()
        try:
            cmd = f"Stop-Service 'WireGuardTunnel${self.tunnel_name}' -Force -ErrorAction SilentlyContinue; sc.exe delete 'WireGuardTunnel${self.tunnel_name}'"
            subprocess.run(
                ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", cmd],
                capture_output=True,
                text=True,
                timeout=10,
                creationflags=CREATE_NO_WINDOW
            )
        except Exception:
            pass
        return True
