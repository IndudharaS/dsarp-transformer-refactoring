# DSARP – Transformer-Based Software Architecture Refactoring Recommendation System

DSARP is a web-based system for generating ranked software architecture refactoring recommendations from detected architecture smells using a transformer classifier, prompt optimization, and HPC-hosted Large Language Models.

---

## Repository

```text
dsarp-transformer-refactoring
```

---

## Project Overview

The system analyzes architecture smell datasets from large software systems and produces ranked architecture-level refactoring recommendations.

The workflow combines:

- Architecture smell processing
- Transformer-based refactoring strategy classification
- Prompt optimization
- HPC-hosted LLM recommendation generation
- Recommendation ranking
- Interactive dashboard visualization
- Report generation

---

## Supported Software Systems

| System | Version | Files |
|----------|----------|----------:|
| Tika | 697d7c047daf1f661a4ed067bbc8f9c58bb6faa2 | 1813 |
| Karaf | 5f5677d7395170208907f2f1655ae9fd9b3bff9e | 16892 |
| Struts | d59aea5f5d6099ba09e894cb8810e00a37e112b1 | 2462 |
| Logging-Log4j2 | 4f474b32751f4ccad67424ca585612584440cd63 | 3283 |
| Cassandra | 0269fd5665751e8a6d8eab852e0f66c142b10ee6 | 4675 |

---

## Supported Architecture Smells

- God Component (`godComponent`)
- Unstable Dependency (`unstableDep`)
- Cyclic Dependency (`cyclicDep`)

---

## Technology Stack

### Frontend

- Next.js
- TypeScript
- Tailwind CSS
- Axios
- TanStack Table
- Recharts

### Backend

- FastAPI
- Python
- Pandas
- NumPy
- Pydantic
- Uvicorn

### Database

- MongoDB

### HPC / Machine Learning

- PyTorch
- Hugging Face Transformers
- vLLM
- PEFT
- TRL
- BitsAndBytes
- CUDA
- Slurm

### Models

#### Transformer Classifier

```text
microsoft/codebert-base
```

#### Recommendation Generator

```text
nvidia/Llama-3.1-Nemotron-70B-Instruct-HF
```

#### Optional Fine-Tuned Model

```text
Qwen/Qwen2.5-Coder-7B-Instruct
```

---

## System Architecture

```text
User
 │
 ▼
Next.js Frontend
 │
 ▼
FastAPI Backend
 │
 ▼
MongoDB
 │
 ▼
CSV Validation
 │
 ▼
Feature Builder
 │
 ▼
Transformer Classifier
 │
 ▼
Prompt Optimizer
 │
 ▼
Nemotron 70B (HPC)
 │
 ▼
Output Validator
 │
 ▼
Recommendation Ranking
 │
 ▼
MongoDB
 │
 ▼
Dashboard + Reports
```

---

## Input Files

Users upload three CSV files:

```text
smell-characteristics.csv
smell-affects.csv
component-metrics.csv
```

### smell-characteristics.csv

Required columns:

```text
smellType
Severity
Size
Strength
InstabilityGap
AffectedElements
NumberOfEdges
```

### smell-affects.csv

Required columns:

```text
from
to
fromId
toId
```

### component-metrics.csv

Required columns:

```text
name
FanIn
FanOut
LinesOfCode
InstabilityMetric
AbstractnessMetric
PageRank
```

---

## Project Structure

```text
dsarp/
├── frontend/
│   ├── app/
│   ├── components/
│   └── lib/
│
├── backend/
│   ├── app/
│   │   ├── routes/
│   │   ├── db/
│   │   ├── models/
│   │   └── pipeline/
│   ├── uploads/
│   ├── reports/
│   └── requirements.txt
│
├── ml/
│   ├── scripts/
│   ├── slurm/
│   ├── models/
│   └── data/
│
└── README.md
```

---

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

---

## Data Flow

```text
CSV Upload
    │
    ▼
Upload Storage
    │
    ▼
MongoDB Metadata
    │
    ▼
CSV Validation
    │
    ▼
Feature Builder
    │
    ▼
Structured Smell Objects
    │
    ▼
Transformer Classifier
    │
    ▼
Refactoring Strategy Prediction
    │
    ▼
Prompt Version Selection
    │
    ▼
Nemotron 70B Generation
    │
    ▼
Output Validation
    │
    ▼
Recommendation Ranking
    │
    ▼
MongoDB Storage
    │
    ▼
Dashboard + Reports
```

