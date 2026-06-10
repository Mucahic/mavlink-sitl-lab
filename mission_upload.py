#!/usr/bin/env python3
# mission_upload.py
# MAVLink gorev yukleme protokolunu (mission protocol) bastan sona gosterir:
# MISSION_COUNT -> MISSION_REQUEST(_INT) -> MISSION_ITEM_INT -> MISSION_ACK.
# Istanbul uzerinde uc waypoint'lik kucuk bir gorev atar.
# Kullanim: python3 mission_upload.py tcp:127.0.0.1:5760
# Yalnizca kendi SITL laboratuvarinda calistir.

import sys
import time
from pymavlink import mavutil

CONN = sys.argv[1] if len(sys.argv) > 1 else "tcp:127.0.0.1:5760"

# (lat, lon, alt_m) seklinde uc waypoint
WPS = [
    (41.015137, 28.979530, 50.0),
    (41.020000, 28.985000, 80.0),
    (41.025000, 28.990000, 50.0),
]

m = mavutil.mavlink_connection(CONN)
m.wait_heartbeat(timeout=30)
if m.target_component == 0:
    m.target_component = 1
print("[+] baglanildi sys=%d" % m.target_system)


def send_item(seq):
    # Verilen sira numarasindaki waypoint'i MISSION_ITEM_INT olarak yollar.
    # lat/lon 1e7 ile carpilarak integer (derece * 1e7) gonderilir.
    lat, lon, alt = WPS[seq]
    m.mav.mission_item_int_send(
        m.target_system, m.target_component,
        seq,
        mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
        mavutil.mavlink.MAV_CMD_NAV_WAYPOINT,
        0, 1,                      # current, autocontinue
        0, 0, 0, 0,                # param1..4
        int(lat * 1e7), int(lon * 1e7), alt,
        mavutil.mavlink.MAV_MISSION_TYPE_MISSION)
    print("    >> MISSION_ITEM_INT seq=%d  %.6f, %.5f,  %dm" % (seq, lat, lon, int(alt)))


# Once mevcut gorevi temizle
print("")
print("[*] MISSION_CLEAR_ALL once")
m.mav.mission_clear_all_send(m.target_system, m.target_component)
ack = m.recv_match(type="MISSION_ACK", blocking=True, timeout=5)
if ack:
    print("    << MISSION_ACK type=%d" % ack.type)

# Yukleme: kac waypoint gelecegini duyur
print("")
print("[1] >> MISSION_COUNT count=%d" % len(WPS))
m.mav.mission_count_send(m.target_system, m.target_component,
                         len(WPS), mavutil.mavlink.MAV_MISSION_TYPE_MISSION)

# Arac sirayla isteyecek; her istege ilgili item ile cevap ver
step = 2
done = False
t_end = time.time() + 20
while not done and time.time() < t_end:
    req = m.recv_match(type=["MISSION_REQUEST", "MISSION_REQUEST_INT", "MISSION_ACK"],
                       blocking=True, timeout=5)
    if req is None:
        continue
    if req.get_type() == "MISSION_ACK":
        print("")
        ok = "ACCEPTED" if req.type == 0 else "type=%d" % req.type
        print("[FIN] << MISSION_ACK %s" % ok)
        done = True
        break
    seq = req.seq
    print("[%d] << MISSION_REQUEST seq=%d" % (step, seq))
    step += 1
    send_item(seq)
