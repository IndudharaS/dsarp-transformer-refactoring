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
training_features
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

## Stage 2 Training Dataset

Each completed analysis stores one transformer-ready feature per smell in the
`training_features` collection. The feature contains deterministic natural
language in `text` and the rule-classifier strategy in `label`.

```text
GET /api/smells/{runId}
GET /api/training-data/{runId}
GET /api/training-data/{runId}/export
```

Download a Google Colab-compatible CSV containing exactly `text,label`:

```bash
curl -o dsarp-training.csv \
  http://127.0.0.1:8000/api/training-data/YOUR_RUN_ID/export
```

These are pseudo-labels from the Stage 2 rule baseline. Before model
evaluation, combine multiple systems, inspect class balance, and create
stratified train, validation, and test splits.

## Stage 2 Tests

```bash
cd backend
source venv/Scripts/activate
python -m unittest discover -s tests -v
```

Tests cover file types, empty files, required columns, normalization, training
features, rules, classification, ranking, route registration, processed smells,
and JSON/CSV training-data APIs.

## Stage 3 Dataset Preparation CLI

This utility prepares data only; it does not train a transformer. Run commands
from `backend/` with the virtual environment activated.

Create a cleaned, unbalanced export from one MongoDB run:

```bash
python -m app.cli.prepare_dataset \
  --run-id YOUR_RUN_ID \
  --output reports/stage3-original.csv
```

Combine several MongoDB runs:

```bash
python -m app.cli.prepare_dataset \
  --run-id RUN_ID_1 \
  --run-id RUN_ID_2 \
  --run-id RUN_ID_3 \
  --output reports/stage3-combined.csv
```

Create original and downsampled exports:

```bash
python -m app.cli.prepare_dataset \
  --run-id RUN_ID_1 \
  --run-id RUN_ID_2 \
  --output reports/stage3-original.csv \
  --balance downsample \
  --balanced-output reports/stage3-balanced.csv
```

Experimental oversampling to a chosen number of rows per class:

```bash
python -m app.cli.prepare_dataset \
  --run-id RUN_ID_1 \
  --output reports/stage3-original.csv \
  --balance oversample \
  --target-count 100 \
  --balanced-output reports/stage3-oversampled.csv
```

Existing `text,label` CSV files can also be merged:

```bash
python -m app.cli.prepare_dataset \
  --input-csv reports/tika.csv \
  --input-csv reports/karaf.csv \
  --output reports/stage3-combined.csv
```

The utility always writes a `*.quality.json` report beside the original output
unless `--report-output` is provided. The clean original export removes empty
text, empty labels, and duplicate text. Downsampling never invents examples;
oversampling duplicates minority examples and is intended only for experiments.

## Multi-Project Stage 3 Data Collection

This workflow collects data only. It does not start transformer training.
The DSARP backend processes architecture-analysis CSVs; it does not clone Java
repositories or generate those CSVs directly from source code.

### 1. Prepare CSV Inputs

Export the following three files from the same architecture-analysis tool and
version for each project:

```text
smell-characteristics.csv
smell-affects.csv
component-metrics.csv
```

Suggested local layout outside this repository:

```text
/e/datasets/dsarp/
  karaf/
  struts/
  log4j2/
  cassandra/
```

Each project folder must contain all three files. Required columns are listed
in the `Required CSV Columns` section above. Extra columns are allowed.

### 2. Restore Atlas And Start Backend

In MongoDB Atlas, confirm that the cluster is active, the database user has
read/write access, and the current public IP is allowed under Network Access.

From Windows Git Bash:

```bash
cd /e/Masters_Project/dsarp-transformer-refactoring/backend
source venv/Scripts/activate
python -m uvicorn app.main:app --reload
```

In another terminal:

```bash
curl http://127.0.0.1:8000/api/health
```

Continue only when the response contains `"database":true`.

### 3. Upload Each Project

Set reusable values in Git Bash:

```bash
API=http://127.0.0.1:8000
DATA_ROOT=/e/datasets/dsarp
```

Karaf:

```bash
curl -X POST "$API/api/upload" \
  -F "projectName=Apache Karaf Stage 3 Dataset" \
  -F "systemName=Karaf" \
  -F "version=5f5677d7395170208907f2f1655ae9fd9b3bff9e" \
  -F "smellCharacteristics=@$DATA_ROOT/karaf/smell-characteristics.csv;type=text/csv" \
  -F "smellAffects=@$DATA_ROOT/karaf/smell-affects.csv;type=text/csv" \
  -F "componentMetrics=@$DATA_ROOT/karaf/component-metrics.csv;type=text/csv"
```

Struts:

```bash
curl -X POST "$API/api/upload" \
  -F "projectName=Apache Struts Stage 3 Dataset" \
  -F "systemName=Struts" \
  -F "version=d59aea5f5d6099ba09e894cb8810e00a37e112b1" \
  -F "smellCharacteristics=@$DATA_ROOT/struts/smell-characteristics.csv;type=text/csv" \
  -F "smellAffects=@$DATA_ROOT/struts/smell-affects.csv;type=text/csv" \
  -F "componentMetrics=@$DATA_ROOT/struts/component-metrics.csv;type=text/csv"
```

Log4j2 uses the backend system name `Logging-Log4j2`:

