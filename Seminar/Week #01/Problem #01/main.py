# My Python version: 3.10.12
# IDE: VS code

import os
import argparse
from tqdm import tqdm

from rdp_analyzer.config import SECURITY_EVENT_IDS, LSM_EVENT_IDS, RCM_EVENT_IDS
from rdp_analyzer.evtx_reader import iter_evtx_records
from rdp_analyzer.parsers import (
    parse_security_event,
    parse_rcm_event,
    parse_lsm_event,
    parse_rdpclient_event
)
from rdp_analyzer.correlator import correlate_sessions
from rdp_analyzer.failures import analyze_failures
from rdp_analyzer.outputs import (
    write_sessions,
    write_failures,
    write_timeline,
    write_summary_report
)
from rdp_analyzer.utils import ensure_dir

def load_events(evtx_path: str, log_type: str):
    events = []
    for event_id, channel, ts, d, raw_xml in tqdm(iter_evtx_records(evtx_path), desc=f"Parsing {log_type}"):
        if not event_id:
            continue

        if log_type == "Security":
            if event_id not in SECURITY_EVENT_IDS:
                continue
            events.append(parse_security_event(event_id, ts, d, raw_xml))

        elif log_type == "RCM":
            if event_id not in RCM_EVENT_IDS:
                continue
            events.append(parse_rcm_event(event_id, ts, d, raw_xml))

        elif log_type == "LSM":
            if event_id not in LSM_EVENT_IDS:
                continue
            events.append(parse_lsm_event(event_id, ts, d, raw_xml))

        elif log_type == "RDPClient":
            events.append(parse_rdpclient_event(event_id, ts, d, raw_xml))

    return events


def main():
    parser = argparse.ArgumentParser(description="Modular EVTX RDP Analyzer")
    parser.add_argument("--security", required=True)
    parser.add_argument("--lsm", required=True)
    parser.add_argument("--rcm", required=True)
    parser.add_argument("--rdpclient", required=False)
    parser.add_argument("--out", default="output")
    parser.add_argument("--time-window", type=int, default=5)
    args = parser.parse_args()

    ensure_dir(args.out)

    security_events = load_events(args.security, "Security")
    lsm_events = load_events(args.lsm, "LSM")
    rcm_events = load_events(args.rcm, "RCM")

    rdpclient_events = []
    if args.rdpclient and os.path.exists(args.rdpclient):
        rdpclient_events = load_events(args.rdpclient, "RDPClient")

    sessions = correlate_sessions(
        security_events=security_events,
        rcm_events=rcm_events,
        lsm_events=lsm_events,
        time_window_minutes=args.time_window
    )

    df_failures, df_fail_by_ip, df_fail_by_user_ip = analyze_failures(security_events)

    sessions_csv, sessions_json = write_sessions(args.out, sessions)
    failure_paths = write_failures(args.out, df_failures, df_fail_by_ip, df_fail_by_user_ip)
    timeline_path = write_timeline(args.out, security_events, rcm_events, lsm_events)
    report_path = write_summary_report(args.out, sessions, df_fail_by_ip, df_fail_by_user_ip)

    print("\n=== DONE ===")
    print(f"[+] Sessions CSV: {sessions_csv}")
    print(f"[+] Sessions JSON: {sessions_json}")
    if failure_paths:
        for k, v in failure_paths.items():
            print(f"[+] {k}: {v}")
    print(f"[+] Timeline CSV: {timeline_path}")
    print(f"[+] Summary Report: {report_path}")


if __name__ == "__main__":
    main()