---

## Transformer Classification

Input:

```text
SmellType=cyclicDep
Severity=4.2
Size=3
Strength=0.8
InstabilityGap=0.2
NumberOfEdges=5
FanIn=12
FanOut=18
LOC=1300
PageRank=0.04
```

Output:

```json
{
  "predictedStrategy": "ExtractSharedComponent",
  "classifierConfidence": 0.92
}
```

### Strategy Classes

```text
ExtractComponent
SplitResponsibilities
DependencyInversion
IntroduceInterface
ExtractSharedComponent
FacadePattern
MediatorPattern
LayerReorganization
```

---

## Prompt Optimization

Prompt versions:

```text
v1
v2
v3
v4
v5
```

Evaluation process:

```text
v1 → Score
v2 → Score
v3 → Score
v4 → Score
v5 → Score
```

Early stopping:

```text
If currentScore < previousScore:
    Stop and select previous prompt

If improvement < 0.02:
    Stop and select current prompt

Else:
    Continue
```

---

## Recommendation Ranking

### Smell Priority Score

```text
0.35 × Severity
+ 0.20 × Size
+ 0.20 × Strength
+ 0.15 × InstabilityGap
+ 0.10 × NumberOfEdges
```

### Recommendation Quality Score

```text
0.25 × JSON Validity
+ 0.20 × Recommendation Confidence
+ 0.20 × Strategy Match
+ 0.15 × Actionability
+ 0.10 × Testing Advice Quality
+ 0.10 × Expected Impact Quality
```

### Final Ranking Score

```text
0.50 × Smell Priority Score
+ 0.30 × Recommendation Quality Score
+ 0.20 × Classifier Confidence
```

### Rank Levels

```text
Critical  : 0.80 - 1.00
High      : 0.60 - 0.79
Medium    : 0.40 - 0.59
Low       : 0.00 - 0.39
```

---

## Backend Setup

```bash
cd backend

python -m venv venv

source venv/bin/activate

pip install -r requirements.txt

uvicorn app.main:app --reload
```

Backend URL:

```text
http://localhost:8000
```

---

## Frontend Setup

```bash
cd frontend

npm install

npm run dev
```

Frontend URL:

```text
http://localhost:3000
```

---

## Environment Variables

### backend/.env

```env
MONGO_URI=mongodb://localhost:27017
MONGO_DB=dsarp

UPLOAD_DIR=uploads
REPORT_DIR=reports

HPC_LLM_BASE_URL=http://localhost:9000/v1
HPC_LLM_MODEL=nvidia/Llama-3.1-Nemotron-70B-Instruct-HF
```

### frontend/.env.local

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## HPC Setup

Start Nemotron 70B:

```bash
sbatch ml/slurm/run_vllm_server.sh
```

Classifier training:

```bash
sbatch ml/slurm/train_classifier.sh
```

QLoRA fine-tuning:

```bash
sbatch ml/slurm/train_lora.sh
```

---

## API Endpoints

```text
GET  /api/health

POST /api/upload

POST /api/analyze/{runId}

GET  /api/recommendations/{runId}

GET  /api/recommendations/{runId}/{smellId}

GET  /api/stats/{runId}

GET  /api/prompts

GET  /api/prompt-evaluations/{runId}

GET  /api/reports/{runId}/download?format=csv

GET  /api/reports/{runId}/download?format=excel

GET  /api/reports/{runId}/download?format=html
```

---

## Team Responsibilities

### Team Member 1

- HPC
- vLLM
- Transformer Classifier
- Fine-Tuning

### Team Member 2

- FastAPI Backend
- MongoDB
- Data Processing
- Ranking Engine

### Team Member 3

- Next.js Frontend
- Dashboard
- Reports
- Documentation

---

## Limitations

- Only three smell types are currently supported.
- Refactoring implementation is recommendation-only.
- Weak labels are used initially for classifier training.
- LLM output may require fallback validation.
- Fine-tuned generator is optional.

---

## Future Work

- Automatic source code transformation
- Additional architecture smell support
- Human expert evaluation
- CI/CD integration
- Build and test execution
- Repository mining
- Architecture evolution tracking

---

## License

Academic Master's Project.
