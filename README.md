# TP-Link Powerline Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

HACS-Integration für **TP-Link Powerline-Adapter** — funktioniert mit reinen PLC-Adaptern **ohne WiFi und ohne IP-Adresse**!

## Wie funktioniert das?

Kommuniziert direkt über **HomePlug AV Management Messages** (Layer 2, Ethertype `0x88E1`). Keine IP nötig — genau wie die offizielle tpPLC-App.

```
Home Assistant (Ethernet)
     │
     │ Raw Ethernet (0x88E1)
     │
     ├── ⚡ Adapter #1 (MAC: AA:BB:CC:DD:EE:01)
     │        ⚡ Stromleitung ⚡
     └── ⚡ Adapter #2 (MAC: AA:BB:CC:DD:EE:02)
```

## ✨ Features

- 🔍 **Auto-Discovery** — findet alle Adapter automatisch (Layer 2)
- 🔄 **Dynamische Erkennung** — sucht jede Minute nach neuen Geräten
- 📊 **TX/RX Datenraten** pro Adapter (Mbit/s PHY Rate)
- 🔢 **Adapter-Anzahl** (Online + Gesamt)
- 📡 **Online-Status** pro Adapter
- 📡 **Firmware-Version** jedes Adapters
- 💡 **LED-Steuerung** pro Adapter (experimentell)

## ⚠️ Voraussetzungen

Raw Socket Zugriff (**CAP_NET_RAW**) + **Ethernet-Kabel** (WiFi geht nicht für Layer 2!)

### Docker
```yaml
services:
  homeassistant:
    cap_add:
      - NET_RAW
    network_mode: host
```

### HAOS
Sollte out-of-the-box funktionieren.

### Python venv
```bash
sudo setcap cap_net_raw+ep $(readlink -f $(which python3))
```

## 📦 Installation

1. `custom_components/tplink_powerline` nach `config/custom_components/` kopieren
2. HA neu starten
3. **Einstellungen** → **Geräte & Dienste** → **Integration hinzufügen** → **"TP-Link Powerline"**
4. Klick auf **Weiter** → Adapter werden automatisch gefunden

## 📊 Entities

### Netzwerk-Übersicht
| Entity | Beschreibung |
|--------|-------------|
| Powerline TX Gesamt | Summe TX-Raten aller Adapter |
| Powerline RX Gesamt | Summe RX-Raten aller Adapter |
| Powerline Adapter Online | Anzahl aktuell erreichbarer Adapter |
| Powerline Adapter Gesamt | Anzahl aller je gesehenen Adapter |

### Pro Adapter (wird automatisch als eigenes Gerät angelegt)
| Entity | Beschreibung |
|--------|-------------|
| TX Rate | PHY TX Rate in Mbit/s |
| RX Rate | PHY RX Rate in Mbit/s |
| Status | Online / Offline |
| LED | Ein/Aus (experimentell) |

### Dynamische Erkennung
Neue Adapter werden **automatisch alle 60 Sekunden** gesucht. Wenn ein neuer Adapter eingesteckt wird, erscheinen seine Entities nach spätestens einer Minute in Home Assistant.

## 🐛 Debug

```yaml
logger:
  logs:
    custom_components.tplink_powerline: debug
```

## 📝 Hinweise

- **LED-Steuerung** ist experimentell — die exakte HomePlug AV MME für LED-Kontrolle ist noch nicht vollständig verifiziert. Ein Wireshark-Capture (Filter: `eth.type == 0x88e1`) beim LED-Umschalten über die Windows TP-Link Utility wäre hilfreich!
- HA muss per **Ethernet** verbunden sein (WiFi kann keine Layer 2 HomePlug AV Frames senden)
