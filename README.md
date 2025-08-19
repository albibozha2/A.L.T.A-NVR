# A.L.T.A NVR - Advanced Linux-based Total Analytics Network Video Recorder

**Krijuar nga Albi Bozha dhe Florian Tani**

## Përshkrimi i Projektit

A.L.T.A NVR është një sistem i avancuar regjistrimi dhe analize video i bazuar në Linux, i krijuar për të ofruar zgjidhje të plotë për monitorimin dhe analizën e videove të sigurisë. Ky sistem përdor teknologjitë më të fundit të inteligjencës artificiale për detektimin dhe analizën e ngjarjeve në kohë reale.

## 🚀 Karakteristikat Kryesore

- **Regjistrim Inteligjent**: Regjistrim i aktivizuar nga lëvizja ose ngjarjet
- **Analizë AI**: Detektim i objekteve dhe njerëzve përmes YOLO
- **Ndërfaqe Web**: Ndërfaqe moderne dhe miqësore për përdoruesin
- **WebSocket**: Transmetim i të dhënave në kohë reale
- **Docker Support**: Instalim i lehtë përmes Docker
- **Multi-kamera**: Mbështetje për shumë kamera njëkohësisht
- **Ruajtje Cloud**: Sinkronizim me shërbime cloud

## 📋 Kërkesat Sistemore

- **OS**: Linux (Ubuntu 20.04+ rekomandohet)
- **Python**: 3.11+
- **Docker**: 20.10+
- **RAM**: Min. 4GB (8GB rekomandohet)
- **Hapësirë Disku**: Min. 50GB për regjistrime

## 🛠️ Instalimi

### Metoda 1: Instalim me Docker (Rekomandohet)

```bash
# Klononi repository
git clone https://github.com/albibozha2/A.L.T.A-NVR.git
cd A.L.T.A-NVR

# Ndërtimi i imazhit Docker
./docker_build.sh

# Nisja e aplikacionit
docker-compose up -d
```

### Metoda 2: Instalim Manual

```bash
# Instalimi i dependencies
pip install -r requirements.txt

# Konfigurimi
cp config/config.yaml.example config/config.yaml

# Nisja e aplikacionit
python src/main.py
```

## 🌐 Aksesi

Pas instalimit, aplikacioni do të jetë i aksesueshëm në:

- **Web Interface**: http://localhost:8080
- **API Documentation**: http://localhost:8080/docs
- **Health Check**: http://localhost:8080/health

## ⚙️ Konfigurimi

Konfigurimi bëhet nëpërmjet skedarit `config/config.yaml`:

```yaml
server:
  host: "0.0.0.0"
  port: 8080

cameras:
  - name: "Kamera Hyrje"
    url: "rtsp://user:pass@ip:port/stream"
    
detection:
  enabled: true
  classes: ["person", "car", "truck"]
```

## 📊 API Endpoints

- `GET /api/cameras` - Lista e kamerave
- `POST /api/recordings/start` - Fillim regjistrimi
- `GET /api/events` - Ngjarjet e detektuara
- `WS /ws` - WebSocket për të dhëna në kohë reale

## 🎯 Shembuj Përdorimi

### Shtimi i një kamere të re
```bash
curl -X POST http://localhost:8080/api/cameras \
  -H "Content-Type: application/json" \
  -d '{"name": "Kamera Parking", "url": "rtsp://192.168.1.100:554/stream"}'
```

### Marrja e regjistrimeve
```bash
curl http://localhost:8080/api/recordings?start=2024-01-01&end=2024-01-02
```

## 🔧 Zhvillimi

### Struktura e Projektit
```
A.L.T.A-NVR/
├── src/
│   ├── core/          # Logjika kryesore
│   ├── api/           # API endpoints
│   └── websocket/     # WebSocket handlers
├── config/            # Skedarët e konfigurimit
├── docs/              # Dokumentacioni
├── docker/            # Skedarët Docker
└── web/               # Ndërfaqja web
```

### Kontributi
Për të kontribuar në projekt:
1. Fork repository
2. Krijo branch-in tënd (`git checkout -b feature/AmazingFeature`)
3. Commit ndryshimet (`git commit -m 'Add some AmazingFeature'`)
4. Push në branch (`git push origin feature/AmazingFeature`)
5. Hap një Pull Request

## 📞 Mbështetje

Për probleme ose pyetje:
- **Email**: albi.bozha@example.com, florian.tani@example.com
- **Issues**: [GitHub Issues](https://github.com/albibozha2/A.L.T.A-NVR/issues)
- **Discussions**: [GitHub Discussions](https://github.com/albibozha2/A.L.T.A-NVR/discussions)

## 📄 Licenca

Ky projekt është nën licencën MIT. Shih skedarin [LICENSE](LICENSE) për detaje.

## 🙏 Falënderime

- Faleminderit të gjithë kontribuesve
- Komunitetit open source për libraritë e përdorura
- YOLO për modelin e detektimit

---

**Krijuar me ❤️ nga Albi Bozha dhe Florian Tani**
