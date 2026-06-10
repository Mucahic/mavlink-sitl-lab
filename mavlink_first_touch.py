#!/usr/bin/env python3
# mavlink_first_touch.py
# ArduPilot SITL'e baglanir, ilk HEARTBEAT'i cozer, biraz telemetri
# orneklemesi yapar, sonra force-arm + 20m kalkis verir.
# Kullanim: python3 mavlink_first_touch.py tcp:127.0.0.1:5760
# Yalnizca kendi SITL laboratuvarinda calistir.

import sys
import time
from pymavlink import mavutil

# Baglanti adresi (argv[1] verilmezse varsayilan SITL portu)
CONN = sys.argv[1] if len(sys.argv) > 1 else "tcp:127.0.0.1:5760"


def enum_name(enum, val):
    # MAVLink sayisal enum degerini okunur ismine cevirir (or. 2 -> MAV_TYPE_QUADROTOR)
    try:
        return mavutil.mavlink.enums[enum][val].name
    except Exception:
        return str(val)


print("[*] Baglaniliyor: %s" % CONN)
m = mavutil.mavlink_connection(CONN)

# Ilk HEARTBEAT'i bekle: aracin kim oldugunu buradan ogreniyoruz
hb = m.wait_heartbeat(timeout=60)
if hb is None:
    print("[!] HEARTBEAT gelmedi, cikiliyor.")
    sys.exit(1)
if m.target_component == 0:
    m.target_component = 1

print("[+] HEARTBEAT alindi  sys=%d comp=%d" % (m.target_system, m.target_component))
print("    arac tipi : %s" % enum_name("MAV_TYPE", hb.type))
print("    otopilot  : %s" % enum_name("MAV_AUTOPILOT", hb.autopilot))
print("    sis durum : %s" % enum_name("MAV_STATE", hb.system_status))
# Not: bu "v%d" HEARTBEAT'in mavlink_version alani (yillardir 3), paket
# bicimi (v1/v2) degil. Bicimi ilk bayt belirler: 0xFD ise MAVLink 2.
print("    MAVLink   : v%d" % hb.mavlink_version)

# Aractan duzenli telemetri akmasi icin tum stream'leri iste
m.mav.request_data_stream_send(
    m.target_system, m.target_component,
    mavutil.mavlink.MAV_DATA_STREAM_ALL, 4, 1)

print("")
print("[*] GPS/EKF kilitlenmesi bekleniyor...")
# Arm icin EKF'in konum tahmini oturmali; once 3D GPS kilidi ariyoruz
locked = False
t_end = time.time() + 50
while time.time() < t_end:
    g = m.recv_match(type="GPS_RAW_INT", blocking=True, timeout=2)
    if g and g.fix_type >= 3:
        p = m.recv_match(type="GLOBAL_POSITION_INT", blocking=True, timeout=2)
        if p and p.lat != 0:
            locked = True
            break
print("[%s] GPS: %s" % ("+" if locked else "!", "3D kilit" if locked else "kilit yok"))

print("")
print("[*] Gelen telemetri (cozulmus):")
# Birkac farkli mesaj tipini yakalayip okunur biciminde basiyoruz
want = ["ATTITUDE", "GLOBAL_POSITION_INT", "GPS_RAW_INT", "VFR_HUD"]
seen = {}
t_end = time.time() + 10
while time.time() < t_end and len(seen) < len(want):
    msg = m.recv_match(type=want, blocking=True, timeout=2)
    if msg is None:
        continue
    t = msg.get_type()
    if t in seen:
        continue
    seen[t] = msg
    if t == "ATTITUDE":
        print("  ATTITUDE             roll=%+.3f pitch=%+.3f yaw=%+.3f rad"
              % (msg.roll, msg.pitch, msg.yaw))
    elif t == "GLOBAL_POSITION_INT":
        print("  GLOBAL_POSITION_INT  lat=%.7f lon=%.7f alt=%.1fm"
              % (msg.lat / 1e7, msg.lon / 1e7, msg.relative_alt / 1000.0))
    elif t == "GPS_RAW_INT":
        print("  GPS_RAW_INT          fix=%d sat=%d"
              % (msg.fix_type, msg.satellites_visible))
    elif t == "VFR_HUD":
        print("  VFR_HUD              alt=%.1fm hiz=%.1fm/s" % (msg.alt, msg.groundspeed))

# Tek bir mesajin ham alanlarini da dokup gosterelim
if "GLOBAL_POSITION_INT" in seen:
    a = seen["GLOBAL_POSITION_INT"]
    print("")
    print("[*] GLOBAL_POSITION_INT ham alanlari:")
    for f in a.get_fieldnames():
        print("    %-16s = %s" % (f, getattr(a, f)))

print("")
print("[*] GUIDED + force-arm + takeoff")
# GUIDED moda gec, sonra arm. param2=21196 = ArduPilot force-arm sihirli degeri
# (pre-arm kontrollerini simulasyonda gecmek icin).
m.set_mode("GUIDED")
time.sleep(2)
armed = False
t_end = time.time() + 50
while time.time() < t_end and not armed:
    m.mav.command_long_send(
        m.target_system, m.target_component,
        mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM, 0, 1, 21196, 0, 0, 0, 0, 0)
    t2 = time.time() + 4
    while time.time() < t2:
        # HEARTBEAT'teki SAFETY_ARMED biti set olduysa arm gerceklesti
        hbm = m.recv_match(type="HEARTBEAT", blocking=True, timeout=2)
        if hbm and (hbm.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED):
            armed = True
            break

if not armed:
    print("[!] Arm olmadi.")
else:
    print("[+] ARMED. TAKEOFF 20m")
    # 20 metreye kalkis komutu
    m.mav.command_long_send(
        m.target_system, m.target_component,
        mavutil.mavlink.MAV_CMD_NAV_TAKEOFF, 0, 0, 0, 0, 0, 0, 0, 20)
    t_end = time.time() + 18
    while time.time() < t_end:
        v = m.recv_match(type="GLOBAL_POSITION_INT", blocking=True, timeout=2)
        if v:
            print("    yukseklik=%5.1fm  dikey_hiz=%+.1fm/s"
                  % (v.relative_alt / 1000.0, -v.vz / 100.0))
