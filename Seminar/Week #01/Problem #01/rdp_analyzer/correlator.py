# My Python version: 3.10.12
# IDE: VS code

from datetime import datetime, timedelta
from collections import defaultdict
import hashlib


def _make_session_id(prefix, username, ip, ts):
    """
    Deterministic-ish session id for fallback sessions (RCM/LSM 기반)
    """
    base = f"{prefix}|{username}|{ip}|{ts.isoformat() if ts else ''}"
    return hashlib.md5(base.encode("utf-8")).hexdigest()[:12]


def correlate_sessions(security_events, rcm_events, lsm_events, time_window_minutes=5):
    """
    1) 우선순위 1: Security 4624(LogonType=10) 기반 세션 생성
    2) 만약 0건이면: RCM 1149 기반으로 fallback 세션 생성
       - 동일 사용자/동일 IP + 시간 근접 이벤트를 하나의 세션으로 묶음
       - LSM 24/25 같은 세션 이벤트를 attach (disconnect/reconnect 카운트)
    """

    # ------------------------------------------------------------
    # A) 1차 시도: Security 4624(LogonType=10) 기반 세션
    # ------------------------------------------------------------

    # Index logoffs and admin privs by logon_id
    logoff_by_logonid = {}
    adminpriv_by_logonid = set()

    for ev in security_events:
        if ev["event_id"] == 4634 and ev["logon_id"]:
            logoff_by_logonid[ev["logon_id"]] = ev["timestamp"]
        if ev["event_id"] == 4672 and ev["logon_id"]:
            adminpriv_by_logonid.add(ev["logon_id"])

    rcm_sorted = sorted([e for e in rcm_events if e["event_id"] == 1149], key=lambda x: x["timestamp"] or datetime.min)
    lsm_sorted = sorted(lsm_events, key=lambda x: x["timestamp"] or datetime.min)

    def find_best_rcm_match(start_ts, username, ip):
        if not start_ts:
            return None
        win = timedelta(minutes=time_window_minutes)
        candidates = []
        for e in rcm_sorted:
            if not e["timestamp"]:
                continue
            if abs(e["timestamp"] - start_ts) <= win:
                candidates.append(e)

        if not candidates:
            return None

        def score(e):
            s = 0
            if username and e["username"] and str(username).lower() == str(e["username"]).lower():
                s += 2
            if ip and e["ip"] and ip == e["ip"]:
                s += 2
            s += max(0, 1 - abs((e["timestamp"] - start_ts).total_seconds()) / win.total_seconds())
            return s

        candidates.sort(key=score, reverse=True)
        return candidates[0]

    def collect_lsm_for_window(tmin, tmax, username=None, ip=None):
        out = []
        for e in lsm_sorted:
            if not e["timestamp"]:
                continue
            if e["timestamp"] < tmin or e["timestamp"] > tmax:
                continue

            if username and e.get("username"):
                if str(username).lower() != str(e["username"]).lower():
                    continue

            if ip and e.get("ip"):
                if ip != e["ip"]:
                    continue

            out.append(e)
        return out

    sessions = []

    for ev in security_events:
        if ev["event_id"] != 4624:
            continue

        lt = ev.get("logon_type")
        if not lt or str(lt).strip() != "10":
            continue

        start_ts = ev["timestamp"]
        username = ev["username"]
        domain = ev["domain"]
        ip = ev["ip"]
        workstation = ev["workstation"]
        logon_id = ev["logon_id"]

        end_ts = logoff_by_logonid.get(logon_id)

        duration = None
        if start_ts and end_ts:
            duration = int((end_ts - start_ts).total_seconds())
            if duration < 0:
                duration = None

        rcm_match = find_best_rcm_match(start_ts, username, ip)

        # LSM attach
        if end_ts:
            tmin = start_ts - timedelta(minutes=2)
            tmax = end_ts + timedelta(minutes=2)
        else:
            tmin = start_ts - timedelta(minutes=2)
            tmax = start_ts + timedelta(minutes=30)

        lsm_list = collect_lsm_for_window(tmin, tmax, username=username)

        disconnect_count = sum(1 for x in lsm_list if x["event_id"] == 24)
        reconnect_count = sum(1 for x in lsm_list if x["event_id"] == 25)

        session_ids = [x["session_id"] for x in lsm_list if x.get("session_id")]
        session_id = session_ids[0] if session_ids else None

        sessions.append({
            "session_start": start_ts.isoformat() if start_ts else None,
            "session_end": end_ts.isoformat() if end_ts else None,
            "duration_sec": duration,
            "username": username,
            "domain": domain,
            "client_ip": ip,
            "workstation": workstation,
            "session_id": session_id,
            "evidence_basis": "Security4624(LogonType=10)",
            "logon_id": logon_id,
            "admin_priv_4672": logon_id in adminpriv_by_logonid,

            "auth_event_time_1149": rcm_match["timestamp"].isoformat() if rcm_match and rcm_match["timestamp"] else None,
            "auth_client_ip_1149": rcm_match["ip"] if rcm_match else None,
            "auth_client_name_1149": rcm_match["client_name"] if rcm_match else None,

            "disconnect_count": disconnect_count,
            "reconnect_count": reconnect_count,
            "lsm_events": [
                {
                    "timestamp": x["timestamp"].isoformat() if x["timestamp"] else None,
                    "event_id": x["event_id"],
                    "session_id": x.get("session_id"),
                    "ip": x.get("ip")
                }
                for x in lsm_list
            ]
        })

    # 만약 Security 기반 세션이 있으면 그대로 반환
    sessions.sort(key=lambda x: x["session_start"] or "")
    if len(sessions) > 0:
        return sessions

    # ------------------------------------------------------------
    # B) Fallback: RCM 1149 기반 세션 생성
    # ------------------------------------------------------------
    # Security에서 RDP LogonType=10이 없다면, RCM 1149는 "인증 성공" 증거로 사용 가능
    # 동일 user+ip + 시간 근접한 1149들을 하나의 접속 세션으로 묶는다.
    #
    # 종료 시점은 Security logoff가 없으면 확정 어려움
    # -> 다음 1149까지를 하나의 윈도우로 잡거나, fixed session_window 사용
    # ------------------------------------------------------------

    fallback_sessions = []

    # 1149만 사용
    auth_events = [e for e in rcm_sorted if e.get("timestamp") and e.get("ip")]
    if not auth_events:
        return []

    auth_events.sort(key=lambda x: x["timestamp"])

    # 세션 그룹핑 기준: 같은 user+ip에서 일정 시간 이상 간격 나면 새로운 세션
    gap = timedelta(minutes=30) 
    session_window = timedelta(hours=2) 

    current = None

    def flush_current():
        if not current:
            return
        fallback_sessions.append(current)

    for e in auth_events:
        u = e.get("username") or "UNKNOWN"
        ip = e.get("ip")
        ts = e["timestamp"]

        if current is None:
            current = {
                "session_start_ts": ts,
                "session_end_ts": None,
                "username": u,
                "domain": None,
                "client_ip": ip,
                "workstation": None,
                "session_id": _make_session_id("RCM1149", u, ip, ts),
                "auth_events": [e],
            }
            continue

        # 같은 user+ip이면서 gap 안이면 같은 세션으로 묶음
        same_user = str(current["username"]).lower() == str(u).lower()
        same_ip = current["client_ip"] == ip
        last_ts = current["auth_events"][-1]["timestamp"]

        if same_user and same_ip and (ts - last_ts) <= gap:
            current["auth_events"].append(e)
        else:
            flush_current()
            current = {
                "session_start_ts": ts,
                "session_end_ts": None,
                "username": u,
                "domain": None,
                "client_ip": ip,
                "workstation": None,
                "session_id": _make_session_id("RCM1149", u, ip, ts),
                "auth_events": [e],
            }

    flush_current()

    for s in fallback_sessions:
        start_ts = s["session_start_ts"]

        last_auth_ts = s["auth_events"][-1]["timestamp"]
        end_guess = min(last_auth_ts + session_window, last_auth_ts + timedelta(minutes=30))
        s["session_end_ts"] = end_guess

        lsm_list = collect_lsm_for_window(
            start_ts - timedelta(minutes=5),
            end_guess + timedelta(minutes=5),
            username=s["username"]  
        )

        disconnect_count = sum(1 for x in lsm_list if x["event_id"] == 24)
        reconnect_count = sum(1 for x in lsm_list if x["event_id"] == 25)

        fallback_row = {
            "session_start": start_ts.isoformat(),
            "session_end": end_guess.isoformat() if end_guess else None,
            "duration_sec": int((end_guess - start_ts).total_seconds()) if end_guess else None,

            "username": s["username"],
            "domain": None,
            "client_ip": s["client_ip"],
            "workstation": None,
            "session_id": s["session_id"],
            "evidence_basis": "RCM1149(Fallback: Security4624Type10 not found)",
            "logon_id": None,
            "admin_priv_4672": False,

            "auth_event_time_1149": s["auth_events"][0]["timestamp"].isoformat(),
            "auth_client_ip_1149": s["client_ip"],
            "auth_client_name_1149": s["auth_events"][0].get("client_name"),

            "disconnect_count": disconnect_count,
            "reconnect_count": reconnect_count,
            "lsm_events": [
                {
                    "timestamp": x["timestamp"].isoformat() if x["timestamp"] else None,
                    "event_id": x["event_id"],
                    "session_id": x.get("session_id"),
                    "ip": x.get("ip")
                }
                for x in lsm_list
            ],

            "auth_events_count": len(s["auth_events"]),
        }

        sessions.append(fallback_row)

    sessions.sort(key=lambda x: x["session_start"] or "")
    return sessions