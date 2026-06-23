# DSARP - Transformer-Based Software Architecture Refactoring

Stage 2 processes uploaded DSARP CSV files without an HPC LLM. It builds smell
objects, creates rule-based recommendations and classifier predictions, ranks
the recommendations, and exposes statistics APIs.

## Project Structure

```text
frontend/
backend/
  app/
    main.py
    config.py
    db/
      mongo.py
    routes/
      upload.py
      analyze.py
      recommendations.py
      stats.py
      prompts.py
      reports.py
    models/
      schemas.py
    pipeline/
      validator.py
  uploads/
  reports/
  requirements.txt
  .env.example
  .env
ml/
README.md
```

## Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

On Windows PowerShell:

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Backend URL:

```text
http://localhost:8000
```

## Frontend Setup

In a second PowerShell window:

```powershell
cd frontend
npm install
npm run dev
```

Open:

```text
http://localhost:3000
```

The upload page creates new runs. The temporary database test page at
`http://localhost:3000/database` shows recent `analysis_runs` records and
verifies that each one has matching metadata in `uploaded_files`.

Stage 2 frontend routes:

```text
/runs
/runs/{runId}
/runs/{runId}/recommendations
/runs/{runId}/recommendations/{smellId}
/runs/{runId}/stats
```

## Online MongoDB Environment

The backend is configured for an online MongoDB connection. Edit `backend/.env` and replace `USERNAME`, `PASSWORD`, and `YOUR_CLUSTER` with your MongoDB Atlas connection details.

```env
MONGO_URI=mongodb+srv://USERNAME:PASSWORD@YOUR_CLUSTER.mongodb.net/?retryWrites=true&w=majority
MONGO_DB=dsarp
UPLOAD_DIR=uploads
REPORT_DIR=reports
HPC_LLM_BASE_URL=http://localhost:9000/v1
HPC_LLM_MODEL=nvidia/Llama-3.1-Nemotron-70B-Instruct-HF
```

For MongoDB Atlas, make sure your current IP address is allowed under Network Access and that the database user has read/write access to the `dsarp` database.

After startup, verify the connection:

```text
http://localhost:8000/api/health
```

Expected response when MongoDB is reachable:

```json
{
  "status": "ok",
  "database": true
}
```

## Stage 1 API

```text
GET  /api/health
POST /api/upload
GET  /api/runs
GET  /api/runs/{runId}
POST /api/analyze/{runId}
GET  /api/recommendations/{runId}
GET  /api/recommendations/{runId}/{smellId}
GET  /api/stats/{runId}
```

`POST /api/analyze/{runId}` can be run again safely. Existing smells,
classifier predictions, and recommendations for that run are replaced before
the new analysis results are inserted.

`POST /api/upload` accepts multipart form data:

```text
projectName
systemName
version
smellCharacteristics
smellAffects
componentMetrics
```

Uploaded files are stored under `backend/uploads/{runId}/` with fixed names:

```text
smell-characteristics.csv
smell-affects.csv
component-metrics.csv
```

## Supported Software Systems

| System | Version | Files |
| --- | --- | ---: |
| Tika | 697d7c047daf1f661a4ed067bbc8f9c58bb6faa2 | 1813 |
| Karaf | 5f5677d7395170208907f2f1655ae9fd9b3bff9e | 16892 |
| Struts | d59aea5f5d6099ba09e894cb8810e00a37e112b1 | 2462 |
| Logging-Log4j2 | 4f474b32751f4ccad67424ca585612584440cd63 | 3283 |
| Cassandra | 0269fd5665751e8a6d8eab852e0f66c142b10ee6 | 4675 |

The backend seeds these systems into the `software_systems` collection on startup when MongoDB is available.

## MongoDB Collections

```text
software_systems
analysis_runs
uploaded_files
smells
classifier_predictions
prompt_versions
prompt_evaluations
model_outputs
recommendations
reports
```

## Required CSV Columns

`smell-characteristics.csv`

```text
smellType, Severity, Size, Strength, InstabilityGap, AffectedElements, NumberOfEdges
```

`smell-affects.csv`

```text
from, to, fromId, toId
```

`component-metrics.csv`

```text
name, FanIn, FanOut, LinesOfCode, InstabilityMetric, AbstractnessMetric, PageRank
```
