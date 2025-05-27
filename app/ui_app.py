import gradio as gr
import requests
import os
import json

# --- Configuration ---
# Replace this with your actual App Runner URL from Section 10.6
# For Hugging Face Spaces, we'll use an environment variable later.
APP_RUNNER_API_URL_LOCAL_TEST = "https://vspfqqvejz.ap-southeast-1.awsapprunner.com/parse_resume" # e.g., "https://<id>.<region>.awsapprunner.com/parse_resume"

# For Hugging Face deployment, the URL will be read from a secret
APP_RUNNER_API_URL = os.environ.get("APP_RUNNER_API_URL", APP_RUNNER_API_URL_LOCAL_TEST)

def process_resume_via_api(pdf_file_object):
    """
    Sends the uploaded PDF to the App Runner API and returns the extracted keywords.
    'pdf_file_object' is a TemporaryFile object from Gradio.
    """
    if pdf_file_object is None:
        return "Error: No PDF file provided."

    files = {'resume': (pdf_file_object.name, open(pdf_file_object.name, 'rb'), 'application/pdf')}

    try:
        print(f"Sending request to: {APP_RUNNER_API_URL}")
        response = requests.post(APP_RUNNER_API_URL, files=files, timeout=300) # Increased timeout
        response.raise_for_status()  # Raises an exception for HTTP errors (4xx or 5xx)

        api_response = response.json()

        # Format the output for better readability
        output_text = "--- Extracted Details ---\n"
        if "mlflow_run_id" in api_response: # Check if this key exists
            output_text += f"MLflow Run ID: {api_response['mlflow_run_id']}\n"
        output_text += f"S3 Path: {api_response.get('s3_path', 'N/A')}\n"
        output_text += f"Textract Job ID: {api_response.get('textract_job_id', 'N/A')}\n\n"

        output_text += "Combined Keywords/Entities:\n"
        if api_response.get("combined_keywords"):
            output_text += "\n".join([f"- {kw}" for kw in api_response["combined_keywords"]])
        else:
            output_text += "No keywords extracted."

        # Optionally, add more details
        # output_text += "\n\nRule-Based Skills:\n"
        # output_text += "\n".join([f"- {kw}" for kw in api_response.get("rule_based_skills", [])])
        # output_text += "\n\nText Snippet:\n"
        # output_text += api_response.get("text_snippet", "")

        return output_text

    except requests.exceptions.HTTPError as http_err:
        error_message = f"HTTP error occurred: {http_err}\n"
        try: # Try to get more details from the API's JSON error response
            error_details = response.json()
            error_message += f"API Error: {error_details.get('error', 'Unknown API error')}"
        except ValueError: # If response is not JSON
            error_message += f"Response Content: {response.text}"
        print(error_message)
        return error_message
    except requests.exceptions.RequestException as req_err:
        print(f"Request exception: {req_err}")
        return f"Error connecting to API: {req_err}"
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return f"An unexpected error occurred: {e}"

# Define Gradio Interface
iface = gr.Interface(
    fn=process_resume_via_api,
    inputs=gr.File(label="Upload Resume PDF", file_types=['.pdf']),
    outputs=gr.Textbox(label="Extraction Results", lines=15, placeholder="Results will appear here..."),
    title="📄 Resume Parser",
    description="Upload a PDF resume to extract keywords and entities using AWS Textract, Comprehend, and custom rules via our deployed API.",
    allow_flagging="never"
)

if __name__ == "__main__":
    print(f"Using API URL: {APP_RUNNER_API_URL}")
    if "YOUR_APP_RUNNER_URL_HERE" in APP_RUNNER_API_URL and not os.environ.get("APP_RUNNER_API_URL"):
        print("\nWARNING: You are using the placeholder APP_RUNNER_API_URL_LOCAL_TEST.")
        print("Please replace 'YOUR_APP_RUNNER_URL_HERE/parse_resume' in app/ui_app.py with your actual App Runner URL for local testing.\n")
    iface.launch()