FROM python:3.10-slim

WORKDIR /app

# Copy dependency definition
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Expose port 8080
EXPOSE 8080

# Command to run your app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]