# Contributing

Danke für deinen Beitrag zu **ha-tp-link-powerline**! 🙌

## Projektstatus

Diese Integration ist aktuell **experimentell**.

Der stabilste Teil ist derzeit die **Erkennung von Powerline/dLAN-Adaptern**.
Features wie LED-Steuerung können je nach Modell/Chipset abweichen.

## So meldest du Bugs am besten

Bitte nutze das Bug-Template in `.github/ISSUE_TEMPLATE/bug_report.yml` und gib möglichst an:

- Home Assistant Version
- Integrationsversion
- Adapter-Modelle + Firmware
- reproduzierbare Schritte
- relevante Logs
- Vergleich mit der Windows-App **tpPLC** (falls verfügbar)

## Debug-Logs aktivieren

```yaml
logger:
  logs:
    custom_components.tplink_powerline: debug
```

## Wireshark (optional, aber sehr hilfreich)

Wenn du LED/Protokollprobleme analysieren willst, ist ein Capture oft der schnellste Weg:

- Start Wireshark auf dem Interface, an dem die Powerline-Adapter sichtbar sind
- Setze Display-Filter auf:

```text
eth.type == 0x88e1 or eth.type == 0x8912
```

- Führe die Aktion aus (z.B. LED in tpPLC toggeln)
- Speichere den Mitschnitt als `.pcapng`
- Bitte vor Upload sensible Daten prüfen/anonymisieren (MAC/Seriennummern etc.)

## Pull Requests

Kleine, fokussierte PRs sind ideal:

1. Problem kurz beschreiben
2. Änderung klar eingrenzen
3. Test/Validierung hinzufügen (mindestens `python -m compileall custom_components/tplink_powerline`)
4. Bei Protokolländerungen: Logs oder Capture-Ausschnitte beilegen
