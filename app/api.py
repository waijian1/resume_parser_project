import os
import boto3
import time
import json
import logging
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import uuid
import mlflow
import tempfile

# --- Flask App Setup ---
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 # 16 MB upload limit

# --- AWS Configuration (Read from Environment Variables) ---
S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', 'resume-parser-waijian-20250525')
TEXTRACT_ROLE_ARN = os.environ.get('TEXTRACT_ROLE_ARN', 'arn:aws:iam::747549824523:role/TextractS3AccessRole')
AWS_REGION = os.environ.get('AWS_DEFAULT_REGION', 'ap-southeast-1')

# --- MLflow Configuration --- # <--- NEW SECTION
MLFLOW_TRACKING_URI = os.environ.get('MLFLOW_TRACKING_URI')
MLFLOW_EXPERIMENT_NAME = "Resume_Processing_API_V1"

if not S3_BUCKET_NAME or not TEXTRACT_ROLE_ARN:
    logging.error("FATAL ERROR: S3_BUCKET_NAME or TEXTRACT_ROLE_ARN environment variables not set.")
    # In a real app, you might exit or handle this more gracefully.

if MLFLOW_TRACKING_URI:
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    logging.info(f"MLflow tracking URI set to: {MLFLOW_TRACKING_URI}")

mlflow.set_experiment(MLFLOW_EXPERIMENT_NAME)
logging.info(f"MLflow experiment set to: {MLFLOW_EXPERIMENT_NAME}")

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Boto3 Clients ---
s3_client = boto3.client('s3', region_name=AWS_REGION)
textract_client = boto3.client('textract', region_name=AWS_REGION)
comprehend_client = boto3.client('comprehend', region_name=AWS_REGION)

# --- Skill Keywords (You can load this from a file later) ---
SKILL_KEYWORDS = [
    'python', 'java', 'c++', 'sql', 'aws', 'azure', 'gcp', 's3', 'ec2',
    'lambda', 'react', 'angular', 'vue', 'django', 'flask', 'machine learning',
    'data science', 'pandas', 'numpy', 'scikit-learn', 'tensorflow', 'pytorch',
    'docker', 'kubernetes', 'git', 'ci/cd', 'agile', 'airflow', 'mlflow'
    # Add more if want...
]
COMPREHEND_EXCLUDE = ['PERSON', 'LOCATION', 'DATE', 'ORGANIZATION', 'QUANTITY']

# --- Helper Functions (Copied/Adapted from Notebook) ---
def start_textract_job(bucket, document_key):
    logging.info(f"Starting Textract job for: {document_key}")
    try:
        response = textract_client.start_document_text_detection(
            DocumentLocation={'S3Object': {'Bucket': bucket, 'Name': document_key}}
        )
        return response['JobId']
    except Exception as e:
        logging.error(f"Error starting Textract job for {document_key}: {e}")
        return None

def wait_for_job_completion(job_id, delay=5, timeout=300):
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = textract_client.get_document_text_detection(JobId=job_id)
            status = response['JobStatus']
            logging.info(f"Job {job_id} Status: {status}")
            if status == 'SUCCEEDED': return True
            if status in ['FAILED', 'PARTIAL_SUCCESS']: return False
            time.sleep(delay)
        except Exception as e:
            logging.error(f"Error checking job {job_id}: {e}")
            return False
    logging.error(f"Job {job_id} timed out.")
    return False

def get_textract_results(job_id):
    all_blocks = []
    next_token = None
    try:
        while True:
            params = {'JobId': job_id}
            if next_token: params['NextToken'] = next_token
            response = textract_client.get_document_text_detection(**params)
            all_blocks.extend(response.get('Blocks', []))
            next_token = response.get('NextToken')
            if not next_token: break
        return all_blocks
    except Exception as e:
        logging.error(f"Error getting results for {job_id}: {e}")
        return None

def extract_text_from_blocks(blocks):
    return "\n".join([b['Text'] for b in blocks if b['BlockType'] == 'LINE']) if blocks else ""

def find_skills_keyword_based(text, skills_list):
    found = set([skill for skill in skills_list if skill in text.lower()]) if text else set()
    return list(found)

def find_entities_comprehend(text):
    if not text: return []
    try:
        response = comprehend_client.detect_entities(Text=text[:4900], LanguageCode='en')
        return response.get('Entities', [])
    except Exception as e:
        logging.error(f"Error calling Comprehend: {e}")
        return []

def combine_results(rule_skills, comp_entities, exclude_types):
    combined = set([s.lower() for s in rule_skills])
    combined.update([
        e['Text'].lower() for e in comp_entities if e['Type'] not in exclude_types
    ])
    return list(combined)

