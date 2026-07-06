# DSARP implementation audit

## Stage 1 - complete

- FastAPI application, CORS, health endpoint, and separated routes
- MongoDB Atlas-compatible configuration and collection initialization
- Multipart CSV upload, fixed stored names, run metadata, and UTC timestamps
- Next.js upload and database-record verification views

## Stage 2 - complete

- CSV loading and required-column validation
- Smell normalization, dependency matching, and component metric matching
- Rule recommendation and rule-classifier fallback
- Per-run ranking and duplicate-safe MongoDB persistence
- Recommendation, smell, statistics, and training-data APIs
- Dataset quality, balancing, multi-run export, and backend tests

## Stage 3 - classifier workflow ready; trained artifact pending

- Existing Colab notebook upgraded to `microsoft/codebert-base`
- Combined `text,label` dataset utility added
- Friend's RefactoringMiner output retained and converted as weak labels
- Empty/duplicate/imbalance checks and provenance report added
- FastAPI transformer adapter added with deterministic rule fallback
- Colab model install path documented

The final trained model is not stored in Git. Run the notebook on a Colab GPU,
then extract its downloaded artifact to
`backend/app/ml/saved_transformer_classifier/` and rerun an analysis.

## Important remaining work from the implementation specification

- Prompt versions and prompt evaluation endpoints are placeholders.
- Nemotron/vLLM generation and prompt optimization require an available model
  endpoint; recommendations currently remain deterministic rule outputs.
- Report downloads currently return HTTP 501.
- Slurm deployment scripts and Qwen QLoRA training are not implemented.

These items must not be described as complete merely because the classifier
notebook runs. They belong to the later generation, reporting, and HPC stages.

## Friend dataset assessment

The mined Apache dataset contains useful repository, commit, metric-delta, and
RefactoringMiner evidence. Its labels are mostly code-level operations and are
not the same ontology as DSARP's eight architecture strategy labels. The
converter therefore uses an explicit architecture-smell mapping and identifies
the records as `apache-mined-weak-label` in the report. Human review or stronger
labels are still recommended before final evaluation.
