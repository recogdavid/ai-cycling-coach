# Use Python 3.11 Alpine base image
FROM python:3.11-alpine

# Set working directory
WORKDIR /app

# Install system dependencies first (needed for psycopg2-binary)
RUN apk add --no-cache --virtual .build-deps gcc musl-dev postgresql-dev

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install wget for healthcheck
RUN apk add --no-cache wget

# Copy application files
COPY . .

# Expose port 5000
EXPOSE 5000

# Set environment variables
ENV DB_HOST=ai-cycling-coach-postgres-1 \
    DB_NAME=aicoach_db \
    DB_USER=aicoach_user \
    DB_PASSWORD=your_password \
    FLASK_APP=app.py \
    FLASK_ENV=development

# Run the application
CMD ["python3", "app.py"]
