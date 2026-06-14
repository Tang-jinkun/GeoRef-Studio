# GeoRef Studio

GeoRef Studio is an online georeferencing tool for GIS imagery workflows.

V1.0 focuses on the main workflow:

```text
upload image -> create control points -> affine georeference -> preview -> export GeoTIFF
```

## Repository Layout

```text
backend/   FastAPI service and GIS processing modules
frontend/  Vue 3 + TypeScript application
docs/      Product and development documentation
storage/   Local development file storage
```

## Local Development

Copy environment defaults:

```bash
cp .env.example .env
```

Start infrastructure and services:

```bash
docker compose up --build
```

Backend health check:

```bash
curl http://localhost:8000/api/health
```

Frontend:

```text
http://localhost:5173
```

## Manual Backend Setup

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Manual Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

