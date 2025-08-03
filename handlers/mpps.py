from logzero import logger
from network.dicomweb import send_n_action

def handle_n_create(event):
    ds = event.attribute_list
    ae_title = event.assoc.requestor.ae_title

    logger.info(f"[MPPS N-CREATE] From AE: {ae_title}")
    logger.debug(f"[MPPS N-CREATE] Dataset:\n{ds}")

    try:
        send_n_action(ds, ae_title, action_type=1)
        return 0x0000, None
    except Exception as e:
        logger.error(f"[MPPS N-CREATE] Failed: {e}")
        return 0x0110, None


def handle_n_set(event):
    ds = event.modification_list
    ae_title = event.assoc.requestor.ae_title

    logger.info(f"[MPPS N-SET] From AE: {ae_title}")
    logger.debug(f"[MPPS N-SET] Dataset:\n{ds}")

    try:
        send_n_action(ds, ae_title, action_type=3)
        return 0x0000, None
    except Exception as e:
        logger.error(f"[MPPS N-SET] Failed: {e}")
        return 0x0110, None
