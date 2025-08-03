from logzero import logger
from pydicom.dataset import Dataset
from pydicom.sequence import Sequence
from pydicom.valuerep import DA, TM
from datetime import date
from network.dicomweb import send_ups_rs_query


def handle_find(event):
    ds = event.identifier
    logger.info("[DIMSE C-FIND] Handler triggered")
    logger.debug(f"[DIMSE C-FIND] Incoming Dataset: {ds}")

    filters = build_filters(ds)
    worklist = send_ups_rs_query(event.assoc.requestor.ae_title, filters)

    for item in worklist:
        if event.is_cancelled:
            yield (0xFE00, None)
        else:
            yield (0xFF00, convert_ups_to_mwl_dataset(item))


def build_filters(ds):
    filters = {
        "00400002__from": date.today().strftime("%Y%m%d")
    }
    if ds.get("PatientID") and str(ds.PatientID) != "*":
        filters["00100020"] = str(ds.PatientID)
    if ds.get("PatientName") and str(ds.PatientName) != "*":
        filters["00100010"] = str(ds.PatientName)
    if ds.get("Modality"):
        filters["00081030"] = str(ds.Modality)

    logger.debug(f"[UPS-RS] Built filters: {filters}")
    return filters


def get_tag_value(item, tag, default=None):
    try:
        return item[tag]["Value"][0]
    except Exception:
        return default


def convert_ups_to_mwl_dataset(item):
    ds = Dataset()
    sps = Dataset()

    # Patient-level attributes
    ds.PatientID = get_tag_value(item, "00100020", "")
    ds.PatientName = get_tag_value(item, "00100010", "")
    ds.PatientSex = get_tag_value(item, "00100040", "U")
    dob = get_tag_value(item, "00100030")
    if dob:
        ds.PatientBirthDate = DA(dob)

    ds.AccessionNumber = get_tag_value(item, "00080050", "")

    # SPS-level attributes (0040,0100)
    modality = get_tag_value(item, "00081030", "")
    sps.Modality = modality
    sps.ScheduledProcedureStepDescription = f"{modality} Imaging Procedure"

    date = get_tag_value(item, "00400002")
    if date:
        sps.ScheduledProcedureStepStartDate = DA(date)

    dt = get_tag_value(item, "00404011")
    if dt and len(dt) >= 14:
        sps.ScheduledProcedureStepStartTime = TM(dt[8:])

    ds.ScheduledProcedureStepSequence = Sequence([sps])
    return ds
