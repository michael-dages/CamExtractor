import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Upload, FileSpreadsheet, Download, CheckCircle, AlertCircle, Loader2, Crosshair } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine, ResponsiveContainer
} from 'recharts';

const API_BASE = '';

// prefix -> axis info, mirror of cam_xml.AXIS_MAPPING on the backend.
// The prefix (not just the axis name) determines the output filename and target
// CAMS folder, so the dropdown selects by prefix. AXVACUUM has one prefix per group.
const AXIS_MAPPING = {
  horz_: { axisName: 'AXHORIZ', axisNumber: 4 },
  vert_: { axisName: 'AXVERTICAL', axisNumber: 3 },
  rec_: { axisName: 'AXRECIP', axisNumber: 14 },
  gat3_: { axisName: 'AXGATE3', axisNumber: 10 },
  late_: { axisName: 'AXLATEGATE', axisNumber: 15 },
  pri_: { axisName: 'AXPRISLIDE', axisNumber: 13 },
  rot1_: { axisName: 'AXROTODEX1', axisNumber: 8 },
  rot2_: { axisName: 'AXROTODEX2', axisNumber: 7 },
  vac_: { axisName: 'AXVACUUM', axisNumber: 12, group: 0 },
  vac1_: { axisName: 'AXVACUUM', axisNumber: 12, group: 1 },
  vac2_: { axisName: 'AXVACUUM', axisNumber: 12, group: 2 },
  vac3_: { axisName: 'AXVACUUM', axisNumber: 12, group: 3 },
  vac4_: { axisName: 'AXVACUUM', axisNumber: 12, group: 4 },
  vac5_: { axisName: 'AXVACUUM', axisNumber: 12, group: 5 },
  vac6_: { axisName: 'AXVACUUM', axisNumber: 12, group: 6 },
};
const REJECT_AXES = new Set(['AXVACUUM', 'AXRECIP', 'AXGATE3']);
const PREFIX_OPTIONS = Object.keys(AXIS_MAPPING);
const INDEX_OPTIONS = Array.from({ length: 25 }, (_, i) => i + 1); // cam-selection slots 1-25

function prefixLabel(prefix) {
  const a = AXIS_MAPPING[prefix];
  const grp = a.group != null ? ` grp ${a.group}` : '';
  return `${prefix} - ${a.axisName}${grp}`;
}

// Build the descriptive part of the HMIText: strip a known extension / "<prefix>_<index>-"
// lead-in and any existing "NN) " so it can be re-prefixed with the selected index.
function deriveBaseDescription(res) {
  const axisMeta = res.axis || {};
  let raw = axisMeta.hmitext;
  if (!raw) {
    raw = res.filename.replace(/\.[^.]+$/, '');
    const m = raw.match(/^[a-z]+\d*_\d+-(.*)$/i);
    if (m) raw = m[1];
  }
  return raw.replace(/^\s*\d+\)\s*/, '').trim();
}

function downloadBlob(blob, filename) {
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', filename);
  document.body.appendChild(link);
  link.click();
  link.parentNode.removeChild(link);
  window.URL.revokeObjectURL(url);
}

function downloadTextFile(content, filename, mime) {
  downloadBlob(new Blob([content], { type: mime }), filename);
}

