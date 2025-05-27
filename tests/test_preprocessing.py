# End-to-End Resume Parser and Skill Extractor with MLOps Pipeline

## 🌟 Project Overview

This project demonstrates a comprehensive MLOps pipeline for parsing PDF resumes, extracting relevant skills and entities, and making this functionality accessible via an API and a user-friendly web interface. It showcases skills in Python, AWS AI services, containerization, orchestration, experiment tracking, and UI deployment.

The primary goal is to take a PDF resume, use AWS Textract for OCR and text extraction, apply rule-based methods and AWS Comprehend for entity/skill identification, and track the entire process using MLflow. The extracted information is served via a Dockerized Flask API, orchestrated for batch processing by Apache Airflow, and can be run locally using Kubernetes (Minikube). An interactive Gradio UI allows for easy resume uploads and result visualization, deployable to Hugging Face Spaces.

## ✨ Features

* **PDF Resume Parsing:** Extracts text content from PDF files using AWS Textract.
* **Skill & Entity Extraction:**
    * Rule-based keyword matching for a predefined list of skills.
    * Named Entity Recognition using AWS Comprehend.
    * Combined and deduplicated results from both methods.
* **Experiment Tracking:** Uses MLflow to log parameters, metrics, and artifacts (extracted text, skills lists) for each processed resume, with artifacts stored in AWS S3.
* **Dockerized Flask API:** A robust API built with Flask and containerized with Docker to serve the resume parsing and skill extraction logic.
* **Local Orchestration (Airflow):** An Apache Airflow DAG to simulate batch processing of resumes from an S3 "intake" folder, demonstrating workflow automation.
* **Local Container Orchestration (Kubernetes):**
    * Deployment of the Flask API to a local Minikube Kubernetes cluster.
    * Deployment of an MLflow server to Minikube, configured with an S3 artifact store.
    * Demonstrates multi-service interaction within Kubernetes.
* **Cloud API Deployment Concept (AWS App Runner):** Previously explored deploying the Flask API to AWS App Runner (steps available in project history, service paused/deleted to manage costs).
* **Interactive Web UI:** A user-friendly interface built with Gradio for easy PDF uploads and viewing of extracted results.
* **UI Deployment (Hugging Face Spaces):** The Gradio UI is deployable to Hugging Face Spaces (configured to call a local API via tunneling for development, or a publicly deployed API for public demos).

## 🛠️ Tech Stack & Skills Demonstrated

* **Programming:** Python
* **Cloud (AWS):**
    * S3 (Simple Storage Service): For storing raw resumes, MLflow artifacts.
    * Textract: For OCR and text extraction from PDFs.
    * Comprehend: For Named Entity Recognition.
    * IAM: For managing permissions.
    * ECR (Elastic Container Registry): For storing Docker images.
    * App Runner (Conceptual understanding/previous implementation): For deploying containerized web applications.
* **Containerization & Orchestration:**
    * Docker: For containerizing the Flask API and MLflow server.
    * Kubernetes (K8s): Using Minikube for local cluster deployment (API & MLflow server), `kubectl`.
* **MLOps & Data Pipeline:**
    * MLflow: For experiment tracking (parameters, metrics, S3 artifacts), MLflow UI.
    * Apache Airflow (v3.0.1): For workflow orchestration (DAGs, PythonOperator), Airflow UI.
* **Web Development & API:**
    * Flask: For building the REST API.
    * Gunicorn: As a WSGI server for Flask.
    * Requests: For HTTP calls from the UI to the API.
* **UI Development:**
    * Gradio: For building the interactive web UI.
    * Hugging Face Spaces: For deploying the Gradio UI.
* **Environment Management:** Miniconda, Mamba, Conda environments.
* **NLP (Basic):** Rule-based entity extraction, text processing.
* **Other:** REST APIs, JSON, YAML, Git, WSL (Windows Subsystem for Linux).

## 🏗️ Project Architecture (High-Level)

