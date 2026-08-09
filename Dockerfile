# Use official Python slim image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Change working directory to src so Uvicorn can find main.py
WORKDIR /app/src

# Expose the port FastAPI runs on
EXPOSE 8000

# Run the application from the src directory
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
