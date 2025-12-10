# 1. Use an official Python image
FROM python:3.10-slim

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Copy requirements first (for caching)
COPY requirements.txt .

# 4. Install dependencies
# We add --no-cache-dir to keep the image small
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the rest of the application code
COPY . .

# 6. Expose the port (Render usually uses 10000, but it sets $PORT env var)
EXPOSE 8000

# 7. Command to run the app
# Force 1 worker to save RAM and disable access logs for speed
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1 --no-access-log"]