# --- API Endpoint ---
@app.route('/parse_resume', methods=['POST'])
def parse_resume():
    if 'resume' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files['resume']

    if file.filename == '':
        return jsonify({"error": "No file selected for uploading"}), 400

    if file and file.filename.lower().endswith('.pdf'):
        filename = secure_filename(file.filename)
        unique_filename = f"uploads/{uuid.uuid4()}-{filename}"
        logging.info(f"Received file: {filename}, saving to S3 as {unique_filename}")

        # <--- START MLFLOW RUN ---
        with mlflow.start_run(run_name=f"api_upload_{filename}") as run:
            run_id = run.info.run_id
            logging.info(f"Started MLflow Run ID: {run_id}")
            mlflow.log_param("source", "api_upload")
            mlflow.log_param("original_filename", filename)
            mlflow.log_param("s3_key", unique_filename)
            mlflow.log_param("s3_bucket", S3_BUCKET_NAME)
        
            try:
                # Upload to S3
                s3_client.upload_fileobj(file, S3_BUCKET_NAME, unique_filename)
                logging.info(f"File uploaded to S3: s3://{S3_BUCKET_NAME}/{unique_filename}")
    
                # Start Textract
                job_id = start_textract_job(S3_BUCKET_NAME, unique_filename)
                if not job_id:
                    mlflow.log_metric("status", 0)
                    return jsonify({"error": "Failed to start Textract job"}), 500
                mlflow.log_param("textract_job_id", job_id)
    
                # Wait for Textract
                if not wait_for_job_completion(job_id):
                    mlflow.log_metric("status", 0)
                    return jsonify({"error": "Textract job failed or timed out"}), 500
    
                # Get Results & Process
                blocks = get_textract_results(job_id)
                if not blocks:
                    mlflow.log_metric("status", 0)
                    return jsonify({"error": "Failed to get Textract results"}), 500
    
                extracted_text = extract_text_from_blocks(blocks)
                rule_skills = find_skills_keyword_based(extracted_text, SKILL_KEYWORDS)
                comp_entities = find_entities_comprehend(extracted_text)
                combined_kws = combine_results(rule_skills, comp_entities, COMPREHEND_EXCLUDE)

                # Log Metrics - mlflow
                logging.info("Logging metrics...")
                mlflow.log_metric("text_length_chars", len(extracted_text))
                mlflow.log_metric("num_textract_blocks", len(blocks))
                mlflow.log_metric("num_rule_based_skills", len(rule_skills))
                mlflow.log_metric("num_comprehend_entities", len(comp_entities))
                mlflow.log_metric("num_combined_keywords", len(combined_kws))
                mlflow.log_metric("status", 1) # 1 for success
                logging.info("Metrics logged.")

                # Log Artifacts - mlflow
                logging.info("Logging artifacts...")
                with tempfile.TemporaryDirectory() as tmpdir:
                    # Save combined keywords
                    keywords_path = os.path.join(tmpdir, "combined_keywords.json")
                    with open(keywords_path, "w") as f:
                        json.dump(combined_kws, f, indent=4)
                    mlflow.log_artifact(keywords_path, "results")

                    # Save extracted text
                    text_path = os.path.join(tmpdir, "extracted_text.txt")
                    with open(text_path, "w", encoding='utf-8') as f:
                        f.write(extracted_text)
                    mlflow.log_artifact(text_path, "results")
                logging.info("Artifacts logged.")
                
                # Prepare Response
                response_data = {
                    "s3_path": f"s3://{S3_BUCKET_NAME}/{unique_filename}",
                    "textract_job_id": job_id,
                    "combined_keywords": combined_kws,
                    "rule_based_skills": rule_skills,
                    "comprehend_entities": comp_entities, # Send full details
                    "text_snippet": extracted_text[:500] + "..."
                }
                return jsonify(response_data), 200
    
            except Exception as e:
                logging.error(f"An error occurred during processing: {e}")
                return jsonify({"error": f"Internal server error: {e}"}), 500

    else:
        return jsonify({"error": "Only PDF files are allowed"}), 400

# --- Run the App (for local testing only) ---
if __name__ == '__main__':
    # For local testing, you might need to set env vars manually or use a .env file
    # Example:
    # os.environ['S3_BUCKET_NAME'] = 'your-bucket'
    # os.environ['TEXTRACT_ROLE_ARN'] = 'your-role-arn'
    # os.environ['AWS_DEFAULT_REGION'] = 'your-region'
    app.run(debug=True, host='0.0.0.0', port=5000)