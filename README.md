# mavlink-sitl-lab

mucahic.com'daki "Aviyonik Siber Guvenligi #1: SITL ve MAVLink'e Ilk Dokunus"
yazisinin lab scriptleri. Hepsi ArduPilot SITL uzerinde pymavlink ile calisir.

## Scriptler

- `mavlink_first_touch.py` SITL'e baglanir, HEARTBEAT'i cozer, telemetri orneklemesi yapar, force-arm + 20m kalkis verir.
- `disarm_in_flight.py` 20m'de asili araca ayni kimlik dogrulamasiz kanaldan force-disarm gonderir; arac serbest duser.
- `mission_upload.py` gorev protokolu: MISSION_COUNT / MISSION_REQUEST / MISSION_ITEM_INT / MISSION_ACK akisiyla uc waypoint yukler.
- `param_protocol.py` parametre protokolu: ARMING_CHECK okur, degistirir, geri yazar (PARAM_REQUEST_READ / PARAM_SET / PARAM_VALUE).
- `reboot_dos_poc.py` kimlik dogrulamasiz uzaktan DoS PoC (PREFLIGHT_REBOOT_SHUTDOWN failure-injection). Bildirim: ArduPilot issue #33253.

## Kullanim

```
pip install pymavlink
python3 mavlink_first_touch.py tcp:127.0.0.1:5760
python3 disarm_in_flight.py    tcp:127.0.0.1:5762
python3 mission_upload.py      tcp:127.0.0.1:5760
python3 param_protocol.py      tcp:127.0.0.1:5760
```

## Uyari

`reboot_dos_poc.py` hedef otopilot surecini cokertir. Bu betikleri yalnizca kendi
SITL laboratuvarinda veya yazili izin verilen test ortaminda calistir.

Yazi: https://mucahic.com/dossier-11.html
