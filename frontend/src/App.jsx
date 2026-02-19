import React, { useState, useCallback } from 'react';
import axios from 'axios';
import { Upload, FileSpreadsheet, Download, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const API_BASE = 'http://localhost:5000';

function App() {
  const [isUploading, setIsUploading] = useState(false);
  const [results, setResults] = useState([]);
  const [dragActive, setDragActive] = useState(false);

  const processFiles = async (files) => {
    setIsUploading(true);
    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
      formData.append('files', files[i]);
    }

    try {
      // Use 'blob' to handle binary zip or json
      const response = await axios.post(`${API_BASE}/process`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        responseType: 'blob'
      });

      const contentType = response.headers['content-type'];

      if (contentType && contentType.includes('application/zip')) {
        // Handle Zip Download
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', 'processed_cams.zip');
        document.body.appendChild(link);
        link.click();
        link.parentNode.removeChild(link);
        alert("Batch processing complete! Zip file downloaded.");
      } else {
        // Handle JSON Response (Blob -> JSON)
        const text = await response.data.text();
        const json = JSON.parse(text);
        if (json.results) {
          setResults(prev => [...json.results, ...prev]);
        }
      }

    } catch (error) {
      console.error("Upload failed", error);
      alert("Error processing files. Make sure the backend is running.");
    } finally {
      setIsUploading(false);
    }
  };

  const onFileSelect = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      processFiles(e.target.files);
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      processFiles(e.dataTransfer.files);
    }
  };

  const downloadFile = (content, filename, type) => {
    let blob;
    if (type === 'xlsx') {
      const byteCharacters = atob(content);
      const byteNumbers = new Array(byteCharacters.length);
      for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
      }
      const byteArray = new Uint8Array(byteNumbers);
      blob = new Blob([byteArray], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
    } else {
      blob = new Blob([content], { type: 'text/csv;charset=utf-8;' });
    }

    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="app-container">
      <header>
        <motion.h1
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          CamExtractor Pro
        </motion.h1>
        <p className="subtitle">Industrial Cam Motion Profile Transformation</p>
      </header>

      <main>
        <div
          className={`upload-zone ${dragActive ? 'active' : ''}`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          onClick={() => document.getElementById('fileInput').click()}
        >
          <input
            id="fileInput"
            type="file"
            multiple
            accept=".xlsx,.xls,.zip"
            onChange={onFileSelect}
            className="hidden"
            style={{ display: 'none' }}
          />

          <AnimatePresence mode="wait">
            {isUploading ? (
              <motion.div
                key="loading"
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 1.1 }}
              >
                <Loader2 className="upload-icon animate-spin" />
                <h2>Processing your cams...</h2>
                <p>Normalizing campoints and generating profiles</p>
              </motion.div>
            ) : (
              <motion.div
                key="idle"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
              >
                <Upload className="upload-icon" />
                <h2>Drop Excel files here</h2>
                <p>Support for batch processing subfolders coming soon</p>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        <div className="results-grid">
          <AnimatePresence>
            {results.map((res, idx) => (
              <motion.div
                key={`${res.filename}-${idx}`}
                className="result-card"
                initial={{ opacity: 0, scale: 0.9, y: 20 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                transition={{ delay: idx * 0.1 }}
              >
                <div className="card-header">
                  <div className="filename-container flex items-center gap-2">
                    <FileSpreadsheet className="text-primary" size={20} />
                    <span className="filename">{res.filename}</span>
                  </div>
                  <span className={`badge ${res.success ? 'badge-success' : 'badge-error'}`}>
                    {res.success ? 'Success' : 'Failed'}
                  </span>
                </div>

                {res.success ? (
                  <>
                    <div className="graph-container">
                      <img
                        src={`data:image/png;base64,${res.graph}`}
                        alt="Motion Profile"
                        className="graph-img"
                      />
                    </div>

                    <div className="flex gap-2 mb-4">
                      <button
                        className="button flex-1 text-sm py-2"
                        onClick={() => downloadFile(res.csv, `${res.filename.split('.')[0]}.csv`, 'csv')}
                      >
                        <Download size={16} className="inline mr-2" /> CSV
                      </button>
                      <button
                        className="button flex-1 text-sm py-2"
                        onClick={() => downloadFile(res.xlsx, `${res.filename.split('.')[0]}.xlsx`, 'xlsx')}
                      >
                        <Download size={16} className="inline mr-2" /> XLSX
                      </button>
                    </div>

                    <div className="ascii-preview">
                      {res.table}
                    </div>
                  </>
                ) : (
                  <div className="error-message p-4 text-red-400">
                    <AlertCircle className="inline mr-2" />
                    {res.error}
                  </div>
                )}
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      </main>
    </div>
  );
}

export default App;
