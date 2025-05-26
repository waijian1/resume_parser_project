# 1. Use an official Python runtime as a parent image
FROM python:3.10-slim

# 2. Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 3. Set the working directory in the container
WORKDIR /app

# 4. Install system dependencies (if any - none needed for now)
# RUN apt-get update && apt-get install -y --no-install-recommends some-package

# 5. Copy the requirements file and install Python dependencies
COPY requirements.txt requirements.txt
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# 6. Copy the application code into the container
COPY ./app /app

# 7. Expose the port the app runs on (Gunicorn default is 8000, but we'll tell it 5000)
EXPOSE 5000

# 8. Define the command to run your application using Gunicorn
#    We use 4 workers, bind to 0.0.0.0 (all interfaces), and port 5000.
CMD ["gunicorn", "--workers", "4", "--bind", "0.0.0.0:5000", "--timeout", "360", "api:app"]