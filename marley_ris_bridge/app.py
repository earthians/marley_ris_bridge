# Copyright (c) 2025, earthians and contributors
# For license information, please see license.txt

import argparse
import json
import logging
import requests
import signal
import sys

from datetime import date
from logzero import logger, setup_logger
from pynetdicom import AE, evt
from pynetdicom._globals import ALL_TRANSFER_SYNTAXES
from pydicom.dataset import Dataset
from pydicom.sequence import Sequence
from pydicom.valuerep import DA, TM

from pynetdicom.sop_class import (
	Verification,
	ModalityWorklistInformationFind,
)

CONFIG_PATH = "./marley_ris_bridge/config.json"
ae = "MARLEY-RIS"
config = {}
active_callers = set()

appointment_worklist_map = { #TODO: map
	"patient_name": "PatientName", # (0010,0010)
	"patient": "PatientID", # (0010,0020)
	"date_of_birth": "PatientBirthDate", # (0010,0030)
	"gender": "PatientSex", # (0010,0040)
	"name": "AccessionNumber", # (0008,0050)
	# "requested_procedure_id": "RequestedProcedureID", # (0040,1001)
	# "scheduled_procedure_step_id": "ScheduledProcedureStepID", # (0040,0009)
	# "scheduled_station_ae_title": "ScheduledStationAETitle", # (0040,0001)
	# "scheduled_procedure_step_start_date": "ScheduledProcedureStepStartDate", # (0040,0002)
	# "scheduled_procedure_step_start_time": "ScheduledProcedureStepStartTime", # (0040,0003)
	# "modality": "Modality", # (0008,0060)
	# "scheduled_performing_physician_name": "ScheduledPerformingPhysicianName", # (0040,0006)
	# "scheduled_procedure_step_description": "ScheduledProcedureStepDescription", # (0040,0007)
	# "scheduled_procedure_step_location": "ScheduledProcedureStepLocation", # (0040,0010)
	# "pre_medication": "PreMedication", # (0040,0012)
	# "requesting_physician": "RequestingPhysician", # (0032,1032)
}

def handle_echo(event):
	logger.info("C-ECHO triggered")
	return 0x0000

def handle_find(event):
	ds = event.identifier
	logger.info("C-FIND handler triggered")
	logger.debug(f"[C-FIND] Incoming Dataset: {ds}")

	filters = build_filters(ds)
	worklist = send_ups_rs_query(filters)
	if len(worklist):
		logger.debug(f"[C-FIND] UPS-RS complete, returning {len(worklist)} MWL item(s)")

	def get_tag(item, tag, default=None):
		try:
			return item[tag]["Value"][0]
		except Exception:
			return default

	for item in worklist:
		if event.is_cancelled:
			yield (0xFE00, None)
			return

		identifier = Dataset()
		sps = Dataset()

		# Patient-level fields
		identifier.PatientID = get_tag(item, "00100020", "")
		identifier.PatientName = get_tag(item, "00100010", "")
		identifier.PatientSex = get_tag(item, "00100040", "U")
		dob = get_tag(item, "00100030")
		if dob:
			identifier.PatientBirthDate = DA(dob)

		identifier.AccessionNumber = get_tag(item, "00080050", "")

		# Scheduled Procedure Step (0040,0100)
		sps.Modality = get_tag(item, "00081030", "")
		sps.ScheduledProcedureStepDescription = f"{get_tag(item, '00081030', '')} Imaging Procedure"

		scheduled_date = get_tag(item, "00400002")
		if scheduled_date:
			sps.ScheduledProcedureStepStartDate = DA(scheduled_date)

		scheduled_dt = get_tag(item, "00404011")
		if scheduled_dt and len(scheduled_dt) >= 14:
			sps.ScheduledProcedureStepStartTime = TM(scheduled_dt[8:])  # HHMMSS

		identifier.ScheduledProcedureStepSequence = Sequence([sps])

		yield (0xFF00, identifier)

def handle_assoc_accepted(event):
	ae_title = event.assoc.requestor.ae_title
	active_callers.add(ae_title)
	logger.debug(f"[ASSOCIATE] {ae_title} connected. Active: {len(active_callers)}")

def handle_assoc_released(event):
	ae_title = event.assoc.requestor.ae_title
	active_callers.discard(ae_title)
	logger.debug(f"[RELEASE] {ae_title} disconnected. Active: {len(active_callers)}")

def send_ups_rs_query(filters):
	fields = list(appointment_worklist_map.keys())
	config = get_config()
	url = f"{config['host_name'].rstrip('/')}/api/method/healthcare.healthcare.api.ups_rs.get_ups_tasks"
	headers = {
		"Authorization": f"token {config['api_key']}:{config['api_secret']}",
		"Accept": "application/json",
	}
	payload = {"fields": json.dumps(fields), "filters": json.dumps(filters)}
	try:
		logger.debug(f"[C-FIND] Sending UPS-RS to {url}: {payload}")
		r = requests.get(url, headers=headers, params=payload)
		logger.debug(f"[C-FIND] UPS-RS Response: {r.status_code} - {r.text}")
		r.raise_for_status()
		return r.json().get("message", [])
	except Exception as e:
		logger.debug(f"[C-FIND] UPS-RS failed: {e}")
		return []

def build_filters(ds):
	filters = {
		"00400002__from": date.today().strftime("%Y%m%d") # dates from today only
	}
	if ds.get("PatientID") and str(ds.PatientID) != "*":
		filters["00100020"] = str(ds.PatientID)

	if ds.get("PatientName") and str(ds.PatientName) != "*":
		filters["00100010"] = str(ds.PatientName)

	if ds.get("Modality"):
		filters["00081030"] = str(ds.Modality)

	logger.debug(f"Build UPS filters:\n{filters}")
	return filters

def get_config():
	global config
	if not config:
		with open(CONFIG_PATH) as f:
			config = json.load(f)
			logger.debug(f"Read config:\n{config}")
	return config

def start_scp(args):
	""" Start SCP for required contexts, C-ECHO, C-FIND """
	logger.info("Starting up Marley RIS Bridge...")
	global ae
	ae = AE(ae_title=args.title)
	ae.maximum_associations = 5
	ae.add_supported_context(Verification, ALL_TRANSFER_SYNTAXES)
	ae.add_supported_context(ModalityWorklistInformationFind, ALL_TRANSFER_SYNTAXES)

	handlers = [
		(evt.EVT_C_ECHO, handle_echo),
		(evt.EVT_C_FIND, handle_find),
		(evt.EVT_ACCEPTED, handle_assoc_accepted),
		(evt.EVT_RELEASED, handle_assoc_released),
	]
	logger.info("Ready to receive connections")
	ae.start_server((args.host, int(args.port)), evt_handlers=handlers, block=True)

def stop_scp(signal=None, frame=None):
	""" Ctrl+C """
	logger.info("Shutting down Marley RIS Bridge...")
	# ae.shutdown() # FIXME: doesn't return
	sys.exit(0)

def main():
	""" python3.11 -m marley_ris_bridge.app MARLEY-SCP --host 0.0.0.0 -p 104 """
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

	level_str = str(config.get("log_level", "INFO")).upper()
	level = getattr(logging, level_str, logging.INFO)
	logger.setLevel(level)

	signal.signal(signal.SIGINT, stop_scp)
	start_scp(args)

if __name__ == "__main__":
	main()
