import requests
from logzero import logger
from config import get_config

def handle_echo(event):
    logger.debug("[DIMSE C-ECHO] Triggered")

    try:
        config = get_config()
        url = f"{config['host_name'].rstrip('/')}/dicom-web/echo"

        headers = {
            "X-AE-TITLE": event.assoc.requestor.ae_title,
            # "X-AE-TOKEN": config.get("ae_token", ""),
            "Accept": "application/json",
            "Authorization": f"token {config['api_key']}:{config['api_secret']}",
        }
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        logger.info(f"[DICOMWEB C-ECHO] Marley verified: {response.status_code}")
    except Exception as e:
        logger.warning(f"[DICOMWEB C-ECHO] Marley verification failed: {e}")
        return 0xA700  # Refused / Upstream error

    logger.info("[DIMSE C-ECHO] Completed successfully")
    return 0x0000
