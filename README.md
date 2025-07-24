
# Marley RIS Bridge


This is a CLI DICOM Modality Worklist (MWL) SCP. It uses a Marley instance as the backend.

## Usage

```bash
python -m marley_ris_bridge.app MARLEY --host 0.0.0.0 -p 104
```

## SCP Features

- C-ECHO (Verification)
- C-FIND (Modality Worklist)

## Configure Marley backend site

```bash
config.json


{
    "host_name": "site-url",
    "api_key": "your-api-key",
    "api_secret": "your-api-secret"
}
```
