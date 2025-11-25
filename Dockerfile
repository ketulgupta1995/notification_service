FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt ./
# Install gcc and build tools
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*
    
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.services.notifier:app", "--host", "0.0.0.0", "--port", "8000"]