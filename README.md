# CamExtractor

**CamExtractor** is a modern web application for processing industrial cam motion profile data. It extracts position and degrees data from Excel files, calculates normalized "CAMPOINTS" with high precision, and exports results to CSV and XLSX formats.

## Features

- **Web Interface**: User-friendly React frontend with drag-and-drop upload.
- **Batch Processing**: Upload a `.zip` archive to process multiple files at once.
- **Visual Validation**: Interactive graphs and data tables to verify profile integrity.
- **Export Options**: Toggle CSV and XLSX output formats.
- **Dockerized**: Easy deployment via Docker Compose.

## Quick Start (Docker)

The recommended way to run CamExtractor is using Docker.

```bash
docker compose up -d
```

Open [http://localhost:5000](http://localhost:5000) in your browser.

## Development

To run the application locally for development:

```bash
# Start dev environment (hot-reloading)
docker compose -f docker-compose.dev.yml up --build
```

### Architecture
- **Frontend**: React + Vite (Port 5173 in dev)
- **Backend**: Python Flask (Port 5000)

## Legacy Usage (CLI)

You can still use the underlying Python script directly if you prefer the command line or `tkinter` GUI:

```bash
pip install -r requirements.txt
python main.py
```
*Note: This requires a local Python environment and display support for the file dialog.*

## Cam Logic

- **Regular Cam** (360 points): Detected when data has >37 entries. Normalized to 360.
- **Rotodex Cam** (180 points): Detected when data has ≤37 entries. Normalized to 180.
- **Precision**: Calculations use 6 decimal places of precision suitable for industrial motion control.