1.  **UI (Gradio - Local or Hugging Face):** User uploads PDF.
2.  **Flask API (Local Docker or K8s Pod):** Receives PDF.
    * Uploads PDF to an S3 "uploads" prefix.
    * Calls AWS Textract to get text from the S3 PDF.
    * Calls AWS Comprehend with the extracted text.
    * Applies local rule-based skill matching.
    * Combines results.
    * Logs parameters, metrics, and artifacts (extracted text, skills) to MLflow Server (which uses S3 for artifacts).
    * Returns extracted details to the UI.
3.  **Airflow DAG (Local `standalone`):**
    * Monitors an S3 "batch_intake" prefix (simulated by finding one file).
    * Processes found PDFs using `PythonOperator` (calling Textract, Comprehend, skill logic).
    * Logs results to MLflow Server.
    * Moves processed files in S3 to "processed/" or "failed/" prefixes.
4.  **MLflow Server (Local or K8s Pod):**
    * Receives tracking data from API and Airflow.
    * Stores experiment metadata locally (SQLite via `emptyDir` in K8s for demo, or local `mlruns` file backend).
    * Stores artifacts in a dedicated S3 bucket.

## ⚙️ Local Setup and Installation

Follow these steps to set up and run the project locally on WSL (Ubuntu).

**Prerequisites:**

* WSL 2 with Ubuntu installed.
* Miniconda or Anaconda installed within WSL.
* Mamba installed (`conda install mamba -n base -c conda-forge`).
* Docker Desktop installed on Windows, with WSL 2 integration enabled.
* AWS Account and AWS CLI configured locally (`aws configure`) with an IAM user having necessary permissions (S3 full access to relevant buckets, Textract full access, Comprehend full access).
* (Optional) A Docker Hub account if you wish to push images there.
* (Optional) A Hugging Face account for deploying the UI.

**1. Create and Activate New Conda Environment:**

