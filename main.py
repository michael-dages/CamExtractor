# Import necessary tools
import os
import argparse
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

#Set the precision for Decimal operations
getcontext().prec = TRUNCATE_POINTS + 1

def create_ascii_table(input_dictionary, table):
    """Create an ascii table from the derived data"""
    for list in input_dictionary:
        table.add_column(list.title(), input_dictionary[list])
    table.align = "l"


def create_graph(cef, x_list, y_list):
    """Create graph using pyplot"""
    plt.plot(x_list, y_list)
    plt.title(cef.base_filename)
    plt.xlabel(POSITION_COLUMN[cef.position_index_found].title())
    plt.ylabel(DEGREES_COLUMN[cef.degrees_index_found].title())
    plt.get_current_fig_manager().set_window_title(cef.figure_title + " Motion Profile")
    plt.show()


def remove_null_from_dataframe(pandas_list):
    """Remove null values from list extracted via pandas library"""
    # Loop through the original and make changes to the new list
    clean_list = [items for items in pandas_list if pd.notna(items)]
    return clean_list


def panda_manipulation(cef):
    """Use the pandas library to retrieve the degrees column and create a list"""
    # Drop rows where either column is NaN so both lists stay the same length
    clean_df = cef.dataframe[[POSITION_COLUMN[cef.position_index_found], DEGREES_COLUMN[cef.degrees_index_found]]].dropna()
    position_list = clean_df[POSITION_COLUMN[cef.position_index_found]].tolist()
    degrees_list = clean_df[DEGREES_COLUMN[cef.degrees_index_found]].tolist()

    # Check if it's a rotodex cam
    if len(position_list) <= EXPECTED_ROTODEX_LIST_LENGTH:
        cef.is_rotodex_cam = True

    # Check if the list ends at 355 or 360 for regular cams, or 175 or 180 for rotodex cams
    if not cef.is_rotodex_cam:
        num_campoints = REGULAR_NUM_CAMPOINTS
        final_degrees_position = REGULAR_FINAL_CAMPOINT
    else:
        num_campoints = ROTODEX_NUM_CAMPOINTS
        final_degrees_position = ROTODEX_NUM_CAMPOINTS

    if position_list[-1] != num_campoints:
        position_list.append(num_campoints)
        degrees_list.append(final_degrees_position)

    # Create campoints list by dividing by the num campoints if the item isn't null
    precision_str = '0.' + '0' * TRUNCATE_POINTS
    campoints_list = [Decimal(index / num_campoints).quantize(Decimal(precision_str)) for index in degrees_list if
                      pd.notna(index)]

    # Create dictionary
    cef_dictionary = {
        POSITION_COLUMN[cef.position_index_found]: position_list,
        DEGREES_COLUMN[cef.degrees_index_found]: degrees_list,
        CAMPOINTS_COLUMN: campoints_list
    }
    return cef_dictionary


def export_xlsx():
    """Exports an XLSX version of the original file"""
    # Specify the output filename and path
    xlsx_filename = cef.filename_without_extension + ".xlsx"
    # Create the XLSX writer
    xlsx_writer = pd.ExcelWriter(xlsx_filename, engine="xlsxwriter")
    df = pd.DataFrame(cef_dict)
    df.to_excel(xlsx_writer, sheet_name="Values", index=False)
    xlsx_writer.save()


def export_csv(cef, csv_campoints_list):
    """Use the pandas library to export the campoints to CSV"""
    # Pandas dataframe to export CSV
    df = pd.DataFrame(csv_campoints_list, columns=[CSV_HEADER])
    df.to_csv(cef.csv_export_filename, index=False)


def process_single_file(cef, show_graph=True, show_table=True):
    """Process a single Excel file and export CSV. Returns True on success."""
    if not cef.is_valid_data():
        return False

    cef_dict = panda_manipulation(cef)

    br_campoints = cef_dict[CAMPOINTS_COLUMN].copy()

    export_csv(cef, br_campoints)

    if show_table:
        cef_table = PrettyTable()
        create_ascii_table(cef_dict, cef_table)
        print(cef_table)

    if show_graph:
        create_graph(
            cef,
            x_list=cef_dict[POSITION_COLUMN[cef.position_index_found]],
            y_list=cef_dict[DEGREES_COLUMN[cef.degrees_index_found]],
        )

    return True


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
            ok = process_single_file(cef, show_graph=False, show_table=False)
            if ok:
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
        cef = CampointsExcelFile()
        process_single_file(cef)


if __name__ == "__main__":
    main()
