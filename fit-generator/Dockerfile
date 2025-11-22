FROM python:3.11-alpine

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install wget for healthcheck
RUN apk add --no-cache wget

# Copy application
COPY app.py .

EXPOSE 5000

CMD ["python3", "app.py"]
