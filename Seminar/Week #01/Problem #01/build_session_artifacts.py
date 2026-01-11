# My Python version: 3.10.12
# IDE: VS code

import argparse
import json
from datetime import timedelta
from collections import defaultdict, Counter

import pandas as pd


# -----------------------------
# Helpers
# -----------------------------
def to_dt(s):
    return pd.to_datetime(s, utc=True, errors="coerce")

def safe_str(x):
    return None if pd.isna(x) else str(x)

def norm_user(u):
    if u is None or pd.isna(u) or str(u).strip() == "":
        return "UNKNOWN"
    return str(u).strip()

def norm_ip(ip):
    if ip is None or pd.isna(ip) or str(ip).strip() == "":
        return None
    return str(ip).strip()

def calc_confidence(has_1149, has_lsm, user_known):
    # 간단하지만 납득 가능한 Confidence 규칙
    if has_1149 and has_lsm and user_known:
        return "HIGH"
    if has_1149 and (has_lsm or user_known):
        return "MEDIUM"
    if has_1149:
        return "LOW"
    return "UNKNOWN"

def extract_host_from_1149_events(df_1149_group):
    """
    timeline_all_events.csv에는 client_name이 없을 수 있음.
    있을 경우에만 뽑는다.
    """
    if "client_name" not in df_1149_group.columns:
        return None
    # 가장 많이 나온 host를 사용
    vals = [v for v in df_1149_group["client_name"].dropna().astype(str).tolist() if v.strip()]
    if not vals:
        return None
    return Counter(vals).most_common(1)[0][0]


