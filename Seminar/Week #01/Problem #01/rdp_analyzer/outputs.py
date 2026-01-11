# My Python version: 3.10.12
# IDE: VS code

import os
import json
import pandas as pd
from collections import defaultdict

def write_sessions(out_dir, sessions):
    df_sessions = pd.DataFrame(sessions)
    csv_path = os.path.join(out_dir, "rdp_sessions.csv")
    json_path = os.path.join(out_dir, "rdp_sessions.json")

    df_sessions.to_csv(csv_path, index=False, encoding="utf-8-sig")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(sessions, f, indent=2, ensure_ascii=False)

    return csv_path, json_path

def write_failures(out_dir, df_failures, df_fail_by_ip, df_fail_by_user_ip):
    paths = {}

    if df_failures.empty:
        return paths

    paths["failures_csv"] = os.path.join(out_dir, "rdp_failures_4625.csv")
    paths["fail_ip_csv"] = os.path.join(out_dir, "rdp_failure_top_ips.csv")
    paths["fail_user_ip_csv"] = os.path.join(out_dir, "rdp_failure_top_user_ip.csv")

    df_failures.to_csv(paths["failures_csv"], index=False, encoding="utf-8-sig")
    df_fail_by_ip.to_csv(paths["fail_ip_csv"], index=False, encoding="utf-8-sig")
    df_fail_by_user_ip.to_csv(paths["fail_user_ip_csv"], index=False, encoding="utf-8-sig")

    return paths

def write_timeline(out_dir, security_events, rcm_events, lsm_events):
    timeline_rows = []

    for e in security_events:
        timeline_rows.append({
            "timestamp": e["timestamp"].isoformat() if e["timestamp"] else None,
            "source": e["source"],
            "event_id": e["event_id"],
            "username": e["username"],
            "ip": e["ip"],
            "logon_id": e["logon_id"]
        })

    for e in rcm_events:
        timeline_rows.append({
            "timestamp": e["timestamp"].isoformat() if e["timestamp"] else None,
            "source": e["source"],
            "event_id": e["event_id"],
            "username": e["username"],
            "ip": e["ip"],
            "logon_id": None
        })

    for e in lsm_events:
        timeline_rows.append({
            "timestamp": e["timestamp"].isoformat() if e["timestamp"] else None,
            "source": e["source"],
            "event_id": e["event_id"],
            "username": e["username"],
            "ip": e["ip"],
            "logon_id": None
        })

    df_timeline = pd.DataFrame(timeline_rows).sort_values("timestamp")
    path = os.path.join(out_dir, "timeline_all_events.csv")
    df_timeline.to_csv(path, index=False, encoding="utf-8-sig")

    return path

def write_summary_report(out_dir, sessions, failures_by_ip, failures_by_user_ip):
    report_path = os.path.join(out_dir, "summary_report.txt")

    total_sessions = len(sessions)
    unique_users = sorted(set([s["username"] for s in sessions if s["username"]]))
    unique_ips = sorted(set([s["client_ip"] for s in sessions if s["client_ip"]]))

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("=== RDP Analysis Summary Report ===\n\n")
        f.write(f"Total RDP Success Sessions: {total_sessions}\n")
        f.write(f"Unique Usernames: {len(unique_users)}\n")
        f.write(f"Unique Client IPs: {len(unique_ips)}\n\n")

        f.write("[Top Client IPs from Successful Sessions]\n")
        ip_count = defaultdict(int)
        for s in sessions:
            if s["client_ip"]:
                ip_count[s["client_ip"]] += 1

        for ip, cnt in sorted(ip_count.items(), key=lambda x: x[1], reverse=True)[:10]:
            f.write(f"- {ip}: {cnt} sessions\n")

        f.write("\n[Users from Successful Sessions]\n")
        for u in unique_users:
            f.write(f"- {u}\n")

        f.write("\n=== Failure Attempts (4625 LogonType=10) ===\n")
        if failures_by_ip is None or failures_by_ip.empty:
            f.write("No RDP failure attempts found.\n")
        else:
            f.write("\n[Top Failure IPs]\n")
            for _, row in failures_by_ip.head(10).iterrows():
                f.write(f"- {row['client_ip']}: {row['fail_count']} failures\n")

            f.write("\n[Top Failure Username+IP]\n")
            for _, row in failures_by_user_ip.head(10).iterrows():
                f.write(f"- {row['username']} @ {row['client_ip']}: {row['fail_count']} failures\n")

    return report_path