```bash
curl -X POST "$API/api/upload" \
  -F "projectName=Apache Log4j2 Stage 3 Dataset" \
  -F "systemName=Logging-Log4j2" \
  -F "version=4f474b32751f4ccad67424ca585612584440cd63" \
  -F "smellCharacteristics=@$DATA_ROOT/log4j2/smell-characteristics.csv;type=text/csv" \
  -F "smellAffects=@$DATA_ROOT/log4j2/smell-affects.csv;type=text/csv" \
  -F "componentMetrics=@$DATA_ROOT/log4j2/component-metrics.csv;type=text/csv"
```

Cassandra:

```bash
curl -X POST "$API/api/upload" \
  -F "projectName=Apache Cassandra Stage 3 Dataset" \
  -F "systemName=Cassandra" \
  -F "version=0269fd5665751e8a6d8eab852e0f66c142b10ee6" \
  -F "smellCharacteristics=@$DATA_ROOT/cassandra/smell-characteristics.csv;type=text/csv" \
  -F "smellAffects=@$DATA_ROOT/cassandra/smell-affects.csv;type=text/csv" \
  -F "componentMetrics=@$DATA_ROOT/cassandra/component-metrics.csv;type=text/csv"
```

Copy each returned `runId`. Create the working manifest from the tracked example:

```bash
cp reports/run_ids.example.json reports/run_ids.json
```

Fill `reports/run_ids.json`:

```json
{
  "Tika": "TIKA_RUN_ID",
  "Karaf": "KARAF_RUN_ID",
  "Struts": "STRUTS_RUN_ID",
  "Logging-Log4j2": "LOG4J2_RUN_ID",
  "Cassandra": "CASSANDRA_RUN_ID"
}
```

The working `run_ids.json` is ignored by Git; the blank example remains tracked.

### 4. Run Stage 2 Analysis

Set the IDs copied from the upload responses:

```bash
TIKA_RUN_ID=replace_me
KARAF_RUN_ID=replace_me
STRUTS_RUN_ID=replace_me
LOG4J2_RUN_ID=replace_me
CASSANDRA_RUN_ID=replace_me
```

Analyze every run:

```bash
curl -X POST "$API/api/analyze/$TIKA_RUN_ID"
curl -X POST "$API/api/analyze/$KARAF_RUN_ID"
curl -X POST "$API/api/analyze/$STRUTS_RUN_ID"
curl -X POST "$API/api/analyze/$LOG4J2_RUN_ID"
curl -X POST "$API/api/analyze/$CASSANDRA_RUN_ID"
```

Every response must have `"status":"completed"` and non-zero processed counts.

### 5. Verify Stage 2 Results

The same commands work for any run ID:

```bash
curl "$API/api/smells/$KARAF_RUN_ID?limit=1000"
curl "$API/api/recommendations/$KARAF_RUN_ID"
curl "$API/api/stats/$KARAF_RUN_ID"
curl "$API/api/training-data/$KARAF_RUN_ID"
```

### 6. Export Per-Project Training CSVs

```bash
curl -L -o reports/tika-training.csv "$API/api/training-data/$TIKA_RUN_ID/export"
curl -L -o reports/karaf-training.csv "$API/api/training-data/$KARAF_RUN_ID/export"
curl -L -o reports/struts-training.csv "$API/api/training-data/$STRUTS_RUN_ID/export"
curl -L -o reports/log4j2-training.csv "$API/api/training-data/$LOG4J2_RUN_ID/export"
curl -L -o reports/cassandra-training.csv "$API/api/training-data/$CASSANDRA_RUN_ID/export"
```

Each file must have exactly this header:

```text
text,label
```

### 7. Combine Runs And Check Quality

```bash
python -m app.cli.prepare_dataset \
  --run-ids-file reports/run_ids.json \
  --output reports/stage3-original.csv \
  --report-output reports/stage3-original.report.json
```

This writes:

```text
reports/stage3-original.csv
reports/stage3-original.report.json
```

The original export is cleaned and deduplicated but remains unbalanced.

### 8. Create Balanced Export When Suitable

Downsample only after every required label has at least 30 distinct examples.
Otherwise downsampling may leave too little data for training.

```bash
python -m app.cli.prepare_dataset \
  --run-ids-file reports/run_ids.json \
  --output reports/stage3-original.csv \
  --report-output reports/stage3-original.report.json \
  --balance downsample \
  --balanced-output reports/stage3-balanced.csv
```

Experimental oversampling is available, but duplicated examples do not replace
collecting real minority-class examples.

### Google Colab Readiness Checklist

- [ ] Atlas health returns `"database":true`.
- [ ] All five projects have valid runIds in `reports/run_ids.json`.
- [ ] Every analysis status is `completed`.
- [ ] Every project produces non-empty training data.
- [ ] `reports/stage3-original.csv` exists with exactly `text,label` columns.
- [ ] Empty text count is zero.
- [ ] Empty label count is zero.
- [ ] Duplicate text count is zero.
- [ ] Conflicting-label duplicate count is zero.
- [ ] Every label has at least 30 distinct examples.
- [ ] Largest-to-smallest class ratio is at most 3:1.
- [ ] `reports/stage3-original.report.json` has been reviewed.
- [ ] `reports/stage3-balanced.csv` is created only when it retains enough data.
- [ ] Repository-aware train/validation/test splitting is planned to avoid leakage.

Do not start transformer training until every mandatory quality item above is
satisfied. Oversampling alone does not make a dataset research-ready.