```bash
# Remove old environment if it exists from previous attempts (optional)
mamba env remove -n resume_parser_env_v2 -y || true

# Create the new environment
mamba create -n resume_parser_env_v2 python=3.10 -c conda-forge -y
conda activate resume_parser_env_v2
2. Install Core Python Libraries:

Bash

# Ensure (resume_parser_env_v2) is active
mamba install pandas jupyterlab scikit-learn nltk spacy boto3 -c conda-forge -y
python -m spacy download en_core_web_sm
3. Install Airflow, MLflow, Web & UI Libraries (Using Pip with Constraints):

Bash

# Ensure (resume_parser_env_v2) is active
AIRFLOW_VERSION=3.0.1 # Or the latest stable version you used
PYTHON_VERSION=3.10
CONSTRAINT_URL="[https://raw.githubusercontent.com/apache/airflow/constraints-<span class="math-inline">\]\(<52\>https\://raw\.githubusercontent\.com/apache/airflow/constraints\-</span>){AIRFLOW_VERSION}/constraints-<span class="math-inline">\{PYTHON\_VERSION\}\.txt"
pip install \\
"apache\-airflow\[amazon\]\=\=</span>{AIRFLOW_VERSION}" \
    mlflow \
    flask \
    gunicorn \
    gradio \
    requests \
    --constraint "${CONSTRAINT_URL}"
4. AWS Setup (Recap - ensure these are done):

AWS CLI configured (aws configure).
S3 Buckets Created:
YOUR_UNIQUE_BUCKET_NAME: With prefixes like uploads/, batch_intake/, processed/, failed/. (Replace YOUR_UNIQUE_BUCKET_NAME with your actual bucket name).
YOUR_MLFLOW_BUCKET_NAME: For MLflow artifacts. (Replace YOUR_MLFLOW_BUCKET_NAME with your actual bucket name).
IAM User Permissions: Your configured IAM user needs full access to S3 (for the buckets above), Textract, and Comprehend.
5. Create requirements.txt Files (Recommended):

For API Docker image (resume_parser_project/requirements_api.txt):

Plaintext

flask
boto3
gunicorn
mlflow
requests 
# Add any other specific libraries imported ONLY in api.py
Then update your main Dockerfile to use COPY requirements_api.txt requirements.txt.

For Gradio UI Hugging Face Space (resume_parser_project/requirements_gradio_hf.txt):

Plaintext

gradio
requests
(Optional) For full Conda environment replication (environment.yml):

Bash

# While (resume_parser_env_v2) is active:
mamba env export > environment.yml
6. MLflow Setup (Local UI with S3 Artifacts):

Open a new WSL terminal.
Activate environment: conda activate resume_parser_env_v2
Navigate to project root: cd path/to/resume_parser_project
Run:
Bash

mlflow ui --host 0.0.0.0 --port 5000 --default-artifact-root s3://YOUR_MLFLOW_BUCKET_NAME/
(Replace YOUR_MLFLOW_BUCKET_NAME). Keep this terminal running.
7. Airflow Setup (Local standalone):

Open a new WSL terminal.
Activate environment: conda activate resume_parser_env_v2
Set AIRFLOW_HOME:
Bash

export AIRFLOW_HOME=~/airflow_v2 # Or your chosen Airflow home
# Consider adding 'export AIRFLOW_HOME=~/airflow_v2' to your ~/.bashrc
mkdir -p $AIRFLOW_HOME
Initialize DB (if first time for this AIRFLOW_HOME): airflow db init
Create Admin User (if first time):
Bash

airflow users create \
    --username admin \
    --password YOUR_CHOSEN_AIRFLOW_PASSWORD \
    --firstname Your \
    --lastname Name \
    --role Admin \
    --email your@email.com
(Replace YOUR_CHOSEN_AIRFLOW_PASSWORD).
Airflow Variables & Connections (via UI http://localhost:8080):
Connection:
Conn Id: aws_default
Conn Type: Amazon Web Services
Set AWS Access Key ID & AWS Secret Access Key.
Set Region Name (e.g., us-east-1).
Variables:
mlflow_tracking_uri: http://127.0.0.1:5000
Copy your DAG file (e.g., s3_resume_processing_dag_v3.py from the project's airflow_dags folder) to $AIRFLOW_HOME/dags/.
Start Airflow:
Bash

airflow standalone
(Keep this terminal running. Access UI at http://localhost:8080).
8. Kubernetes (Minikube) Setup (Optional - for K8s deployment of API & MLflow Server):

Ensure kubectl and Minikube are installed.
Start Minikube: minikube start --driver=docker
Create AWS credentials secret: kubectl create secret generic aws-credentials --from-file=$HOME/.aws/credentials
Push your resume-parser-api image and YOUR_DOCKERHUB_USERNAME/mlflow-server-custom:v2.13.0 (the MLflow image with boto3) to Docker Hub or your accessible registry.
Update and apply your Kubernetes manifest files in the kubernetes/ directory.
🚀 Running the Project Components
1. Local Dockerized Flask API:

Ensure MLflow UI is running (Setup step 6).
Build your resume-parser-api Docker image if you haven't (or it has changed):
Bash

# In resume_parser_project root (where API's Dockerfile is)
docker build -t resume-parser-api . 
Run the API container (replace placeholders):
Bash

docker stop resume-api-local || true && docker rm resume-api-local || true

docker run -d \
    -p 5001:5000 \
    -v ~/.aws:/root/.aws:ro \
    -e S3_BUCKET_NAME="YOUR_UNIQUE_BUCKET_NAME" \
    -e TEXTRACT_ROLE_ARN="YOUR_TEXTRACT_ROLE_ARN_VALUE_IF_API_NEEDS_IT" \
    -e AWS_DEFAULT_REGION="YOUR_AWS_REGION" \
    -e MLFLOW_TRACKING_URI="[http://host.docker.internal:5000](http://host.docker.internal:5000)" \
    --name resume-api-local \
    resume-parser-api
(Ensure environment variables match what api.py expects. TEXTRACT_ROLE_ARN may not be strictly needed by api.py's Textract call if your IAM user has direct Textract permissions, but set it if the script expects it).
2. Local Gradio UI (Calling Local Docker API):

Ensure the local Dockerized Flask API is running (step above).
In app/ui_app.py, ensure TARGET_API_URL (or similar variable) is set to http://localhost:5001/parse_resume.
Run from project root:
Bash

# Ensure (resume_parser_env_v2) is active
python app/ui_app.py
Access UI at http://127.0.0.1:7860 (or the port Gradio shows).
3. Airflow DAG:

Ensure Airflow standalone is running and MLflow UI is running.
Upload a test PDF to s3://YOUR_UNIQUE_BUCKET_NAME/batch_intake/.
In Airflow UI (http://localhost:8080), find s3_resume_processing_v3, unpause it, and trigger it.
Monitor the DAG run and check MLflow for new runs.
4. Kubernetes Deployment (API & MLflow Server):

Apply manifest files: kubectl apply -f kubernetes/
Access MLflow UI via kubectl port-forward svc/mlflow-service 5000:5000 -> http://localhost:5000.
Get API URL: minikube service resume-parser-service --url. Test with curl.
5. Gradio UI on Hugging Face Spaces:

Requires your API to be publicly accessible.
Option A (Recommended for Demo): Deploy your Flask API to a public endpoint (e.g., AWS App Runner, Google Cloud Run). Set this public URL as a Secret named TARGET_API_URL in your HF Space.
Option B (Temporary/Dev): Use ngrok to expose your local Dockerized API. Use the temporary ngrok URL as the TARGET_API_URL Secret. Your local machine and API must be running.
Set up your Hugging Face Space:
Upload app.py (your ui_app.py code, modified to read TARGET_API_URL from os.environ).
Upload requirements_gradio_hf.txt (containing gradio, requests).
📁 Project Structure (Example)
resume_parser_project/
├── airflow_dags/                 # Airflow DAG definitions (e.g., s3_resume_processing_dag_v3.py)
├── app/                          # Flask API and Gradio UI
│   ├── api.py                    # Flask API code
│   └── ui_app.py                 # Gradio UI code
├── kubernetes/                   # Kubernetes manifest files (deployment.yaml, service.yaml for API & MLflow)
├── data/                         # Local raw data (e.g., PDF downloads for testing)
│   └── raw/
├── Dockerfile                    # For the Flask API (should use requirements_api.txt)
├── mlflow.Dockerfile             # For the custom MLflow server image with boto3
├── requirements_api.txt          # For the API Docker image
├── requirements_gradio_hf.txt    # For Hugging Face Space
├── environment.yml               # Full Conda environment export (optional)
├── README.md                     # This file
└── .gitignore
# --- Directories created by tools (add to .gitignore) ---
# ~/airflow_v2/                   # AIRFLOW_HOME if set here
# mlruns/                         # Local MLflow tracking data (if not overridden by remote server)
# .ipynb_checkpoints/
# __pycache__/
# *.pyc
(Consider adding common patterns like *.DS_Store, venv/, env/, build/, dist/, *.egg-info/ to your .gitignore).

💡 MLOps Concepts Covered
This project provides hands-on experience with several key MLOps concepts:

Experiment Tracking: Using MLflow to log parameters, metrics, and artifacts, enabling reproducibility and comparison.
S3 as an Artifact Store: Configuring MLflow to use a centralized S3 bucket for storing large artifacts.
Containerization: Using Docker to package the Flask API (and a custom MLflow server) for consistent deployment.
Orchestration:
Apache Airflow: For automating and scheduling batch processing workflows (DAGs).
Kubernetes (Minikube): For deploying and managing containerized services locally, including multi-service deployments (API + MLflow).
API Deployment: Serving the core logic via a REST API (Flask).
Cloud Services: Leveraging AWS services (S3, Textract, Comprehend) for core functionalities.
Environment Management: Using Conda/Mamba for isolated Python environments.
Basic UI for ML Apps: Using Gradio for quick and easy UI development and deployment (Hugging Face Spaces).
Conceptual Understanding:
Deploying services to managed cloud platforms (like AWS App Runner).
CI/CD principles for automating the software lifecycle.
🚀 Future Enhancements
Implement a persistent database (e.g., RDS PostgreSQL) for the MLflow backend when deployed on K8s/ECS.
Deploy Airflow to Kubernetes or use Amazon MWAA.
Develop a custom NER model (e.g., with spaCy) for skill extraction and integrate its training/deployment into the MLOps pipeline.
Create a more sophisticated Airflow DAG with S3 sensors, parallel processing of multiple files, and robust error handling for large batches.
Implement a full CI/CD pipeline using GitHub Actions to automate testing, image building, and deployments.
Add more comprehensive input validation and error handling in the API.
Expand the UI features (e.g., displaying more details from Textract/Comprehend).