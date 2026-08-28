import os
import json
import time
import base64
import requests
import uuid
from datetime import datetime, timezone
from cryptography.hazmat.primitives.asymmetric import x25519

CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_FILE = os.path.join(CONFIG_DIR, "warp_credentials.json")
CONF_FILE = os.path.join(CONFIG_DIR, "warp.conf")

# Discord Voice, Gateway, API and Cloudflare CDN CIDR Blocks for Split Tunneling
DISCORD_ALLOWED_IPS = [
    "66.22.192.0/18",       # Discord Voice & WebRTC Media
    "162.159.128.0/17",     # Discord Gateway & API
    "162.159.0.0/17",       # Cloudflare / Discord Edge
    "104.16.0.0/12",        # Discord CDN & Assets
    "172.64.0.0/13",        # Discord API Nodes
    "173.245.48.0/20",      # Cloudflare Edge
    "188.114.96.0/20",      # European Edge
    "190.93.240.0/20",      # Edge Routing
    "197.234.240.0/22",     # Edge Routing
    "198.41.128.0/17",      # Edge Routing
    "2606:4700::/32"        # Discord IPv6
]

class WarpAPI:
    def __init__(self):
        self.api_url = "https://api.cloudflareclient.com/v0a2158/reg"
        self.headers = {
            "User-Agent": "1.1.1.1/24.1",
            "CF-Client-Version": "a-6.30-2158",
            "Content-Type": "application/json; charset=UTF-8"
        }
        self.data = self.load_credentials()

    def generate_keys(self):
        """Generates X25519 private and public keys in base64."""
        priv_key = x25519.X25519PrivateKey.generate()
        pub_key = priv_key.public_key()
        
        priv_b64 = base64.b64encode(priv_key.private_bytes_raw()).decode('utf-8')
        pub_b64 = base64.b64encode(pub_key.public_bytes_raw()).decode('utf-8')
        return priv_b64, pub_b64

    def register(self, force_new=False, mode="discord"):
        """Registers device with Cloudflare WARP and obtains WireGuard config."""
        if not force_new and self.data and self.data.get("token"):
            self.generate_conf_file(mode=mode)
            return self.data

        priv_b64, pub_b64 = self.generate_keys()
        iso_time = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.000Z')

        payload = {
            "key": pub_b64,
            "install_id": "",
            "fcm_token": "",
            "tos": iso_time,
            "model": "Android",
            "serial_number": "",
            "locale": "en_US"
        }

        try:
            resp = requests.post(self.api_url, json=payload, headers=self.headers, timeout=15)
            if resp.status_code == 200:
                res = resp.json()
                config = res.get("config", {})
                peers = config.get("peers", [{}])[0]
                interface = config.get("interface", {}).get("addresses", {})

                raw_endpoint = peers.get("endpoint", {}).get("host") or peers.get("endpoint", {}).get("v4") or "162.159.192.1:2408"
                if ":" not in raw_endpoint:
                    raw_endpoint = f"{raw_endpoint}:2408"
                elif raw_endpoint.endswith(":0"):
                    raw_endpoint = f"{raw_endpoint.split(':')[0]}:2408"

                ipv4_val = interface.get("v4", "172.16.0.2/32")
                if "/" not in ipv4_val:
                    ipv4_val = f"{ipv4_val}/32"

                ipv6_val = interface.get("v6", "2606:4700:110:8e50:84c5:1d74:ea67:1cfa/128")
                if "/" not in ipv6_val:
                    ipv6_val = f"{ipv6_val}/128"

                self.data = {
                    "warp_id": res.get("id"),
                    "token": res.get("token"),
                    "private_key": priv_b64,
                    "public_key": pub_b64,
                    "peer_public_key": peers.get("public_key", "bmXOC+F1FxEMF9dyiK2H5/1SUtzH0JuVo51h2wPfgyo="),
                    "peer_endpoint": raw_endpoint,
                    "assigned_ipv4": ipv4_val,
                    "assigned_ipv6": ipv6_val
                }
            else:
                self.data = {
                    "warp_id": str(uuid.uuid4()),
                    "token": "local_token",
                    "private_key": priv_b64,
                    "public_key": pub_b64,
                    "peer_public_key": "bmXOC+F1FxEMF9dyiK2H5/1SUtzH0JuVo51h2wPfgyo=",
                    "peer_endpoint": "162.159.192.1:2408",
                    "assigned_ipv4": "172.16.0.2/32",
                    "assigned_ipv6": "2606:4700:110:8805:a4bb:a537:4149:7b3c/128"
                }
        except Exception:
            self.data = {
                "warp_id": str(uuid.uuid4()),
                "token": "local_token",
                "private_key": priv_b64,
                "public_key": pub_b64,
                "peer_public_key": "bmXOC+F1FxEMF9dyiK2H5/1SUtzH0JuVo51h2wPfgyo=",
                "peer_endpoint": "162.159.192.1:2408",
                "assigned_ipv4": "172.16.0.2/32",
                "assigned_ipv6": "2606:4700:110:8805:a4bb:a537:4149:7b3c/128"
            }

        self.save_credentials()
        self.generate_conf_file(mode=mode)
        return self.data

    def generate_conf_file(self, mode="discord"):
        """Creates the WireGuard .conf file with Full or Split Tunneling (Discord-only)."""
        if not self.data:
            return None

        if mode == "discord":
            allowed_ips = ", ".join(DISCORD_ALLOWED_IPS)
            # Discord modunda DNS değiştirme - ISP'nin DNS engelleri korunsun
            dns_line = ""
        else:
            allowed_ips = "0.0.0.0/0, ::/0"
            dns_line = "DNS = 1.1.1.1, 1.0.0.1, 2606:4700:4700::1111, 2606:4700:4700::1001"

        conf_content = f"[Interface]\nPrivateKey = {self.data['private_key']}\nAddress = {self.data['assigned_ipv4']}, {self.data['assigned_ipv6']}\n"
        if dns_line:
            conf_content += f"{dns_line}\n"
        conf_content += f"MTU = 1280\n\n[Peer]\nPublicKey = {self.data['peer_public_key']}\nAllowedIPs = {allowed_ips}\nEndpoint = {self.data['peer_endpoint']}\n"

        with open(CONF_FILE, "w", encoding="utf-8") as f:
            f.write(conf_content)
        return CONF_FILE

    def save_credentials(self):
        with open(CREDENTIALS_FILE, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=4)

    def load_credentials(self):
        if os.path.exists(CREDENTIALS_FILE):
            try:
                with open(CREDENTIALS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def check_health(self):
        """Tests connection to Cloudflare trace endpoint and measures latency."""
        try:
            start = time.time()
            resp = requests.get("https://www.cloudflare.com/cdn-cgi/trace", timeout=5)
            latency_ms = int((time.time() - start) * 1000)
            if resp.status_code == 200:
                trace_data = {}
                for line in resp.text.strip().split("\n"):
                    if "=" in line:
                        k, v = line.split("=", 1)
                        trace_data[k] = v
                
                is_warp = trace_data.get("warp") in ["on", "plus"] or "cloudflare" in trace_data.get("h", "")
                return {
                    "success": True,
                    "ping_ms": latency_ms,
                    "ip": trace_data.get("ip", ""),
                    "is_warp": is_warp,
                    "loc": trace_data.get("loc", "")
                }
        except Exception:
            pass
        return {"success": False, "ping_ms": -1, "ip": "", "is_warp": False, "loc": ""}
