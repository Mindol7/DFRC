# My Python version: 3.10.12
# IDE: VS code

import argparse
import pandas as pd
import matplotlib.pyplot as plt


def load_df(csv_path):
    df = pd.read_csv(csv_path)

    # parse datetime
    df["start"] = pd.to_datetime(df["start"], utc=True, errors="coerce")
    df["end_A_next1149_or_pad"] = pd.to_datetime(df["end_A_next1149_or_pad"], utc=True, errors="coerce")
    df["end_B_last_disconnect_or_none"] = pd.to_datetime(df["end_B_last_disconnect_or_none"], utc=True, errors="coerce")

    # normalize user
    df["user"] = df["user"].fillna("UNKNOWN").astype(str)

    return df.sort_values("start").reset_index(drop=True)


def export_user_table(df_user, out_csv):
    """
    사용자별 세션 표를 저장한다.
    """
    cols = [
        "session_id",
        "user",
        "src_ip",
        "auth_count_1149",
        "start",
        "end_A_next1149_or_pad",
        "end_B_last_disconnect_or_none",
        "duration_A_sec",
        "duration_B_sec",
        "disconnect_count",
        "reconnect_count",
        "confidence",
    ]
    out = df_user[cols].copy()

    # ISO string으로 변환
    for c in ["start", "end_A_next1149_or_pad", "end_B_last_disconnect_or_none"]:
        out[c] = out[c].apply(lambda x: x.isoformat() if pd.notna(x) else "")

    out.to_csv(out_csv, index=False, encoding="utf-8-sig")
    print(f"[+] saved table: {out_csv}")


def plot_user_timeline(df_user, out_png, title_prefix=""):
    """
    사용자별 세션 타임라인:
    - y축: 세션 index (세션 하나가 한 줄)
    - x축: 시간
    - 선분: start -> end_A
    - 끝 점: end_A marker
    - end_B가 있으면 다른 marker로 찍음
    """
    if df_user.empty:
        print(f"[!] no sessions to plot: {out_png}")
        return

    # 세션을 시간 순서대로
    df_user = df_user.sort_values("start").reset_index(drop=True)

    fig, ax = plt.subplots(figsize=(16, max(4, len(df_user) * 0.35)))

    for i, row in df_user.iterrows():
        start = row["start"]
        endA = row["end_A_next1149_or_pad"]
        endB = row["end_B_last_disconnect_or_none"]

        if pd.isna(start) or pd.isna(endA):
            continue

        ax.plot([start, endA], [i, i], linewidth=4)

        ax.scatter([endA], [i], marker="o", s=50)

        if pd.notna(endB):
            ax.scatter([endB], [i], marker="x", s=90)

        ip = str(row["src_ip"])
        ax.text(start, i + 0.15, ip, fontsize=8, alpha=0.9)

    ax.set_yticks(range(len(df_user)))
    ax.set_yticklabels(df_user["session_id"].tolist())
    ax.set_xlabel("Time (UTC)")
    ax.set_ylabel("Session ID")
    ax.set_title(f"{title_prefix} RDP Sessions (Start → End_A, End_B marked)")
    fig.autofmt_xdate()

    ax.scatter([], [], marker="o", label="End_A (next 1149 or padding)")
    ax.scatter([], [], marker="x", label="End_B (disconnect-based)")
    ax.legend(loc="upper right")

    plt.tight_layout()
    plt.savefig(out_png, dpi=200)
    print(f"[+] saved plot: {out_png}")


def plot_user_calendar_like(df_user, out_png, title_prefix=""):
    """
    사용자별 '날짜-시간' 캘린더 스타일:
    - y축: 날짜
    - x축: 하루(0~24h)
    - start/endA를 점으로 표시
    """
    if df_user.empty:
        print(f"[!] no sessions to plot: {out_png}")
        return

    df = df_user.copy()
    df = df.dropna(subset=["start", "end_A_next1149_or_pad"])

    df["day"] = df["start"].dt.date
    df["start_hour"] = df["start"].dt.hour + df["start"].dt.minute / 60.0
    df["endA_hour"] = df["end_A_next1149_or_pad"].dt.hour + df["end_A_next1149_or_pad"].dt.minute / 60.0

    days = sorted(df["day"].unique())
    day_to_y = {d: i for i, d in enumerate(days)}

    fig, ax = plt.subplots(figsize=(14, max(4, len(days) * 0.45)))

    for _, r in df.iterrows():
        y = day_to_y[r["day"]]
        ax.plot([r["start_hour"], r["endA_hour"]], [y, y], linewidth=4)
        ax.scatter([r["start_hour"]], [y], marker="|", s=200) 
        ax.scatter([r["endA_hour"]], [y], marker="|", s=200)  

    ax.set_xlim(0, 24)
    ax.set_xticks(range(0, 25, 2))
    ax.set_xlabel("Hour of day (UTC)")
    ax.set_yticks(range(len(days)))
    ax.set_yticklabels([str(d) for d in days])
    ax.set_ylabel("Date")
    ax.set_title(f"{title_prefix} RDP Sessions by Day (Start–End_A)")

    plt.tight_layout()
    plt.savefig(out_png, dpi=200)
    print(f"[+] saved plot: {out_png}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True, help="Path to rdp_session_summary_v2.csv")
    parser.add_argument("--outdir", default="output", help="Output directory")
    args = parser.parse_args()

    df = load_df(args.csv)

    # 사용자 리스트
    users = sorted(df["user"].unique())
    print("[*] users:", users)

    for user in users:
        df_user = df[df["user"] == user].copy()

        # 표 저장
        out_table = f"{args.outdir}/{user}_sessions_table.csv"
        export_user_table(df_user, out_table)

        # 날짜-시간 캘린더 스타일
        out_calendar = f"{args.outdir}/{user}_sessions_calendar.png"
        plot_user_calendar_like(df_user, out_calendar, title_prefix=user)

    print("\n=== DONE ===")


if __name__ == "__main__":
    main()