function ResultCard({ res, idx, exportXML }) {
  const axisMeta = res.axis || {};
  const baseDescription = deriveBaseDescription(res);
  const initialPrefix = axisMeta.prefix && AXIS_MAPPING[axisMeta.prefix] ? axisMeta.prefix : '';
  const initialIndex = axisMeta.index ? String(axisMeta.index) : '';

  const [prefix, setPrefix] = useState(initialPrefix);
  const [index, setIndex] = useState(initialIndex);
  const [hmitext, setHmitext] = useState(initialIndex ? `${initialIndex}) ${baseDescription}` : '');
  const [hmiTouched, setHmiTouched] = useState(false);
  const [rejectMaster, setRejectMaster] = useState(null);
  const [xmlBusy, setXmlBusy] = useState(false);

  const axisInfo = prefix ? AXIS_MAPPING[prefix] : null;
  const axisName = axisInfo ? axisInfo.axisName : '';
  const isCapping = !!(axisName && REJECT_AXES.has(axisName));

  // Auto-populate HMIText as "<index>) <name of file>" until the user edits it manually.
  useEffect(() => {
    if (!hmiTouched && index) {
      setHmitext(`${index}) ${baseDescription}`);
    }
  }, [index, hmiTouched, baseDescription]);

  const chartData = res.points
    ? res.points.master.map((m, i) => ({ master: m, slave: res.points.slave[i] }))
    : [];

  const rejectPosition =
    rejectMaster != null ? Number((rejectMaster / 360).toFixed(6)) : null;

  // Download is allowed only once every required field is satisfied.
  const missing = [];
  if (!prefix) missing.push('axis');
  if (!index) missing.push('index');
  if (hmitext.trim() === '') missing.push('HMIText');
  if (isCapping && rejectMaster == null) missing.push('reject point');
  const canDownload = missing.length === 0 && !!res.points && !xmlBusy;

  const handleChartClick = (state) => {
    if (!isCapping) return;
    if (state && state.activeLabel != null) {
      setRejectMaster(Number(state.activeLabel));
    }
  };

  const downloadXLSX = (content, filename) => {
    const byteCharacters = atob(content);
    const byteNumbers = new Array(byteCharacters.length);
    for (let i = 0; i < byteCharacters.length; i++) {
      byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    const byteArray = new Uint8Array(byteNumbers);
    downloadBlob(
      new Blob([byteArray], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' }),
      filename
    );
  };

  const handleDownloadXML = async () => {
    if (!res.points) {
      alert('No point data available for this file.');
      return;
    }
    setXmlBusy(true);
    try {
      const body = {
        prefix: prefix,
        index: index,
        hmitext: hmitext,
        axis_name: axisName || null,
        axis_number: axisInfo ? axisInfo.axisNumber : null,
        master: res.points.master,
        slave: res.points.slave,
        reject_position: isCapping ? rejectPosition : null,
        source_filename: res.filename,
      };
      const response = await axios.post(`${API_BASE}/export_xml`, body, {
        responseType: 'blob',
      });
      // Folder nomenclature: <prefix><index>.xml (e.g. horz_10.xml).
      downloadBlob(response.data, `${prefix}${index}.xml`);
    } catch (error) {
      // Error responses come back as a blob; surface the message if we can read it.
      let msg = 'Failed to generate XML.';
      try {
        const text = await error.response?.data?.text?.();
        if (text) msg = JSON.parse(text).error || msg;
      } catch (_) { /* ignore */ }
      alert(msg);
    } finally {
      setXmlBusy(false);
    }
  };

  return (
    <motion.div
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
          {/* Interactive chart (used for XML reject-point selection) or static graph */}
          {exportXML && chartData.length > 0 ? (
            <div className="graph-container" style={{ width: '100%', height: 240 }}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart
                  data={chartData}
                  onClick={handleChartClick}
                  style={{ cursor: isCapping ? 'crosshair' : 'default' }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                  <XAxis dataKey="master" type="number" domain={[0, 360]} tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Line type="monotone" dataKey="slave" dot={false} stroke="#22d3ee" strokeWidth={2} isAnimationActive={false} />
                  {rejectMaster != null && (
                    <ReferenceLine x={rejectMaster} stroke="#f43f5e" strokeWidth={2} label={{ value: 'reject', fill: '#f43f5e', fontSize: 11 }} />
                  )}
                </LineChart>
              </ResponsiveContainer>
            </div>
          ) : (
            res.graph && (
              <div className="graph-container">
                <img src={`data:image/png;base64,${res.graph}`} alt="Motion Profile" className="graph-img" />
              </div>
            )
          )}

          {/* XML metadata + export panel */}
          {exportXML && (
            <div className="xml-panel" style={{ border: '1px solid #333', borderRadius: 8, padding: 12, marginBottom: 12 }}>
              <div className="flex gap-2 mb-2" style={{ flexWrap: 'wrap' }}>
                <label className="flex flex-col text-xs" style={{ flex: 1, minWidth: 160 }}>
                  Axis (prefix)
                  <select value={prefix} onChange={(e) => { setPrefix(e.target.value); setRejectMaster(null); }} className="checkbox" style={{ padding: 4 }}>
                    <option value="">-- select --</option>
                    {PREFIX_OPTIONS.map((p) => (
                      <option key={p} value={p}>{prefixLabel(p)}</option>
                    ))}
                  </select>
                </label>
                <label className="flex flex-col text-xs" style={{ width: 80 }}>
                  Index
                  <select value={index} onChange={(e) => setIndex(e.target.value)} className="checkbox" style={{ padding: 4 }}>
                    <option value="">--</option>
                    {INDEX_OPTIONS.map((n) => (
                      <option key={n} value={String(n)}>{n}</option>
                    ))}
                  </select>
                </label>
                <label className="flex flex-col text-xs" style={{ flex: 2, minWidth: 160 }}>
                  HMIText
                  <input type="text" value={hmitext} onChange={(e) => { setHmiTouched(true); setHmitext(e.target.value); }} style={{ padding: 4 }} />
                </label>
              </div>

              {isCapping && (
                <div className="text-xs mb-2 flex items-center gap-2" style={{ color: '#f43f5e' }}>
                  <Crosshair size={14} />
                  {rejectMaster != null
                    ? <span>Reject at master {rejectMaster} {'->'} RejectPosition {rejectPosition}</span>
                    : <span>Click a point on the chart to set the reject position</span>}
                </div>
              )}

              {!canDownload && !xmlBusy && missing.length > 0 && (
                <div className="text-xs mb-2" style={{ color: '#94a3b8' }}>
                  Set {missing.join(', ')} to enable XML download
                  {prefix && index && <span> &middot; saves as <code>{prefix}{index}.xml</code></span>}
                </div>
              )}

              <button
                className="button w-full text-sm py-2"
                onClick={handleDownloadXML}
                disabled={!canDownload}
                style={!canDownload ? { opacity: 0.5, cursor: 'not-allowed' } : undefined}
              >
                {xmlBusy ? <Loader2 size={16} className="inline mr-2 animate-spin" /> : <Download size={16} className="inline mr-2" />}
                {canDownload ? `Download ${prefix}${index}.xml` : 'Download XML'}
              </button>
            </div>
          )}

          <div className="flex gap-2 mb-4">
            {res.csv != null && (
              <button
                className="button flex-1 text-sm py-2"
                onClick={() => downloadTextFile(res.csv, `${res.filename.split('.')[0]}.csv`, 'text/csv;charset=utf-8;')}
              >
                <Download size={16} className="inline mr-2" /> CSV
              </button>
            )}
            {res.xlsx != null && (
              <button
                className="button flex-1 text-sm py-2"
                onClick={() => downloadXLSX(res.xlsx, `${res.filename.split('.')[0]}.xlsx`)}
              >
                <Download size={16} className="inline mr-2" /> XLSX
              </button>
            )}
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
  );
}

function App() {
  const [isUploading, setIsUploading] = useState(false);
  const [results, setResults] = useState([]);
  const [dragActive, setDragActive] = useState(false);
  const [exportCSV, setExportCSV] = useState(true);
  const [exportXLSX, setExportXLSX] = useState(true);
  const [exportXML, setExportXML] = useState(false);

  const processFiles = async (files) => {
    setIsUploading(true);
    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
      formData.append('files', files[i]);
    }

    // Append export flags
    formData.append('export_csv', exportCSV);
    formData.append('export_excel', exportXLSX);
    formData.append('export_xml', exportXML);

    try {
      // Use 'blob' to handle binary zip or json
      const response = await axios.post(`${API_BASE}/process`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        responseType: 'blob'
      });

      const contentType = response.headers['content-type'];

      if (contentType && contentType.includes('application/zip')) {
        // Handle Zip Download
        downloadBlob(new Blob([response.data]), 'processed_cams.zip');
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
        {/* Export Options */}
        <div className="export-options flex justify-center gap-6 mb-4">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={exportCSV}
              onChange={(e) => setExportCSV(e.target.checked)}
              className="checkbox"
            />
            <span>Export CSV</span>
          </label>
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={exportXLSX}
              onChange={(e) => setExportXLSX(e.target.checked)}
              className="checkbox"
            />
            <span>Export XLSX</span>
          </label>
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={exportXML}
              onChange={(e) => setExportXML(e.target.checked)}
              className="checkbox"
            />
            <span>Export XML</span>
          </label>
        </div>

        {exportXML && (
          <p className="subtitle" style={{ fontSize: 12, marginTop: -8, marginBottom: 12 }}>
            XML uses the file name (&lt;prefix&gt;_&lt;index&gt;-&lt;HMIText&gt;) for axis metadata; edit it per result below.
            In zip batches the reject position is omitted (no chart to click).
          </p>
        )}

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
                <h2>Drop Excel files or Zip archives here</h2>
                <p>Drag and drop multiple files or a .zip archive for batch processing</p>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        <div className="results-grid">
          <AnimatePresence>
            {results.map((res, idx) => (
              <ResultCard
                key={`${res.filename}-${idx}`}
                res={res}
                idx={idx}
                exportXML={exportXML}
              />
            ))}
          </AnimatePresence>
        </div>
      </main>
    </div>
  );
}

export default App;
