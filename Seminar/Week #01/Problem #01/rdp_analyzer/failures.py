# My Python version: 3.10.12
# IDE: VS code

import pandas as pd

# RDP 실패 이벤트들을 분석함

def analyze_failures(security_events):
    attempts = []
    for ev in security_events:
        if ev["event_id"] != 4625:
            continue
        lt = ev.get("logon_type")
        if not lt or str(lt).strip() != "10":
            continue

        attempts.append({
            "timestamp": ev["timestamp"].isoformat() if ev["timestamp"] else None,
            "username": ev["username"],
            "domain": ev["domain"],
            "client_ip": ev["ip"],
            "status": ev["status"],
            "substatus": ev["substatus"],
        })

    df = pd.DataFrame(attempts)
    if df.empty:
        return df, pd.DataFrame(), pd.DataFrame()

    by_ip = df.groupby(["client_ip"]).size().reset_index(name="fail_count").sort_values("fail_count", ascending=False)
    by_user_ip = df.groupby(["username", "client_ip"]).size().reset_index(name="fail_count").sort_values("fail_count", ascending=False)

    return df, by_ip, by_user_ip