# Copyright (c) 2025, earthians and contributors
# For license information, please see license.txt

import argparse
import logging
import signal
import sys
from logzero import logger, setup_logger
from pynetdicom import AE, evt
from pynetdicom._globals import ALL_TRANSFER_SYNTAXES
from pydicom.uid import UID

from handlers.echo import handle_echo
from handlers.find import handle_find
from handlers.mpps import handle_n_create, handle_n_set
from handlers.n_action import handle_n_action
from handlers.assoc import handle_assoc_accepted, handle_assoc_released
from config import get_config

MPPS_SOP_CLASS = UID("1.2.840.10008.3.1.2.3.3")
MPPS_NOTIFICATION_SOP_CLASS = UID("1.2.840.10008.3.1.2.5.3")

def start_scp(args):
    logger.info("Starting up Marley RIS Bridge...")
    ae = AE(ae_title=args.title)
    ae.maximum_associations = 5
    ae.add_supported_context("1.2.840.10008.1.1", ALL_TRANSFER_SYNTAXES)  # Verification
    ae.add_supported_context("1.2.840.10008.5.1.4.31", ALL_TRANSFER_SYNTAXES)  # MWL
    ae.add_supported_context(MPPS_SOP_CLASS, ALL_TRANSFER_SYNTAXES)
    ae.add_supported_context(MPPS_NOTIFICATION_SOP_CLASS, ALL_TRANSFER_SYNTAXES)

    handlers = [
        (evt.EVT_C_ECHO, handle_echo),
        (evt.EVT_C_FIND, handle_find),
        (evt.EVT_N_CREATE, handle_n_create),
        (evt.EVT_N_ACTION, handle_n_action),
        (evt.EVT_N_SET, handle_n_set),
        (evt.EVT_ACCEPTED, handle_assoc_accepted),
        (evt.EVT_RELEASED, handle_assoc_released),
    ]
    logger.info("Ready to receive connections")
    ae.start_server((args.host, int(args.port)), evt_handlers=handlers, block=True)

def stop_scp(signal=None, frame=None):
    logger.info("Shutting down Marley RIS Bridge...")
    sys.exit(0)

def main():
    """ python3 -m app MARLEY-SCP --host 0.0.0.0 -p 104 """

    parser = argparse.ArgumentParser()
    parser.add_argument("title")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("-p", "--port", default=104)
    args = parser.parse_args()

    try:
        setup_logger(logfile="./logs/marley_ris_bridge.log", maxBytes=10*1024*1024, backupCount=5)
    except Exception as e:
        import os
        os.makedirs("./logs", exist_ok=True)
        logger.info("Setup Logger failed, creating 'logs' directory")
        logger.debug(f"Setup Logger failed, creating 'logs' directory \n{e}")
        setup_logger(logfile="./logs/marley_ris_bridge.log", maxBytes=10*1024*1024, backupCount=5)

    config = get_config()
    level = getattr(logging, str(config.get("log_level", "INFO")).upper(), logging.INFO)
    logger.setLevel(level)

    signal.signal(signal.SIGINT, stop_scp)
    start_scp(args)

if __name__ == "__main__":
    main()
