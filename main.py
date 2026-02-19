# Import necessary tools
import os
import argparse
import base64
import io
import matplotlib.pyplot as plt
import pandas as pd
from prettytable import PrettyTable
from decimal import Decimal, getcontext
from campoints_excel_file import (
    CampointsExcelFile, DEGREES_COLUMN, POSITION_COLUMN,
    RED_TERMINAL_TEXT, GREEN_TERMINAL_TEXT, DEFAULT_TERMINAL_TEXT,
)

# Declare global constants
CSV_HEADER = '% MA_PERIODE=1 SL_PERIODE=1 CYCLIC=1'
CAMPOINTS_COLUMN = 'CAMPOINTS'
REGULAR_NUM_CAMPOINTS = 360
REGULAR_FINAL_CAMPOINT = 0
EXPECTED_ROTODEX_LIST_LENGTH = 37
ROTODEX_NUM_CAMPOINTS = 180
ROTODEX_FINAL_CAMPOINT = 1
TRUNCATE_POINTS = 6

# Set the precision for Decimal operations
getcontext().prec = TRUNCATE_POINTS + 1

def create_ascii_table(input_dictionary):
    """Create an ascii table from the derived data and return as string"""
    table = PrettyTable()
    columns = [POSITION_COLUMN[0], DEGREES_COLUMN[0], CAMPOINTS_COLUMN]
    # Map dictionary keys to standard column names if they differ
    for key in input_dictionary:
        title = key.title().replace('\n', ' ')
        table.add_column(title, input_dictionary[key])
    table.align = "l"
    return table

def create_graph(cef, x_list, y_list, headless=False):
    """Create graph using pyplot. Returns base64 string if headless."""
    plt.figure(figsize=(10, 6))
    plt.plot(x_list, y_list)
    plt.title(cef.base_filename)
    plt.xlabel(POSITION_COLUMN[cef.position_index_found].title().replace('\n', ' '))
    plt.ylabel(DEGREES_COLUMN[cef.degrees_index_found].title().replace('\n', ' '))
    
    if headless:
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        plt.close()
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        return img_base64
    else:
        try:
            plt.get_current_fig_manager().set_window_title(cef.figure_title + " Motion Profile")
            plt.show()
        except Exception:
            # Fallback if GUI fails
            plt.close()
    return None

def panda_manipulation(cef):
    """Use the pandas library to retrieve the degrees column and create a list"""
    # Drop rows where either column is NaN so both lists stay the same length
    clean_df = cef.dataframe[[POSITION_COLUMN[cef.position_index_found], DEGREES_COLUMN[cef.degrees_index_found]]].dropna()
    position_list = clean_df[POSITION_COLUMN[cef.position_index_found]].tolist()
    degrees_list = clean_df[DEGREES_COLUMN[cef.degrees_index_found]].tolist()

    # Check if it's a rotodex cam
    is_rotodex_cam = len(position_list) <= EXPECTED_ROTODEX_LIST_LENGTH
    cef.is_rotodex_cam = is_rotodex_cam

    # Check if the list ends at 355 or 360 for regular cams, or 175 or 180 for rotodex cams
    if not is_rotodex_cam:
        num_campoints = REGULAR_NUM_CAMPOINTS
        final_degrees_position = REGULAR_FINAL_CAMPOINT
    else:
        num_campoints = ROTODEX_NUM_CAMPOINTS
        final_degrees_position = ROTODEX_FINAL_CAMPOINT

    if position_list[-1] != num_campoints:
        position_list.append(num_campoints)
        degrees_list.append(final_degrees_position)

    # Create campoints list by dividing by the num campoints if the item isn't null
    precision_str = '0.' + '0' * TRUNCATE_POINTS
    campoints_list = [Decimal(float(index) / num_campoints).quantize(Decimal(precision_str)) for index in degrees_list if
                      pd.notna(index)]

    # Create dictionary
    cef_dictionary = {
        POSITION_COLUMN[cef.position_index_found]: position_list,
        DEGREES_COLUMN[cef.degrees_index_found]: degrees_list,
        CAMPOINTS_COLUMN: campoints_list
    }
    return cef_dictionary

