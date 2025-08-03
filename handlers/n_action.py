from logzero import logger
from network.dicomweb import send_n_action


def handle_n_action(event):
    ds = event.action_information
    action_type = event.action_type
    sop_instance_uid = event.request.AffectedSOPInstanceUID

    ae_title = event.assoc.requestor.ae_title

    logger.info(f"[UPS N-ACTION FORWARDING] Type {action_type} on UID {sop_instance_uid} from AE: {ae_title}")
    logger.debug(f"[UPS N-ACTION FORWARDING] Dataset:\n{ds}")

    try:
        send_n_action(ds, action_type, sop_instance_uid, ae_title)
        return 0x0000, None
    except Exception as e:
        logger.error(f"[UPS N-ACTION] Failed: {e}")
        return 0x0110, None
