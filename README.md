# 📈 Tourenplanimport Timo Tool

Dieses Projekt automatisiert den täglichen Import einer neuen RESERV-CSV-Datei von einem SMB-Netzlaufwerk in eine MySQL-Datenbank. Es nutzt eine virtuelle Python-Umgebung und wird täglich über einen Cronjob ausgeführt.

## 📂 Projektstruktur

```bash
/opt/lm_reserved_file2googlesheet/
├── lm_reserved_file2googlesheet.py  # Hauptskript
├── .env                             # Umgebungsvariablen für DB und Pfade
├── venv/                            # Virtuelle Umgebung
```

## 🧱 Einrichtung

### 1. Virtuelle Umgebung vorbereiten

```bash
cd /opt/lm_reserved_file2googlesheet
python3 -m venv venv
source venv/bin/activate
pip pip install python-dotenv mysql-connector-python requests
```

### 2. CIFS für SMB-Zugriff installieren

```bash
sudo apt update
sudo apt install cifs-utils
```

### 3. SMB-Zugangsdaten sicher speichern

```bash
sudo nano /root/.smbcredentials
```

Inhalt:

```
username=DEIN_USER
password=DEIN_PASS
```

```bash
sudo chmod 600 /root/.smbcredentials
```

### 4. Automount über `/etc/fstab`

```bash
sudo nano /etc/fstab
```

```
//192.168.230.27/LogoMate_Transfer/LogoMate_Import/SAP_HEP_LIVE/logomate_reservedstocks_live /mnt/logomate_reservedstocks_live cifs credentials=/root/.smbcredentials,iocharset=utf8,uid=1000,gid=1000,file_mode=0644,dir_mode=0755,nofail 0 0
```

```
sudo mkdir -p /mnt/logomate_reservedstocks_live
```

```bash
sudo mount -a
```

### 5. Umgebungsvariablen konfigurieren

```bash
nano /opt/lm_reserved_file2googlesheet/.env
```

Beispiel:

```
MYSQL_HOST=dedi848.your-server.de
MYSQL_PORT=3306
MYSQL_USER=xxxx
MYSQL_PASSWORD=xxxxx
MYSQL_DATABASE=xxxxx
LOCAL_PATH_TOURENPLAN=/mnt/tourenplan_share
GOOGLE_CHAT_WEBHOOK_URL=https://chat.googleapis.com/v1/spaces/AAA.../messages?key=...&token=...

```

## 💡 lm_reservedfile2googlecheet.py

Importiert die neueste Datei und aktualisiert die Tabelle `lm_reserved_file`. Fügt jeder Zeile den aktuellen Timestamp hinzu. 
Speichere folgendes Skript unter `/opt/lm_reserved_file2googlesheet/lm_reservedfile2googlecheet.py` und stelle sicher, dass es ausführbar ist:

```bash
chmod +x /opt/lm_reserved_file2googlesheet/lm_reservedfile2googlecheet.py
```


## ▶️ Manuell ausführen

```bash
/opt/lm_reserved_file2googlesheet/venv/bin/python /opt/lm_reserved_file2googlesheet/lm_reservedfile2googlecheet.py
```

## 🧩 Systemd-Service

Um das Skript regelmäßig oder beim Systemstart auszuführen, kann ein `systemd`-Service eingerichtet werden.

### 1. Service-Datei erstellen

```bash
sudo nano /etc/systemd/system/lm_reserved_file2googlesheet.service
```

#### Inhalt:

```ini
[Unit]
Description=CSV Datei importieren
Wants=network-online.target
After=network-online.target

[Service]
Type=simple
WorkingDirectory=/opt/lm_reserved_file2googlesheet/
ExecStart=/opt/lm_reserved_file2googlesheet/venv/bin/python /opt/lm_reserved_file2googlesheet/lm_reservedfile2googlecheet.py
EnvironmentFile=/opt/lm_reserved_file2googlesheet/.env
StandardOutput=append:/var/log/lm_reserved_file2googlesheet.log
StandardError=append:/var/log/lm_reserved_file2googlesheet.log

[Install]
WantedBy=multi-user.target
```

---

### 2. Service aktivieren und starten

```bash
sudo systemctl daemon-reexec
sudo systemctl daemon-reload
sudo systemctl enable lm_reserved_file2googlesheet.service
sudo systemctl start lm_reserved_file2googlesheet.service
```

---

### 3. Service prüfen

Status anzeigen:

```bash
sudo systemctl status lm_reserved_file2googlesheet.service
```

Logs live ansehen:

```bash
journalctl -u lm_reserved_file2googlesheet.service -f
```

---


## ⏰ Optional: systemd-Timer (statt Cronjob)

Du kannst einen systemd-Timer verwenden, um den Export regelmäßig auszuführen (z. B. täglich alle 4 Stunden).

### 1. Timer-Datei erstellen

```bash
sudo nano /etc/systemd/system/lm_reserved_file2googlesheet.timer
```

#### Inhalt:

```ini
[Unit]
Description=Timer für Reserved-Import alle 4 Stunden

[Timer]
OnCalendar=*-*-* 00,04,08,12,16,20:00
Persistent=true
Unit=lm_reserved_file2googlesheet.service

[Install]
WantedBy=timers.target

```

---

### 2. Timer aktivieren und starten

```bash
sudo systemctl daemon-reexec
sudo systemctl daemon-reload
sudo systemctl enable --now lm_reserved_file2googlesheet.timer
```

---

### 3. Timer prüfen

Liste aktiver Timer anzeigen:

```bash
systemctl list-timers
```

Status eines bestimmten Timers anzeigen:

```bash
systemctl status lm_reserved_file2googlesheet.timer
```

Logs des Services anzeigen:

```bash
journalctl -u lm_reserved_file2googlesheet.service
```
