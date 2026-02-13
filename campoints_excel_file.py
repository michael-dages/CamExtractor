from tkinter.filedialog import *
import os
import pandas as pd

# Declare global constants
POSITION_COLUMN = ['POSITION', "Cycle\n Position"]
DEGREES_COLUMN = ['DEGREES', "Axis\n Position"]
DEFAULT_TERMINAL_TEXT = '\033[0m'
RED_TERMINAL_TEXT = '\033[31m'
GREEN_TERMINAL_TEXT = '\033[32m'
BLUE_TERMINAL_TEXT = '\033[34m'


class CampointsExcelFile:
    """Retrieve Excel file and store csv filename in the same path"""

    def __init__(self, file_path=None):
        # Retrieve filename + UNC
        if file_path is not None:
            self.filename_with_path = file_path
        else:
            self.filename_with_path = askopenfilename(filetypes=[("Excel files", ".xlsx .xls")])
        # Get the full UNC without the extension
        self.filename_without_extension = os.path.splitext(self.filename_with_path)[0]
        # Filename only, no extension, no path
        self.figure_title = os.path.basename(self.filename_with_path.split('.')[0])
        # Full UNC with csv extension
        self.csv_export_filename = self.filename_without_extension + ".csv"
        # Filename only with extension
        self.base_filename = os.path.basename(self.filename_with_path)
        self.___filepath = os.path.dirname(self.filename_with_path)
        self.dataframe = None
        self.is_rotodex_cam = False
        self.degrees_index_found = None
        self.position_index_found = None

    def is_valid_data(self):
        """Check if the uploaded Excel file is valid"""
        # Read Excel file in pandas

        # Assign the validity to false, initially
        file_validity = False
        # Check for a valid campoints sheet in the pandas dataframe
        try:
            xl = pd.ExcelFile(self.filename_with_path)
            # Loop through each sheet
            for sheet in xl.sheet_names:
                print(f'Scanning sheet {BLUE_TERMINAL_TEXT}{sheet}{DEFAULT_TERMINAL_TEXT}')
                xl.parse(sheet)
                df = pd.read_excel(xl, sheet)
                # Check if the data we're looking for exists
                degrees_index = next((i for i, column in enumerate(DEGREES_COLUMN) if column in df), None)
                position_index = next((i for i, column in enumerate(POSITION_COLUMN) if column in df), None)

                # Only proceed if both columns were found
                if degrees_index is not None and position_index is not None:
                    print(f"{DEGREES_COLUMN[degrees_index]} Index: {degrees_index}")
                    print(f"{POSITION_COLUMN[position_index]} Index:{position_index}")

                    if (DEGREES_COLUMN[degrees_index] in df) and (
                            POSITION_COLUMN[position_index] in df):
                        # Store the valid indices and dataframe
                        self.degrees_index_found = degrees_index
                        self.position_index_found = position_index
                        self.dataframe = df
                        # Set the file validity to true and break
                        file_validity = True
                        break
                else:
                    print(f"  Skipping - required columns not found")
            # Check the file validity to determine the output text
            if file_validity:
                print(f"{GREEN_TERMINAL_TEXT}Valid{DEFAULT_TERMINAL_TEXT} excel file.  Continuing...")
            else:
                print(f"{RED_TERMINAL_TEXT}Invalid{DEFAULT_TERMINAL_TEXT} excel file. Exiting...")
            return file_validity
        except Exception as e:
            print(e)





