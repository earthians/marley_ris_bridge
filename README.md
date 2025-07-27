
# Marley RIS Bridge


This is a CLI DICOM Modality Worklist (MWL) SCP with support for Modality Performed Procedure Step (MPPS) events.

## Usage

```bash
python -m marley_ris_bridge.app MARLEY-RIS --host 0.0.0.0 -p 104
```

## SCP Features

- C-ECHO (Verification)
- C-FIND (Modality Worklist)
- MPPS - N-CREATE (Start Study)
- MPPS - N-SET (Finish Study)

## Configure Marley backend site

```bash
config.json


{
    "host_name": "site-url",
    "api_key": "your-api-key",
    "api_secret": "your-api-secret"
}
```
