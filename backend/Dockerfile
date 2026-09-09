FROM python:3.12-slim

WORKDIR /app

# Install dependencies first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# database/ is created at runtime by database.py; mount a volume here to persist data
VOLUME ["/app/database"]

EXPOSE 5001

CMD ["python", "app.py"]