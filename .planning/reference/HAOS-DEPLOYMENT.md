# HAOS deployment reference

Canonical deployment info for the FlyNow HAOS instance. Read this before touching SSH/rsync/tar commands.

## Target

| Field | Value |
|---|---|
| Host | `192.168.68.111` |
| User | `miro` (uid 1000, in `wheel`, sudo NOPASSWD) |
| SSH port | **22** (NOT 22222 — standard sshd, not the HA SSH add-on ingress) |
| Auth | SSH key only (password auth not used) |
| HA Core | 2026.4.3 |
| Python | 3.12.13 |
| HAOS | Supervisor + HACS 2.0.5 present |
| Location | 48.202983, 16.97590934328933 ("DOMA", near Bratislava), Europe/Prague, sk |

## SSH key

| Field | Value |
|---|---|
| Private key | `C:\Users\dwdv8103\.ssh\id_ed25519_flynow` (no passphrase) |
| Public key label in `authorized_keys` | `flynow-deploy@OB-OB3103712` |
| Also authorized | `homeassistant-p51` (user's other PC) |

## Connect

```bash
ssh -i ~/.ssh/id_ed25519_flynow -p 22 miro@192.168.68.111
```

Note: `/config` is `root:root 755`. Use `sudo` (NOPASSWD works) or wrap rsync with `--rsync-path="sudo rsync"`.
The `ha` CLI fails in this SSH session with "unauthorized: missing or invalid API token" — supervisor token is not exposed here. Use filesystem inspection (`/config/.storage/*.json`) instead, or restart HA via the UI.

## Deployment paths

| Source | Target on HAOS |
|---|---|
| `custom_components/flynow/` | `/config/custom_components/flynow/` |
| `lovelace/flynow-card/dist/` | `/config/www/flynow-card/` |

Card served at `/local/flynow-card/flynow-card.js`. Chosen intentionally — NOT `/config/www/community/` (HACS-managed).

## Deploy commands (no rsync — tar over SSH)

```bash
# Integration
tar --exclude='__pycache__' --exclude='*.pyc' --exclude='.ruff_cache' --exclude='.mypy_cache' \
  -czf - -C custom_components flynow \
  | ssh -i ~/.ssh/id_ed25519_flynow -p 22 miro@192.168.68.111 \
    "sudo mkdir -p /config/custom_components && sudo tar xzf - -C /config/custom_components/"

# Lovelace card (requires npm run build in lovelace/flynow-card first)
tar -czf - -C lovelace/flynow-card/dist . \
  | ssh -i ~/.ssh/id_ed25519_flynow -p 22 miro@192.168.68.111 \
    "sudo mkdir -p /config/www/flynow-card && sudo tar xzf - -C /config/www/flynow-card/"
```

Rationale: rsync is not installed in Git Bash on dev machine; `scp -r` can't do --delete; `tar | ssh` is simplest equivalent.

## Post-deploy

1. **Reload integration:** Settings → Devices & Services → FlyNow → 3 dots → Reload
2. **If Python code changed:** Full HA restart needed — Settings → System → Restart Home Assistant (UI path, since `ha` CLI doesn't work from SSH session). Downtime ~30–60 s.

## Ready-to-use HA services (skip re-configuring)

These already exist on the target — point FlyNow config flow at them:

- **Crew/pilot push:** `notify.mobile_app_fne_nx9` (Honor 70 Miro), `notify.mobile_app_sm_a715f` (Samsung A71), `notify.mobile_app_mar_lx1b`
- **Google Calendar:** `calendar.balonove_akcie` (dedicated balloon events calendar, account `mburdych@gmail.com`)
- **WhatsApp (CallMeBot):** `notify.whatsapp_callmebot` — already wired in `configuration.yaml` with phone + API key, no extra setup

## Known project status at time of first deploy (2026-04-24)

- Branch: `master` @ `31dcd9a` (Phase 3 merged via PR #1 into `mburdych/FlyNow`)
- All 4 phases complete, 35/35 pytest passes on dev machine
- First config flow run uncovered two bugs — both fixed post-deploy (not yet pushed to GitHub as of this writing):
  - `config_flow.py` — schema used bare `float`/`int` (voluptuous isinstance check); replaced with `vol.Coerce(...)`
  - `coordinator.py` — passed `logger=None` to `DataUpdateCoordinator`; now uses `_LOGGER = logging.getLogger(__name__)`
- Outstanding TODO: `.planning/todos/pending/2026-04-24-config-flow-missing-labels-and-slovak-translations.md` — config flow UI shows raw variable names in English; needs `strings.json` data sections + `translations/sk.json`

## Production hotfix timeline (2026-04-24 evening)

After the first live deploy, several production issues were identified and resolved directly on the HAOS target:

1. **Open-Meteo HTTP 400**
   - Cause: unsupported hourly field `ceiling`.
   - Fix: switched API request to `cloud_base`, improved error message logging.
2. **Runtime crash in analyzer**
   - Error: `'<‘ not supported between instances of 'NoneType' and 'NoneType'`.
   - Cause: unfiltered `None` values in weather arrays.
   - Fix: added numeric sanitization and safe min/max helpers.
3. **Config entry setup failure**
   - Error: `ModuleNotFoundError: Platform flynow.binary_sensor not found`.
   - Cause: `PLATFORMS` expected `binary_sensor.py` while code existed only in `sensor.py`.
   - Fix: added `custom_components/flynow/binary_sensor.py`.
4. **Lovelace card load failure**
   - Error: `i.setConfig is not a function`.
   - Fix: implemented `setConfig()` and `getCardSize()` in custom card class.
5. **Card condition display mismatch**
   - Symptom: `n/a` values despite backend data present.
   - Fix: corrected active-window key mapping and `ok`/`pass` condition flag handling.
6. **Regulatory alignment update**
   - Requirement decision: operate per EASA/SERA civil twilight limits (not sunset-only).
   - Implementation: window builder now computes `day_start`/`day_end` from civil twilight and exposes these in attributes/UI.

### SSH transport reliability note

Observed intermittent `Corrupted MAC on input` with default SSH settings from this workstation.
Stable workaround used for deploy commands:

```bash
ssh -o Ciphers=aes128-ctr -o MACs=hmac-sha2-256-etm@openssh.com ...
```

For binary payload deploy, a Python `subprocess.run(..., input=archive_bytes)` stream proved more reliable than shell pipe/scp on this setup.

## Verify after deploy

```bash
# Syntax check on remote
ssh -i ~/.ssh/id_ed25519_flynow -p 22 miro@192.168.68.111 \
  "sudo python3 -c 'import ast, glob
for f in sorted(glob.glob(\"/config/custom_components/flynow/*.py\")):
    ast.parse(open(f).read()); print(\"OK\", f)'"

# Check files landed
ssh -i ~/.ssh/id_ed25519_flynow -p 22 miro@192.168.68.111 \
  "sudo ls -la /config/custom_components/flynow/ /config/www/flynow-card/"

# Tail HA log for FlyNow errors (last 50 lines containing flynow)
ssh -i ~/.ssh/id_ed25519_flynow -p 22 miro@192.168.68.111 \
  "sudo grep -i flynow /config/home-assistant.log 2>/dev/null | tail -50"
```
