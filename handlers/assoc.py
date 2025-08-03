from logzero import logger

active_callers = set()

def handle_assoc_accepted(event):
    ae_title = event.assoc.requestor.ae_title
    active_callers.add(ae_title)
    logger.info(f"[ASSOCIATE] {ae_title} connected. Active callers: {len(active_callers)}")

def handle_assoc_released(event):
    ae_title = event.assoc.requestor.ae_title
    active_callers.discard(ae_title)
    logger.info(f"[RELEASE] {ae_title} disconnected. Active callers: {len(active_callers)}")
