# CLAUDE.md

This file provides guidance to Claude/AI assistants when working with code in this repository.

## Project Overview

**CamExtractor** is a containerized web application that processes industrial cam motion data from Excel files. It calculates normalized "CAMPOINTS" using high-precision decimal arithmetic and exports results to CSV/XLSX.

- **Frontend**: React + Vite (Dragon-drop upload, Visualization)
- **Backend**: Python Flask (API, Data Processing)
- **Deployment**: Docker Compose

## Core Architecture

### 1. Frontend (`frontend/`)
- **App.jsx**: Main React component handling file uploads (`axios`), state, and UI rendering.
- **Vite**: Build tool for fast development and optimized production builds.
- **Tailwind CSS**: Utility-first styling.

### 2. Backend (`app.py`)
- **API Entry Point**: Flask application serving the compiled frontend and exposing `/process`.
- **Endpoints**:
    - `POST /process`: Accepts `multipart/form-data`.
        - **Single Excel File**: Returns JSON with graph/table data and CSV/XLSX content.
        - **Zip File**: Returns a processed Zip file containing results for all files in the input archive.
    - `GET /health`: Simple health check.

### 3. Logic (`main.py`, `campoints_excel_file.py`)
- **`main.py`**: Business logic. `process_single_file` handles validation, calculation, and export.
- **`campoints_excel_file.py`**: Excel parsing wrapper using `pandas`. Scans sheets for valid columns (`POSITION`, `DEGREES`).

## Development Commands

### Docker (Recommended)
Run the full stack (Frontend + Backend) with hot-reloading context:
```bash
docker compose -f docker-compose.dev.yml up --build
```
- **Access**: `http://localhost:5000`
- **Logs**: `docker compose logs -f`

### Local (Manual)
If running without Docker:
1.  **Frontend**:
    ```bash
    cd frontend && npm run dev
    # Runs on port 5173
    ```
2.  **Backend**:
    ```bash
    pip install -r requirements.txt
    flask run --debug
    # Runs on port 5000
    ```

## Key Constants & Logic
- **Precision**: Uses `decimal.Decimal` with `TRUNCATE_POINTS = 6`.
- **Cam Types**:
    - **Regular**: 360 points (list > 37 items).
    - **Rotodex**: 180 points (list <= 37 items).
- **Export Header**: CSVs must use header `% MA_PERIODE=1 SL_PERIODE=1 CYCLIC=1`.

## Testing
- **Manual**: Use `curl` or the Web UI to upload `test.xlsx` or `test.zip`.
- **Scratch**: Use `scratch/` folder for temporary test files (ignored by git).
