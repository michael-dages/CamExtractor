# Cam Extractor - Project Context

## Project Overview
**CamExtractor** is a modern web application for industrial automation. It processes cam motion profile data from Excel files (`.xls`, `.xlsx`), generating normalized "CAMPOINTS" for machine control. The application features a **React** frontend for easy file uploads and visualization, backed by a **Flask** API that handles the complex data processing.

## Key Functionality
- **Web Interface:** Drag-and-drop file upload, interactive motion profile graphs, and data preview tables.
- **Batch Processing:** Upload a `.zip` archive containing multiple Excel files (including nested folders) to process them all at once. The system returns a single zip with all results.
- **Export Options:** Toggle CSV and XLSX generation on/off.
- **Core Processing:**
    - Auto-detection of "Regular" (360 points) vs "Rotodex" (180 points) profiles.
    - High-precision arithmetic using Python's `Decimal` module.
    - Normalization of degree values to standard "campoints".

## Architecture
The project is containerized using Docker and consists of:

1.  **Frontend (`frontend/`)**:
    - **Tech Stack:** React, Vite, Tailwind CSS.
    - **Duties:** UI, File Uploads, Visualization (Graphs/Charts), API Communication.

2.  **Backend (`app.py`, `main.py`)**:
    - **Tech Stack:** Python, Flask, Pandas, Matplotlib.
    - **`app.py`**: Flask API endpoints (`/process`, `/health`) handling file uploads and responses.
    - **`main.py`**: Core business logic. Validates data, calculates campoints, and generates export content.
    - **`campoints_excel_file.py`**: Handles Excel parsing and column detection.

## Usage

### Docker (Recommended)
The easiest way to run the application is via Docker Compose.

```bash
# Start the application
docker compose up -d

# Open browser
http://localhost:5000
```

### Development
For local development, you can run the backend and frontend separately or use the dev compose file:
```bash
docker compose -f docker-compose.dev.yml up --build
```

## Input Data Specification
The tool automatically scans Excel sheets for columns matching:
- **Set 1:** `POSITION` and `DEGREES`
- **Set 2:** `Cycle\n Position` and `Axis\n Position`

## Cam Logic
- **Rotodex Cam:** Position list length <= 37. Normalized to 180 points.
- **Regular Cam:** Default. Normalized to 360 points.
- **Formula:** `campoint = degree_value / total_points` (Decimal precision).
