# Use a lightweight official Python runtime as a parent image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY backend/ /app/backend/
COPY frontend/ /app/frontend/
COPY scripts/ /app/scripts/

# Copy the preprocessed SQLite blocklist database
# Note: Ensure you run the preprocessor locally first (python scripts/preprocess_urls.py)
# so that scam_urls.db exists in your workspace before building the image.
COPY scam_urls.db /app/scam_urls.db

# Expose port 8000
EXPOSE 8000

# Define the command to run the FastAPI app
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
