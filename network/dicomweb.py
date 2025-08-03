import requests
from logzero import logger
from config import get_config


def send_ups_rs_query(requestor_ae_title, filters):
    config = get_config()
    url = f"{config['host_name'].rstrip('/')}/dicom-web/workitems"
    headers = {
        "X-AE-TITLE": requestor_ae_title or config.get("ae_title", "MARLEY-RIS"),
        # "X-AE-TOKEN": config.get("ae_token", ""),
        "Accept": "application/dicom+json",
        "Content-Type": "application/json",
        "Authorization": f"token {config['api_key']}:{config['api_secret']}",
    }
    try:
        logger.info(f"[DICOMWEB UPS-RS] Sending POST to {url}")
        logger.debug(f"[DICOMWEB UPS-RS] Sending POST to {url} with filters: {filters}")
        r = requests.post(url, headers=headers, json=filters, timeout=10)
        r.raise_for_status()
        logger.debug(f"[DICOMWEB UPS-RS] Response: {r.status_code} - {r.text}")
        return r.json() if r.headers.get("Content-Type", "").startswith("application/json") else []
    except Exception as e:
        logger.warning(f"[DICOMWEB UPS-RS] Query failed: {e}")
        return []


def send_n_action(ds, ae_title, action_type):
    url_map = {
        1: "claim",
        2: "cancelrequest",
        3: "workitemevent"
    }
    if action_type not in url_map:
        raise ValueError(f"Unsupported N-ACTION type: {action_type}")

    config = get_config()
    workitem_uid = getattr(ds, config.get("workitem_uid", "AccessionNumber"), None)
    url = f"{config['host_name'].rstrip('/')}/dicom-web/workitems/{workitem_uid}/{url_map[action_type]}"
    headers = {
        "X-AE-TITLE": getattr(ds, "performed_station_ae", ae_title),
        # "X-AE-TOKEN": config.get("ae_token", ""),
        "Content-Type": "application/dicom+json",
        "Accept": "application/json",
        "Authorization": f"token {config['api_key']}:{config['api_secret']}",
    }
    # transform to dicomweb
    payload = ds.to_json_dict() if hasattr(ds, "to_json_dict") else {}

    try:
        logger.info(f"[DICOMWEB N-ACTION] type={action_type} uid={workitem_uid}")
        logger.debug(f"[DICOMWEB N-ACTION] Payload: {payload}")
        r = requests.post(url, headers=headers, json=payload, timeout=10)
        r.raise_for_status()
        logger.debug(f"[DICOMWEB N-ACTION] Response: {r.status_code} - {r.text}")
        return r.status_code
    except Exception as e:
        logger.error(f"[DICOMWEB N-ACTION] Failed for UID {workitem_uid}: {e}")
        raise
