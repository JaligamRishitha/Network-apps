FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code into backend folder to match import structure
COPY . ./backend/

# Copy main.py and config.py to root for uvicorn
COPY main.py .
COPY config.py .

# Expose port
EXPOSE 4798

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "4798"]
