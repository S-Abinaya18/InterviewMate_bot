# Use official Python runtime as a parent image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy local code to the container image
COPY . .

# Expose port 8080 for Cloud Run
EXPOSE 8080

# Run the Flask app with Gunicorn server
CMD ["gunicorn", "-b", "0.0.0.0:8080", "app:app"]
