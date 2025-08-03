import json
import requests
from logzero import logger
from config import get_config
from utils.mpps_payload import build_mpps_payload
from pydicom.dataset import Dataset

def handle_n_create_legacy(event):
    ds = event.attribute_list
    ae_title = event.assoc.requestor.ae_title

    logger.info(f"[MPPS N-CREATE] From AE: {ae_title}")
    logger.debug(f"[MPPS N-CREATE] Dataset:\n{ds}")

    try:
        payload = build_mpps_payload(ds)
        study_uid = payload.get("study_instance_uid")
        if study_uid:
            send_n_create_legacy(Dataset(), action_type=1, sop_instance_uid=study_uid, ae_title=ae_title)
        return 0x0000, None
    except Exception as e:
        logger.error(f"[MPPS N-CREATE] Failed: {e}")
        return 0x0110, None


def handle_n_set_legacy(event):
    ds = event.modification_list
    ae_title = event.assoc.requestor.ae_title

    logger.info(f"[MPPS N-SET] From AE: {ae_title}")
    logger.debug(f"[MPPS N-SET] Dataset:\n{ds}")

    try:
        payload = build_mpps_payload(ds)
        study_uid = payload.get("study_instance_uid")
        status = payload.get("status", "").lower()
        if study_uid and status == "completed":
            send_n_set_legacy(Dataset(), action_type=3, sop_instance_uid=study_uid, ae_title=ae_title)
        return 0x0000, None
    except Exception as e:
        logger.error(f"[MPPS N-SET] Failed: {e}")
        return 0x0110, None

def send_n_create_legacy(ds):
    config = get_config()
    url = f"{config['host_name'].rstrip('/')}/api/method/healthcare.healthcare.api.mpps.handle_n_create"
    headers = {
        "Authorization": f"token {config['api_key']}:{config['api_secret']}",
        "Content-Type": "application/json",
    }
    payload = ds.to_json_dict() if hasattr(ds, "to_json_dict") else {}

    try:
        logger.debug(f"[LEGACY N-CREATE] Sending to {url}: {payload}")
        r = requests.post(url, headers=headers, data=json.dumps(payload))
        r.raise_for_status()
        logger.debug(f"[LEGACY N-CREATE] Response: {r.status_code} - {r.text}")
    except Exception as e:
        logger.error(f"[LEGACY N-CREATE] Failed: {e}")
        raise


def send_n_set_legacy(ds):
    config = get_config()
    url = f"{config['host_name'].rstrip('/')}/api/method/healthcare.healthcare.api.mpps.handle_n_set"
    headers = {
        "Authorization": f"token {config['api_key']}:{config['api_secret']}",
        "Content-Type": "application/json",
    }
    payload = ds.to_json_dict() if hasattr(ds, "to_json_dict") else {}

    try:
        logger.debug(f"[LEGACY N-SET] Sending to {url}: {payload}")
        r = requests.post(url, headers=headers, data=json.dumps(payload))
        r.raise_for_status()
        logger.debug(f"[LEGACY N-SET] Response: {r.status_code} - {r.text}")
    except Exception as e:
        logger.error(f"[LEGACY N-SET] Failed: {e}")
        raise