# -----------------------------
# Core: Build sessions from RCM1149 + attach LSM evidence
# -----------------------------
def build_sessions_from_timeline(timeline_csv, gap_minutes=30, endA_pad_minutes=10, endB_pad_minutes=5):
    """
    세션 구성: (username, ip) 기준으로 1149 인증 이벤트를 묶고
    LSM 24/25를 근접 window로 attach.
    종료시점 2개:
      - End_A: 다음 1149 전 / 또는 last_1149 + pad
      - End_B: 마지막 disconnect + pad
    """
    df = pd.read_csv(timeline_csv)

    # timestamp 처리
    df["timestamp"] = to_dt(df["timestamp"])
    df = df.dropna(subset=["timestamp"])

    # 필요한 컬럼 기본화
    if "username" not in df.columns:
        df["username"] = None
    if "ip" not in df.columns:
        df["ip"] = None

    df["username"] = df["username"].apply(norm_user)
    df["ip"] = df["ip"].apply(norm_ip)

    # RCM 1149 only
    df_1149 = df[(df["source"] == "RCM") & (df["event_id"] == 1149)].copy()
    df_1149 = df_1149.dropna(subset=["ip"])  # ip는 세션 키이므로 필수
    df_1149 = df_1149.sort_values("timestamp")

    # LSM 24/25
    df_lsm = df[(df["source"] == "LSM") & (df["event_id"].isin([24, 25]))].copy()
    df_lsm = df_lsm.sort_values("timestamp")

    gap = timedelta(minutes=gap_minutes)
    endA_pad = timedelta(minutes=endA_pad_minutes)
    endB_pad = timedelta(minutes=endB_pad_minutes)

    sessions = []
    session_id_counter = 0

    for (user, ip), grp in df_1149.groupby(["username", "ip"]):
        grp = grp.sort_values("timestamp").reset_index(drop=True)

        # host 추출(가능하면)
        host = extract_host_from_1149_events(grp)

        current_start = None
        last_ts = None
        auth_times = []

        def flush_session(next_start_ts=None):
            nonlocal session_id_counter, current_start, last_ts, auth_times

            if current_start is None:
                return

            session_id_counter += 1
            sid = f"S{session_id_counter:04d}"

            if next_start_ts is not None and (next_start_ts - last_ts) <= gap:
                end_A = next_start_ts
            else:
                end_A = last_ts + endA_pad

            wmin = current_start - timedelta(minutes=5)
            wmax = end_A + timedelta(minutes=5)

            # LSM 이벤트 attach: username 기준(LSM ip가 비어있을 수 있어 user가 더 reliable)
            lsm_ev = df_lsm[(df_lsm["timestamp"] >= wmin) & (df_lsm["timestamp"] <= wmax) & (df_lsm["username"] == user)].copy()

            disconnect_times = lsm_ev[lsm_ev["event_id"] == 24]["timestamp"].tolist()
            reconnect_times = lsm_ev[lsm_ev["event_id"] == 25]["timestamp"].tolist()

            if disconnect_times:
                end_B = max(disconnect_times) + endB_pad
            else:
                end_B = pd.NaT

            # Confidence
            user_known = (user != "UNKNOWN")
            has_lsm = (len(lsm_ev) > 0)
            conf = calc_confidence(True, has_lsm, user_known)

            sessions.append({
                "session_id": sid,
                "user": user,
                "src_ip": ip,
                "src_host": host,
                "auth_count_1149": len(auth_times),
                "start": current_start,
                "end_A_next1149_or_pad": end_A,
                "end_B_last_disconnect_or_none": end_B,
                "duration_A_sec": int((end_A - current_start).total_seconds()) if pd.notna(end_A) else None,
                "duration_B_sec": int((end_B - current_start).total_seconds()) if pd.notna(end_B) else None,
                "disconnect_count": len(disconnect_times),
                "reconnect_count": len(reconnect_times),
                "confidence": conf,

                "evidence_auth_1149_first": min(auth_times) if auth_times else None,
                "evidence_auth_1149_last": max(auth_times) if auth_times else None,
                "evidence_disconnect_last": max(disconnect_times) if disconnect_times else None,
                "evidence_reconnect_last": max(reconnect_times) if reconnect_times else None,

                "evidence_events": (
                    [{"timestamp": t.isoformat(), "source": "RCM", "event_id": 1149, "note": "Auth Success"} for t in auth_times] +
                    [{"timestamp": t.isoformat(), "source": "LSM", "event_id": 24, "note": "Disconnect"} for t in disconnect_times] +
                    [{"timestamp": t.isoformat(), "source": "LSM", "event_id": 25, "note": "Reconnect"} for t in reconnect_times]
                )
            })

            # reset
            current_start = None
            last_ts = None
            auth_times = []

        # iterate auth events and split by gap
        for i, row in grp.iterrows():
            ts = row["timestamp"]

            if current_start is None:
                current_start = ts
                last_ts = ts
                auth_times = [ts]
                continue

            if ts - last_ts > gap:
                # 새로운 세션 시작
                flush_session(next_start_ts=None)
                current_start = ts
                last_ts = ts
                auth_times = [ts]
            else:
                last_ts = ts
                auth_times.append(ts)

        flush_session(next_start_ts=None)

    out_df = pd.DataFrame(sessions)
    if out_df.empty:
        return out_df, []

    out_df = out_df.sort_values("start").reset_index(drop=True)
    return out_df, sessions


# -----------------------------
# Failures: try to infer from Security events (if available in timeline)
# -----------------------------
def build_failure_summary(timeline_csv):
    """
    timeline_all_events.csv에 Security 이벤트가 포함돼 있다면:
    - 4625 존재 여부 (LogonType까지는 timeline에 없으므로 제한적)
    현재 데이터셋 특성상 실패가 거의 없을 것.
    """
    df = pd.read_csv(timeline_csv)
    if "source" not in df.columns:
        return {"observed_failures": 0, "top_failure_ips": []}

    df = df[(df["source"] == "Security") & (df["event_id"] == 4625)].copy()
    if df.empty:
        return {"observed_failures": 0, "top_failure_ips": []}

    # ip 컬럼이 비어 있을 수 있음
    if "ip" not in df.columns:
        df["ip"] = None
    df["ip"] = df["ip"].fillna("UNKNOWN_IP")

    top = df["ip"].value_counts().head(10).to_dict()
    return {"observed_failures": int(len(df)), "top_failure_ips": top}


