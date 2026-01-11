# My Python version: 3.10.12
# IDE: VS code

import os
from dateutil import parser as dtparser

def safe_dt(dt_str: str):
    if not dt_str:
        return None
    try:
        return dtparser.parse(dt_str)
    except Exception:
        return None

def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

def normalize_ip(ip):
    if not ip:
        return None
    ip = ip.strip()
    if ip in ["-", "::1", "127.0.0.1", ""]:
        return None
    return ip