def export_xlsx(cef, cef_dict, output_path=None):
    """Exports an XLSX version of the data"""
    xlsx_filename = output_path or (cef.filename_without_extension + ".xlsx")
    df = pd.DataFrame(cef_dict)
    df.to_excel(xlsx_filename, index=False)
    return xlsx_filename

def export_csv(cef, csv_campoints_list, output_path=None):
    """Use the pandas library to export the campoints to CSV"""
    df = pd.DataFrame(csv_campoints_list, columns=[CSV_HEADER])
    filename = output_path or cef.csv_export_filename
    df.to_csv(filename, index=False)
    return filename

def process_single_file(cef, show_graph=True, show_table=True, headless=False):
    """Process a single Excel file. Returns results dict on success, None on failure."""
    if not cef.is_valid_data(verbose=not headless):
        return None

    cef_dict = panda_manipulation(cef)
    
    # Export files if not headless (CLI/GUI mode)
    if not headless:
        export_csv(cef, cef_dict[CAMPOINTS_COLUMN])
        export_xlsx(cef, cef_dict)

    ascii_table = None
    if show_table:
        ascii_table = create_ascii_table(cef_dict)
        if not headless:
            print(ascii_table)

    graph_data = None
    if show_graph or headless:
        graph_data = create_graph(
            cef,
            x_list=cef_dict[POSITION_COLUMN[cef.position_index_found]],
            y_list=cef_dict[DEGREES_COLUMN[cef.degrees_index_found]],
            headless=headless
        )

    return {
        'data': cef_dict,
        'table': str(ascii_table) if ascii_table else None,
        'graph_base64': graph_data,
        'filename': cef.base_filename
    }

def find_excel_files(folder_path):
    """Recursively find all .xlsx/.xls files under folder_path, skipping temp files."""
    excel_files = []
    for root, _dirs, files in os.walk(folder_path):
        for filename in files:
            if filename.startswith("~$"):
                continue
            if filename.lower().endswith((".xlsx", ".xls")):
                excel_files.append(os.path.join(root, filename))
    return excel_files

def process_batch(folder_path):
    """Process all Excel files in a folder tree."""
    if not os.path.isdir(folder_path):
        print(f"{RED_TERMINAL_TEXT}Error:{DEFAULT_TERMINAL_TEXT} '{folder_path}' is not a valid directory.")
        return

    excel_files = find_excel_files(folder_path)

    if not excel_files:
        print(f"No Excel files found in '{folder_path}'.")
        return

    print(f"Found {len(excel_files)} Excel file(s) in '{folder_path}'\n")

    succeeded = 0
    failed = 0
    skipped = 0

    for filepath in excel_files:
        rel_path = os.path.relpath(filepath, folder_path)
        try:
            cef = CampointsExcelFile(file_path=filepath)
            result = process_single_file(cef, show_graph=False, show_table=False)
            if result:
                print(f"  {GREEN_TERMINAL_TEXT}OK{DEFAULT_TERMINAL_TEXT}      {rel_path}")
                succeeded += 1
            else:
                print(f"  {RED_TERMINAL_TEXT}SKIPPED{DEFAULT_TERMINAL_TEXT} {rel_path} (no valid cam data)")
                skipped += 1
        except Exception as e:
            print(f"  {RED_TERMINAL_TEXT}FAILED{DEFAULT_TERMINAL_TEXT}  {rel_path} ({e})")
            failed += 1

    print(f"\nSummary: {len(excel_files)} total, {succeeded} succeeded, {skipped} skipped, {failed} failed")

def main():
    parser = argparse.ArgumentParser(description="Extract cam motion profile data from Excel files.")
    parser.add_argument("-f", "--folder", type=str, help="Batch process all Excel files in the given folder (recursive).")
    args = parser.parse_args()

    if args.folder:
        process_batch(args.folder)
    else:
        try:
            cef = CampointsExcelFile()
            process_single_file(cef)
        except Exception as e:
            print(f"{RED_TERMINAL_TEXT}Error:{DEFAULT_TERMINAL_TEXT} {e}")

if __name__ == "__main__":
    main()