# -----------------------------
# Outputs
# -----------------------------
def save_outputs(outdir, sessions_df, sessions_list, failures_summary):
    outdir = outdir.rstrip("/")

    # 1) Summary CSV
    summary_csv = f"{outdir}/rdp_session_summary_v2.csv"
    df_out = sessions_df.copy()

    # datetime -> iso string
    for c in ["start", "end_A_next1149_or_pad", "end_B_last_disconnect_or_none",
              "evidence_auth_1149_first", "evidence_auth_1149_last",
              "evidence_disconnect_last", "evidence_reconnect_last"]:
        if c in df_out.columns:
            df_out[c] = df_out[c].apply(lambda x: x.isoformat() if pd.notna(x) else None)

    df_out.to_csv(summary_csv, index=False, encoding="utf-8-sig")

    # 2) Cases JSON
    cases_json = f"{outdir}/rdp_session_cases.json"
    cases = []
    for s in sessions_list:
        cases.append({
            "session_id": s["session_id"],
            "identity": {
                "user": s["user"],
                "src_ip": s["src_ip"],
                "src_host": s["src_host"]
            },
            "time": {
                "start": s["start"].isoformat() if pd.notna(s["start"]) else None,
                "end_A_next1149_or_pad": s["end_A_next1149_or_pad"].isoformat() if pd.notna(s["end_A_next1149_or_pad"]) else None,
                "end_B_last_disconnect_or_none": s["end_B_last_disconnect_or_none"].isoformat() if pd.notna(s["end_B_last_disconnect_or_none"]) else None,
                "duration_A_sec": s["duration_A_sec"],
                "duration_B_sec": s["duration_B_sec"]
            },
            "result": {
                "success": True,
                "failure_observed": False,  # 이 데이터셋에서는 RDP 실패 증거가 없거나 제한적임
                "confidence": s["confidence"]
            },
            "evidence": {
                "auth_1149_count": s["auth_count_1149"],
                "disconnect_count": s["disconnect_count"],
                "reconnect_count": s["reconnect_count"],
                "first_auth_1149": s["evidence_auth_1149_first"].isoformat() if s["evidence_auth_1149_first"] else None,
                "last_auth_1149": s["evidence_auth_1149_last"].isoformat() if s["evidence_auth_1149_last"] else None,
                "last_disconnect": s["evidence_disconnect_last"].isoformat() if s["evidence_disconnect_last"] else None,
                "last_reconnect": s["evidence_reconnect_last"].isoformat() if s["evidence_reconnect_last"] else None,
                "events": sorted(s["evidence_events"], key=lambda x: x["timestamp"])
            },
            "notes": [
                "Security 4624(LogonType=10) not present in provided dataset; session timeline is inferred primarily from RCM 1149.",
                "End_A is inferred from next 1149 event timing or a fixed padding after last 1149.",
                "End_B is inferred from last LSM 24(Disconnect) timing if present."
            ]
        })

    with open(cases_json, "w", encoding="utf-8") as f:
        json.dump({"cases": cases, "failures_summary": failures_summary}, f, indent=2, ensure_ascii=False)

    return summary_csv, cases_json

def main():
    parser = argparse.ArgumentParser(description="Build session artifacts (End_A & End_B) from timeline CSV")
    parser.add_argument("--timeline", required=True, help="Path to timeline_all_events.csv")
    parser.add_argument("--outdir", default="output", help="Output directory")
    parser.add_argument("--gap", type=int, default=30, help="Gap minutes to split sessions (per user+ip)")
    parser.add_argument("--endA_pad", type=int, default=10, help="End_A padding minutes after last 1149 if no next event")
    parser.add_argument("--endB_pad", type=int, default=5, help="End_B padding minutes after last disconnect")
    args = parser.parse_args()

    sessions_df, sessions_list = build_sessions_from_timeline(
        args.timeline,
        gap_minutes=args.gap,
        endA_pad_minutes=args.endA_pad,
        endB_pad_minutes=args.endB_pad
    )

    failures_summary = build_failure_summary(args.timeline)

    if sessions_df.empty:
        print("[!] No sessions inferred from timeline.")
        return

    summary_csv, cases_json = save_outputs(args.outdir, sessions_df, sessions_list, failures_summary)

    print("\n=== DONE ===")
    print(f"[+] Summary CSV: {summary_csv}")
    print(f"[+] Case JSON: {cases_json}")


if __name__ == "__main__":
    main()