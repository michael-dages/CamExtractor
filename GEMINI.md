# Cam Extractor - Project Context

## Project Overview
**CamExtractor** is a Python-based utility designed for industrial automation applications. It extracts cam motion profile data from Excel files (`.xls`, `.xlsx`), processes it to generate normalized "CAMPOINTS," and exports the results to CSV and XLSX formats. It also provides visual validation via a generated motion profile graph (matplotlib) and a console-based ASCII table.

## Key Functionality
- **Input:** Excel files containing cam profile data (Position/Degrees).
- **Processing:**
    - Auto-detection of "Regular" (360 points) vs "Rotodex" (180 points) cam profiles based on data length.
    - Normalization of degree values to a standard "campoint" metric.
    - High-precision arithmetic using Python's `Decimal` module (truncated to 6 decimal places).
- **Output:**
    - **CSV:** Specialized format with header `% MA_PERIODE=1 SL_PERIODE=1 CYCLIC=1`.
    - **XLSX:** Detailed table including Position, Degrees, and calculated Campoints.
    - **Visualization:** Interactive Matplotlib graph of the motion profile.
    - **Console:** ASCII summary table.

## Architecture
The project consists of two primary Python modules:

1.  **`main.py` (Entry Point):**
    - Orchestrates the application flow.
    - Handles data cleaning (`remove_null_from_dataframe`), calculation (`panda_manipulation`), and export logic (`export_csv`, `export_xlsx`).
    - Generates visualizations (`create_graph`, `create_ascii_table`).
    - **Constants:**
        - `REGULAR_NUM_CAMPOINTS = 360`
        - `ROTODEX_NUM_CAMPOINTS = 180`
        - `TRUNCATE_POINTS = 6` (Decimal precision)

2.  **`campoints_excel_file.py`:**
    - Defines the `CampointsExcelFile` class.
    - Manages file I/O using `tkinter` (file dialog) and `pandas` (Excel reading).
    - Scans all sheets in a workbook to locate valid data columns.

## Usage

### Prerequisites
- Python 3.x
- **GUI Environment:** The application uses `tkinter` for file selection, requiring a display (or X11 forwarding).

### Installation
```bash
pip install -r requirements.txt
```

### Running the Application
```bash
python main.py
```
1.  A file dialog will open. Select your source Excel file.
2.  The script will scan sheets for valid columns.
3.  If valid, it generates outputs in the same directory as the source file and displays a graph.

## Input Data Specification
The tool automatically scans for columns matching **either** of these naming conventions:

**Set 1 (Standard):**
- `POSITION`
- `DEGREES`

**Set 2 (Alternative):**
- `Cycle\n Position`
- `Axis\n Position`

## Logic & Cam Types
- **Rotodex Cam:** Detected if position list length <= 37. Normalized to 180 points.
- **Regular Cam:** Default. Normalized to 360 points.
- **Normalization Formula:** `campoint = degree_value / total_points` (calculated with Decimal precision).

## Development Notes
- **Precision:** The `decimal` module is used explicitly to avoid floating-point errors common in industrial profile calculations.
- **Dependencies:** `pandas`, `openpyxl`, `prettytable`, `matplotlib`, `xlrd`.
- **Environment:** Since `tkinter` is used, running this in a headless container (like Docker) requires specific setup for display handling.
