# My Python version: 3.10.12
# IDE: VS code

from .utils import normalize_ip

def parse_security_event(event_id, ts, d, raw_xml):
    return {
        "timestamp": ts,
        "source": "Security",
        "event_id": event_id,
        "username": d.get("TargetUserName") or d.get("SubjectUserName") or d.get("AccountName"),
        "domain": d.get("TargetDomainName") or d.get("SubjectDomainName"),
        "ip": normalize_ip(d.get("IpAddress") or d.get("SourceNetworkAddress")),
        "workstation": d.get("WorkstationName"),
        "logon_type": d.get("LogonType"),
        "logon_id": d.get("TargetLogonId") or d.get("LogonId") or d.get("SubjectLogonId"),
        "status": d.get("Status"),
        "substatus": d.get("SubStatus"),
        "raw_xml": raw_xml,
    }

def parse_rcm_event(event_id, ts, d, raw_xml):
    return {
        "timestamp": ts,
        "source": "RCM",
        "event_id": event_id,
        "username": d.get("Param1") or d.get("User") or d.get("UserName") or d.get("Username"),
        "ip": normalize_ip(d.get("Param3") or d.get("ClientAddress") or d.get("Address") or d.get("ClientIP")),
        "client_name": d.get("Param2") or d.get("ClientName") or d.get("Workstation"),
        "raw_xml": raw_xml,
    }

def parse_lsm_event(event_id, ts, d, raw_xml):
    return {
        "timestamp": ts,
        "source": "LSM",
        "event_id": event_id,
        "username": d.get("User") or d.get("UserName") or d.get("Username") or d.get("Param1"),
        "session_id": d.get("SessionID") or d.get("SessionId") or d.get("Param2") or d.get("Session"),
        "ip": normalize_ip(d.get("Address") or d.get("ClientAddress") or d.get("SourceNetworkAddress") or d.get("Param3")),
        "raw_xml": raw_xml,
    }

def parse_rdpclient_event(event_id, ts, d, raw_xml):
    return {
        "timestamp": ts,
        "source": "RDPClient",
        "event_id": event_id,
        "username": d.get("UserName") or d.get("Username") or d.get("Param1"),
        "target": d.get("ServerName") or d.get("TargetServer") or d.get("Param2") or d.get("Host"),
        "ip": normalize_ip(d.get("ServerAddress") or d.get("Address") or d.get("Param3")),
        "raw_xml": raw_xml,
    }