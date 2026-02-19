# CamExtractor Frontend

A modern React application built with Vite, serving as the user interface for CamExtractor.

## Features
- **Drag & Drop Interface**: Easily upload Excel files or Zip archives.
- **Interactive Visualization**: View motion profile graphs directly in the browser.
- **Data Table**: Preview calculated cam points.
- **Export Options**: Toggle CSV/XLSX export.
- **Batch Processing**: Upload a Zip file to process multiple cams at once.

## Development

### Prerequisites
- Node.js 18+
- npm

### Running Locally
```bash
cd frontend
npm install
npm run dev
```
The frontend runs on `http://localhost:5173` and proxies API requests to the Flask backend on port 5000.

### Build
```bash
npm run build
```
Builds the app to `dist/`, which is then served by Flask in production/docker.
