#!/usr/bin/env python3
# param_protocol.py
# MAVLink parametre protokolunu gosterir: bir parametreyi okur (PARAM_REQUEST_READ
# -> PARAM_VALUE), degerini degistirir (PARAM_SET -> PARAM_VALUE onayi), sonra
# eski degerine geri yazar. Ornek parametre: ARMING_CHECK.
# Kullanim: python3 param_protocol.py tcp:127.0.0.1:5760
# Yalnizca kendi SITL laboratuvarinda calistir.

import sys
import time
from pymavlink import mavutil

CONN = sys.argv[1] if len(sys.argv) > 1 else "tcp:127.0.0.1:5760"
NAME = b"ARMING_CHECK"

m = mavutil.mavlink_connection(CONN)
m.wait_heartbeat(timeout=30)
if m.target_component == 0:
    m.target_component = 1
print("[+] baglanildi sys=%d" % m.target_system)


def read_param():
    # Belirli bir parametreyi adiyla okur, gelen PARAM_VALUE'yu dondurur
    m.mav.param_request_read_send(m.target_system, m.target_component, NAME, -1)
    return m.recv_match(type="PARAM_VALUE", blocking=True, timeout=5)


def set_param(value):
    # Parametreye yeni deger yazar; arac uygulanmis halini PARAM_VALUE ile geri yollar
    m.mav.param_set_send(m.target_system, m.target_component, NAME, float(value),
                         mavutil.mavlink.MAV_PARAM_TYPE_INT32)
    return m.recv_match(type="PARAM_VALUE", blocking=True, timeout=5)


# 1-2: oku
print("")
print("[1] >> PARAM_REQUEST_READ name=%s" % NAME.decode())
pv = read_param()
orig = pv.param_value if pv else 1.0
if pv:
    print("[2] << PARAM_VALUE  id=%s  value=%.1f  type=%d  (%d/%d)"
          % (pv.param_id, pv.param_value, pv.param_type, pv.param_index + 1, pv.param_count))

# 3-4: 0 yaz (pre-arm denetimlerini kapatir)
print("")
print("[3] >> PARAM_SET name=%s value=0" % NAME.decode())
pv = set_param(0)
if pv:
    print("[4] << PARAM_VALUE (onay)  id=%s  value=%.1f" % (pv.param_id, pv.param_value))

# 5-6: eski degere geri yaz
print("")
print("[5] >> PARAM_SET %s geri eskiye" % NAME.decode())
pv = set_param(orig)
if pv:
    print("[6] << PARAM_VALUE (geri)  id=%s  value=%.1f" % (pv.param_id, pv.param_value))
