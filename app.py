import os
import io
import zipfile
import base64
import pandas as pd
from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
from main import process_single_file, export_csv, export_xlsx, CAMPOINTS_COLUMN
from campoints_excel_file import CampointsExcelFile

app = Flask(__name__, static_folder='static')
CORS(app)

# Configuration
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

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
    if 'files' not in request.files:
        return jsonify({"error": "No files provided"}), 400
    
    files = request.files.getlist('files')
    results = []
    
    # We'll store processed files in memory for a zip if needed
    processed_files_memory = []

    for file in files:
        if not file.filename:
            continue
            
        file_bytes = file.read()
        file_stream = io.BytesIO(file_bytes)
        
        try:
            # Create the Excel handler with the stream
            cef = CampointsExcelFile(file_stream=file_stream, original_filename=file.filename)
            
            # Process headlessly
            result = process_single_file(cef, show_graph=True, show_table=True, headless=True)
            
            if result:
                # Create CSV string
                CSV_HEADER = '% MA_PERIODE=1 SL_PERIODE=1 CYCLIC=1'
                df_csv = pd.DataFrame(result['data'][CAMPOINTS_COLUMN], columns=[CSV_HEADER])
                csv_content = df_csv.to_csv(index=False)
                
                # Create XLSX bytes (base64 for JSON transport)
                xlsx_buf = io.BytesIO()
                df_xlsx = pd.DataFrame(result['data'])
                df_xlsx.to_excel(xlsx_buf, index=False)
                xlsx_buf.seek(0)
                xlsx_base64 = base64.b64encode(xlsx_buf.read()).decode('utf-8')

                # Add to results list for the UI
                results.append({
                    "filename": file.filename,
                    "success": True,
                    "table": result['table'],
                    "graph": result['graph_base64'],
                    "csv": csv_content,
                    "xlsx": xlsx_base64,
                    "campoints": [str(c) for c in result['data'][CAMPOINTS_COLUMN]]
                })
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

@app.route('/download-zip', methods=['POST'])
def download_zip():
    # This would ideally be more robust, but for a session-based approach:
    # We expect the frontend to send the results they want to zip or we store them.
    # For now, let's just implement a simple zip creator.
    data = request.json
    # ... logic to recreate zip based on processed data ...
    return jsonify({"message": "Not implemented in prototype, but planned."})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
