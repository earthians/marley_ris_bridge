from logzero import logger

def build_mpps_payload(ds):
    def safe_get(obj, key, default=""):
        return getattr(obj, key, default) or default

    study_uid = safe_get(ds, "StudyInstanceUID")
    accession_number = safe_get(ds, "AccessionNumber")
    status = safe_get(ds, "PerformedProcedureStepStatus").lower()
    patient_id = safe_get(ds, "PatientID")
    station_ae = safe_get(ds, "PerformedStationAETitle")
    performer = (
        safe_get(ds, "PerformedProcedureStepPerformerName") or
        safe_get(ds, "PerformingPhysicianName") or
        safe_get(ds, "ScheduledPerformingPhysicianName")
    )

    start_time = safe_get(ds, "PerformedProcedureStepStartDate") + safe_get(ds, "PerformedProcedureStepStartTime")
    end_time = safe_get(ds, "PerformedProcedureStepEndDate") + safe_get(ds, "PerformedProcedureStepEndTime")

    series = []
    instances = []

    if hasattr(ds, "PerformedSeriesSequence"):
        logger.debug("[MPPS PAYLOAD] Found PerformedSeriesSequence")
        for s in ds.PerformedSeriesSequence:
            series_uid = safe_get(s, "SeriesInstanceUID")
            series_desc = safe_get(s, "SeriesDescription")
            modality = safe_get(s, "Modality")

            series.append({
                "series_uid": series_uid,
                "study_uid": study_uid,
                "description": series_desc,
                "modality": modality,
            })

            if hasattr(s, "ReferencedImageSequence"):
                for i in s.ReferencedImageSequence:
                    sop_uid = safe_get(i, "ReferencedSOPInstanceUID")
                    sop_class = safe_get(i, "ReferencedSOPClassUID")
                    instances.append({
                        "sop_instance_uid": sop_uid,
                        "sop_class_uid": sop_class,
                        "series_uid": series_uid,
                        "study_uid": study_uid,
                    })

    payload = {
        "accession_number": accession_number,
        "study_instance_uid": study_uid,
        "patient": patient_id,
        "start_time": start_time,
        "end_time": end_time,
        "status": status,
        "series": series,
        "instances": instances,
        "performed_station_ae": station_ae,
        "performer_name": performer,
        "raw_ds": ds.to_json_dict(),
    }

    logger.debug(f"[MPPS PAYLOAD] Built payload with {len(ds)} DICOM tags")
    return payload
