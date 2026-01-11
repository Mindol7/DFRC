# My Python version: 3.10.12
# IDE: VS code

from Evtx.Evtx import Evtx
from lxml import etree
from .utils import safe_dt

# EVTX를 분석 가능한 형태로 구조화 함.

def iter_evtx_records(evtx_path: str):
    """
    Yield (event_id, channel, timestamp, eventdata_dict, raw_xml,string)
    """

    with Evtx(evtx_path) as log:
        for record in log.records():
            xml_str = record.xml()
            try:
                root = etree.fromstring(xml_str.encode("utf-8"))
            except Exception:
                continue

            ns = {"e": "http://schemas.microsoft.com/win/2004/08/events/event"}
            sys_node = root.find("e:System", namespaces=ns)
            if sys_node is None:
                continue
            eid_node = sys_node.find("e:EventID", namespaces=ns)
            event_id = int(eid_node.text) if eid_node is not None else None

            channel_node = sys_node.find("e:Channel", namespaces=ns)
            channel = channel_node.text if channel_node is not None else None

            time_node = sys_node.find("e:TimeCreated", namespaces=ns)
            ts = safe_dt(time_node.attrib.get("SystemTime")) if time_node is not None else None


            data_dict = {}

            ed = root.find("e:EventData", namespaces=ns)
            if ed is not None:
                for d in ed.findall("e:Data", namespaces=ns):
                    name = d.attrib.get("Name")
                    val = d.text
                    if name:
                        data_dict[name] = val

            ud = root.find("e:UserData", namespaces = ns)
            if ud is not None:
                for elem in ud.iter():
                    if elem is ud:
                        continue
                    tag = etree.QName(elem).localname
                    if elem.text and elem.text.strip():
                        if tag in data_dict:
                            data_dict[f"UserData_{tag}"] = elem.text
                        else:
                            data_dict[tag] = elem.text
                    
                    for k, v in elem.attrib.items():
                        attr_key = f"{tag}_{k}"
                        if attr_key not in data_dict:
                            data_dict[attr_key] = v

            yield event_id, channel, ts, data_dict, xml_str