# Marley RIS Bridge

A Python-based DICOM DIMSE to DICOMWeb bridge for Marley Healthcare.

## Purpose
This utility connects classic DICOM modalities to the Marley DICOMWeb UPS-RS backend using:

- `C-FIND` to UPS-RS query (`/dicom-web/workitems`)
- `MPPS N-CREATE` to UPS claim
- `MPPS N-SET` (Completed) to UPS complete
- `UPS N-ACTION` forwarding

---

## Installation

### 1. Python Virtual Environment
```bash
python3 -m venv env
source env/bin/activate
```

### 2. Configure
Create a file at `marley_ris_bridge/config.py`:
```json
{
  "host_name": "https://marley.example.com",
  "ae_title": "MARLEY-RIS",
  "ae_token": "your-shared-token",
  "api_key": "userapikey",
  "api_secret": "userapisecret",
  "log_level": "DEBUG"
}
```

---

## Usage (CLI)
```bash
python3 -m app MARLEY-SCP --host 0.0.0.0 -p 104
```

---

## Auth
- DICOMWeb requests use Frappe token based auth (config.py)
- Legacy `/api/method` APIs use `Authorization: token <api_key>:<api_secret>`

---

## Testing with `findscu` utility
```bash
findscu -v -S -aet TESTMODALITY -aec MARLEY-RIS localhost 104 -k 0008,0050=*
```
