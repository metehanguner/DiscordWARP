# 🎮 Discord WARP Bypass (Sıfır Ping Kaybı!)

<p align="center">
  <img src="icon.png" width="120" height="120" alt="Discord WARP Logo">
</p>

Discord erişim engellerini **oyunlardaki pingini zerre kadar etkilemeden** ve **tarayıcı hızını düşürmeden** aşmak için geliştirilmiş, akıllı ve taşınabilir bir Windows aracıdır.

Piyasadaki diğer VPN'lerin aksine tüm bilgisayar internetini yavaşlatmaz. **Sadece ve sadece Discord'un** internet trafiğini Cloudflare WARP tünelinden geçirir. Geri kalan her şey (oyunlar, Chrome, Spotify) normal internetinizden akmaya devam eder.

### 🚀 Neden Farklı?
* **Oyunlarda %0 Ping Artışı:** Valorant, CS2, LoL veya herhangi bir oyun tünelden geçmez. Tıpkı VPN kapalıymış gibi orijinal pinginizle oynarsınız.
* **DNS Engellerini Aşar (DoH):** Sistem DNS ayarlarınızı değiştirmez. Diğer engelli siteler açılmaz, sadece Discord sunucularını Cloudflare DNS (DoH) üzerinden gizlice çözümleyerek ISS engellerini atlar.
* **Kurulum Yok, Tek Bir EXE:** Python, ek kütüphane veya karışık kodlara ihtiyacınız yok. İndirdiğiniz `.exe` dosyasına çift tıklayın ve kullanmaya başlayın.
* **Otomatik Sürücü Yükleme:** Bilgisayarınızda WireGuard yoksa, arka planda hiçbir şey hissettirmeden Windows'un resmi paket yöneticisiyle otomatik kurar.

### 🛠️ Özellikler
- **Split Tunneling (Bölünmüş Tünelleme):** 20'den fazla özel Discord IP aralığına sadece Discord trafiğini yönlendirir.
- **Tek Tıkla Bağlantı:** Şalteri açın, her şeyi o halletsin. Adım adım neler olduğunu size göstersin.
- **Sessiz Çalışma (System Tray):** Çarpıya bastığınızda kapanmaz, sağ alt köşeye küçülür ve arka planda sizi korumaya devam eder.
- **Kalıcı Windows Servisi:** Uygulamayı tamamen kapatsanız bile Discord koruması (VPN) açık kalmaya devam eder.
- **Orijinal Cloudflare WARP:** Ücretsiz ve sınırsız, resmi Cloudflare altyapısını kullanır.

### 💻 Nasıl Kullanılır?
1. 📥 **[DiscordWARP.exe İndir](https://github.com/metehanguner/DiscordWARP/raw/main/DiscordWARP.exe)** (Kurulum gerektirmez, doğrudan çalışır).
2. Program otomatik olarak yönetici izni (UAC) isteyecektir, izin verin. (WireGuard sistem servisini başlatmak için şarttır).
3. Ekranda **"Bağlan"** şalterini açın.
4. Tünel açıldığında Discord'unuz anında aktifleşecektir! Uygulamayı kapatıp arka plana gönderebilirsiniz. 

**Not:** Tüneli tamamen sistemden kaldırmak ve programı kapatmak isterseniz uygulamanın içindeki *"Tünel Servisini Kaldır"* butonunu kullanabilirsiniz.

---
*Bu proje açık kaynaklıdır ve Python ile geliştirilmiştir.*
