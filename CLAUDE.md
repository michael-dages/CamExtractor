# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CamExtractor is a Python tool that extracts cam motion profile data from Excel files and generates CAMPOINTS data for industrial cam motion systems. It processes position and degrees data to calculate normalized cam points, then exports results to CSV/XLSX formats and visualizes the motion profile.

## Core Architecture

### Two-Module Design

**main.py** - Main execution script that orchestrates the workflow:
- Data extraction and validation
- Cam point calculations using Decimal precision
- CSV/XLSX export generation
- ASCII table display (PrettyTable)
- Motion profile visualization (matplotlib)

**campoints_excel_file.py** - Excel file handling class (CampointsExcelFile):
- Interactive file selection dialog (tkinter)
- Multi-sheet scanning for valid data
- Column detection for position/degrees data
- Supports two column naming conventions:
  - Standard: 'POSITION' and 'DEGREES'
  - Alternative: 'Cycle\n Position' and 'Axis\n Position'

### Data Flow

1. User selects Excel file via GUI dialog
2. CampointsExcelFile scans sheets for valid POSITION/DEGREES columns
3. main.py extracts data and removes null values
4. Determines cam type: Regular (360 points) or Rotodex (180 points)
5. Calculates CAMPOINTS by normalizing degrees: `campoint = degrees / num_campoints`
6. Exports CSV with header `% MA_PERIODE=1 SL_PERIODE=1 CYCLIC=1`
7. Displays ASCII table and motion profile graph

### Cam Types

**Regular Cam**:
- 360 campoints total
- Detected when data has >37 position entries
- Final position normalized to 0

**Rotodex Cam**:
- 180 campoints total
- Detected when data has ≤37 position entries
- Final position normalized to 180

### Precision Handling

The code uses Python's `Decimal` module with configurable precision (TRUNCATE_POINTS=6) to ensure accurate floating-point calculations for industrial applications.

## Development Commands

### Running the Application

```bash
python main.py
```

This will open a file picker dialog to select an Excel file (.xls or .xlsx) containing cam data.

### Installing Dependencies

```bash
pip install -r requirements.txt
```

Required packages: pandas, openpyxl, prettytable, matplotlib, xlrd

### Building Executable

The project uses PyInstaller to create standalone executables:

```bash
pyinstaller main.spec
```

The generated executable will be in the `dist/` directory.

### Docker Usage

```bash
docker build -t camextractor .
docker run -it camextractor
```

Note: The tkinter file dialog requires X11 forwarding or display configuration in containerized environments.

## Key Constants and Configuration

- `REGULAR_NUM_CAMPOINTS = 360` - Number of points for regular cams
- `ROTODEX_NUM_CAMPOINTS = 180` - Number of points for rotodex cams
- `EXPECTED_ROTODEX_LIST_LENGTH = 37` - Threshold to detect rotodex vs regular
- `TRUNCATE_POINTS = 6` - Decimal precision for campoint calculations
- `CSV_HEADER = '% MA_PERIODE=1 SL_PERIODE=1 CYCLIC=1'` - Required header for output CSV

## Input File Requirements

Excel files must contain columns with one of these naming patterns:
- 'POSITION' and 'DEGREES', or
- 'Cycle\n Position' and 'Axis\n Position'

The scanner checks all sheets in the workbook to find valid data.

## Output Files

- **CSV**: `<original_filename>.csv` - CAMPOINTS column only with special header
- **XLSX**: `<original_filename>.xlsx` - Full table with Position, Degrees, and CAMPOINTS columns
- **Graph**: Interactive matplotlib window showing motion profile
- **Console**: ASCII table with PrettyTable showing all three columns
