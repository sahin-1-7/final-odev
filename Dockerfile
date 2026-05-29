# 1. Base Image
FROM python:3.11-slim

# 2. Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=run.py
ENV FLASK_ENV=production

# 3. Set work directory
WORKDIR /app

# 4. Install system dependencies for compiling psycopg2 and Pillow
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 5. Copy requirements and install python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copy the rest of the application code
COPY . /app/

# 7. Compile multi-language translation catalogs
RUN pybabel compile -d app/translations

# 8. Expose port
EXPOSE 5000

# 9. Start application using Gunicorn WSGI server
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "run:app"]
