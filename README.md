# Cam Extractor

A Python tool that extracts cam motion profile data from Excel files and generates CAMPOINTS data for industrial cam motion systems. The tool processes position and degrees data to calculate normalized cam points, exports results to CSV/XLSX formats, and visualizes the motion profile.

## Features

- **Interactive file selection** via GUI dialog (tkinter)
- **Multi-sheet scanning** to find valid data in any sheet
- **Dual cam type support**:
  - Regular Cam (360 campoints)
  - Rotodex Cam (180 campoints)
- **High-precision calculations** using Python's Decimal module
- **Multiple output formats**: CSV, XLSX, ASCII table, and interactive graph
- **Flexible column detection** supporting multiple naming conventions

## Prerequisites

- Python 3.x
- pandas
- openpyxl
- prettytable
- matplotlib
- xlrd

Install all dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Running the Application

```bash
python main.py
```

A file picker dialog will open. Select an Excel file (.xls or .xlsx) containing your cam data.

### Building Executable

Create a standalone executable using PyInstaller:
```bash
pyinstaller main.spec
```

The executable will be generated in the `dist/` directory.

## Input File Requirements

Excel files must contain columns with one of these naming patterns:
- `POSITION` and `DEGREES`, or
- `Cycle\n Position` and `Axis\n Position`

The tool automatically scans all sheets in the workbook to find valid data.

## Output Files

- **CSV**: `<original_filename>.csv` - Contains CAMPOINTS column with header `% MA_PERIODE=1 SL_PERIODE=1 CYCLIC=1`
- **XLSX**: `<original_filename>.xlsx` - Full table with Position, Degrees, and CAMPOINTS columns
- **Console**: ASCII table displaying all three columns
- **Graph**: Interactive matplotlib window showing the motion profile

## Architecture

### Two-Module Design

**main.py** - Main execution script that orchestrates:
- Data extraction and validation
- Cam point calculations using Decimal precision
- CSV/XLSX export generation
- ASCII table display
- Motion profile visualization

**campoints_excel_file.py** - Excel file handling class that provides:
- Interactive file selection dialog
- Multi-sheet scanning for valid data
- Column detection for position/degrees data

### Cam Types

**Regular Cam** (360 campoints):
- Detected when data has >37 position entries
- Final position normalized to 0

**Rotodex Cam** (180 campoints):
- Detected when data has ≤37 position entries
- Final position normalized to 180

### Calculation

CAMPOINTS are calculated by normalizing degrees:
```
campoint = degrees / num_campoints
```

All calculations use 6 decimal places of precision.

## Motion Profile
![Motion Profile](graphics/graph.png)

## Console Output
![Pretty Table](graphics/pretty_table.png)

