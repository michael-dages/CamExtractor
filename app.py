import os
import io
import zipfile
import base64
import pandas as pd
from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix
from main import process_single_file, CAMPOINTS_COLUMN
from campoints_excel_file import CampointsExcelFile

app = Flask(__name__, static_folder='static')
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
CORS(app)

# Wire up logging to Gunicorn if available
if __name__ != '__main__':
    import logging
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

# Configuration
# UPLOAD_FOLDER no longer strictly needed if doing in-memory, but good for temp if needed

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "service": "CamExtractor API"})

@app.route('/process', methods=['POST'])
def process_files():
    # Retrieve files from both 'files' (legacy/multi) and 'file' (single) fields
    files_list = request.files.getlist('files') + request.files.getlist('file')
    
    if not files_list:
        return jsonify({"error": "No files provided"}), 400

    # Retrieve export flags (default to true if not provided)
    # Frontend sends 'true'/'false' strings
    export_csv = request.form.get('export_csv', 'true').lower() == 'true'
    export_excel = request.form.get('export_excel', 'true').lower() == 'true'

    # Relaxed detection: Check if the first file is a zip, ignoring length check
    # taking into account some browsers might send empty fields or multiple files where one is the zip
    is_zip = False
    zip_file = None
    
    for f in files_list:
        if f.filename and f.filename.lower().endswith('.zip'):
            is_zip = True
            zip_file = f
            break

    if is_zip and zip_file:
        # Output zip buffer
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as output_zip:
            try:
                with zipfile.ZipFile(zip_file) as input_zip:
                    for item in input_zip.infolist():
                        # Skip directories and hidden/OS files
                        if item.is_dir() or item.filename.startswith('__MACOSX') or item.filename.startswith('.'):
                            continue
                        
                        if item.filename.lower().endswith(('.xlsx', '.xls')):
                            # Read file from zip
                            with input_zip.open(item) as extracted_file:
                                file_bytes = extracted_file.read()
                                file_stream = io.BytesIO(file_bytes)
                                
                                # Process
                                process_and_add_to_zip(file_stream, item.filename, output_zip, export_csv, export_excel)
            except zipfile.BadZipFile:
                 return jsonify({"error": "Invalid zip file"}), 400

        zip_buffer.seek(0)
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name='processed_cams.zip'
        )
    
    # Standard processing for Excel files (returns JSON)
    results = []
    
    for file in files_list:
        if not file.filename:
            continue
            
        # Skip if not excel (though we might want to check extension)
        if not file.filename.lower().endswith(('.xlsx', '.xls')):
            continue

        file_bytes = file.read()
        file_stream = io.BytesIO(file_bytes)
        
        try:
            # Create the Excel handler with the stream
            cef = CampointsExcelFile(file_stream=file_stream, original_filename=file.filename)
            
            # Process headlessly
            result = process_single_file(cef, show_graph=True, show_table=True, headless=True)
            
            if result:
                response_item = {
                    "filename": file.filename,
                    "success": True,
                    "table": result['table'],
                    "graph": result['graph_base64'],
                    "campoints": [str(c) for c in result['data'][CAMPOINTS_COLUMN]]
                }

                if export_csv:
                    # Create CSV string
                    CSV_HEADER = '% MA_PERIODE=1 SL_PERIODE=1 CYCLIC=1'
                    df_csv = pd.DataFrame(result['data'][CAMPOINTS_COLUMN], columns=[CSV_HEADER])
                    response_item["csv"] = df_csv.to_csv(index=False)
                
                if export_excel:
                    # Create XLSX bytes (base64 for JSON transport)
                    xlsx_buf = io.BytesIO()
                    df_xlsx = pd.DataFrame(result['data'])
                    df_xlsx.to_excel(xlsx_buf, index=False)
                    xlsx_buf.seek(0)
                    response_item["xlsx"] = base64.b64encode(xlsx_buf.read()).decode('utf-8')

                # Add to results list for the UI
                results.append(response_item)
            else:
                results.append({
                    "filename": file.filename,
                    "success": False,
                    "error": "No valid cam data found"
                })
        except Exception as e:
            results.append({
                "filename": file.filename,
                "success": False,
                "error": str(e)
            })

    return jsonify({"results": results})

def process_and_add_to_zip(file_stream, original_filename, output_zip, export_csv=True, export_excel=True):
    try:
        # Create handler
        cef = CampointsExcelFile(file_stream=file_stream, original_filename=original_filename)
        
        # Process headlessly
        result = process_single_file(cef, show_graph=False, show_table=False, headless=True)
        
        if result:
            # Prepare base filename (strip extension)
            base_name = os.path.splitext(original_filename)[0]
            
            if export_csv:
                # 1. Add CSV
                CSV_HEADER = '% MA_PERIODE=1 SL_PERIODE=1 CYCLIC=1'
                df_csv = pd.DataFrame(result['data'][CAMPOINTS_COLUMN], columns=[CSV_HEADER])
                csv_content = df_csv.to_csv(index=False)
                output_zip.writestr(f"{base_name}.csv", csv_content)
            
            if export_excel:
                # 2. Add XLSX
                xlsx_buf = io.BytesIO()
                df_xlsx = pd.DataFrame(result['data'])
                df_xlsx.to_excel(xlsx_buf, index=False)
                output_zip.writestr(f"{base_name}_processed.xlsx", xlsx_buf.getvalue())
            
    except Exception as e:
        print(f"Failed to process {original_filename}: {e}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
