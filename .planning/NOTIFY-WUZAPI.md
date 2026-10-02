# Notify ciele a WuzAPI — otvorené

**Stav:** otvorené, 2026-10-02. Zistené na živom HAOS, kód FlyNow sa nemenil.

FlyNow 1.3.0 pri prechode NO-GO → GO volá `notify.send_message` (`custom_components/flynow/notifications.py`). Záznam lokality Malý Madaras má stále predvolené ciele z `const.py`:

- `notify.crew_phone`
- `notify.pilot_phone`
- `notify.whatsapp_group`

Žiadna z týchto entít na HAOS neexistuje. Varovanie `Referenced entities … are missing` padlo 2026-10-02 o 01:48 a znova pri štarte o 10:38. Správa posádke, pilotovi ani na WhatsApp neodišla.

## Čo overiť

WuzAPI nie je `notify` entita. WhatsApp na tomto HAOS ide cez Žofku, `shell_command.zofka_send_whatsapp` (repo HomeAssistant-P51). Do poľa `whatsapp_notifier` sa WuzAPI zapísať nedá, kým FlyNow nebude volať tú cestu priamo.

Reálne `notify` entity sú len telefóny mobilnej aplikácie: `notify.sm_a715f`, `notify.mar_lx1b`, `notify.honor_70_miro`, `notify.danko`. Posádka a pilot sa dajú prepnúť na dva z nich v config flow. WhatsApp ostáva na overenie WuzAPI.
