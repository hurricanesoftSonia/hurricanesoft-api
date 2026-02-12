FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY . /app/
RUN pip install --no-cache-dir -e /app/ && \
    pip install --no-cache-dir psycopg2-binary

# Create config directory
RUN mkdir -p /root/.hurricanesoft

EXPOSE 8080

CMD ["python", "-m", "hurricanesoft_api", "--host", "0.0.0.0", "--port", "8080"]
