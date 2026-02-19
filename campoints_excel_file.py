import os
import pandas as pd
import logging

# Set up logging for headless operations
logger = logging.getLogger(__name__)

# Declare global constants
POSITION_COLUMN = ['POSITION', "Cycle\n Position"]
DEGREES_COLUMN = ['DEGREES', "Axis\n Position"]
DEFAULT_TERMINAL_TEXT = '\033[0m'
RED_TERMINAL_TEXT = '\033[31m'
GREEN_TERMINAL_TEXT = '\033[32m'
BLUE_TERMINAL_TEXT = '\033[34m'

class CampointsExcelFile:
    """Retrieve Excel file and store csv filename in the same path"""

    def __init__(self, file_path=None, file_stream=None, original_filename=None):
        """
        Initialize with a file path or a file stream (e.g. from a web upload).
        """
        if file_path is not None:
            self.filename_with_path = file_path
        elif file_stream is not None:
            # For web uploads, we might only have a stream and a filename
            self.filename_with_path = original_filename or "uploaded_file.xlsx"
            self.file_stream = file_stream
        else:
            # Fallback to tkinter only if no path/stream provided (interactive mode)
            try:
                from tkinter.filedialog import askopenfilename
                self.filename_with_path = askopenfilename(filetypes=[("Excel files", ".xlsx .xls")])
            except (ImportError, RuntimeError):
                raise RuntimeError("No input file provided and GUI is not available.")

        # Get the full UNC without the extension
        self.filename_without_extension = os.path.splitext(self.filename_with_path)[0]
        # Filename only, no extension, no path
        self.figure_title = os.path.basename(self.filename_without_extension)
        # Full UNC with csv extension
        self.csv_export_filename = self.filename_without_extension + ".csv"
        # Filename only with extension
        self.base_filename = os.path.basename(self.filename_with_path)
        self.filepath = os.path.dirname(self.filename_with_path)
        self.dataframe = None
        self.is_rotodex_cam = False
        self.degrees_index_found = None
        self.position_index_found = None
        self.file_stream = getattr(self, 'file_stream', None)

    def is_valid_data(self, verbose=True):
        """Check if the uploaded Excel file is valid"""
        file_validity = False
        source = self.file_stream if self.file_stream is not None else self.filename_with_path
        
        try:
            xl = pd.ExcelFile(source)
            # Loop through each sheet
            for sheet in xl.sheet_names:
                if verbose:
                    print(f'Scanning sheet {BLUE_TERMINAL_TEXT}{sheet}{DEFAULT_TERMINAL_TEXT}')
                
                df = pd.read_excel(xl, sheet)
                # Check if the data we're looking for exists
                degrees_index = next((i for i, column in enumerate(DEGREES_COLUMN) if column in df), None)
                position_index = next((i for i, column in enumerate(POSITION_COLUMN) if column in df), None)

                # Only proceed if both columns were found
                if degrees_index is not None and position_index is not None:
                    if verbose:
                        print(f"  {DEGREES_COLUMN[degrees_index]} Index: {degrees_index}")
                        print(f"  {POSITION_COLUMN[position_index]} Index: {position_index}")

                    # Store the valid indices and dataframe
                    self.degrees_index_found = degrees_index
                    self.position_index_found = position_index
                    self.dataframe = df
                    file_validity = True
                    break
                else:
                    if verbose:
                        print(f"  Skipping - required columns not found")
            
            if verbose:
                if file_validity:
                    print(f"{GREEN_TERMINAL_TEXT}Valid{DEFAULT_TERMINAL_TEXT} excel file. Continuing...")
                else:
                    print(f"{RED_TERMINAL_TEXT}Invalid{DEFAULT_TERMINAL_TEXT} excel file.")
            
            return file_validity
        except Exception as e:
            logger.error(f"Error validating Excel data: {e}")
            if verbose:
                print(f"{RED_TERMINAL_TEXT}Error:{DEFAULT_TERMINAL_TEXT} {e}")
            return False
