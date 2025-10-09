FROM python:3.11-slim

WORKDIR /app

# install git + build tools for Python packages
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    libffi-dev \
    libssl-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY prod_assistant ./prod_assistant
COPY . .

EXPOSE 8000
CMD ["bash", "-c", "python prod_assistant/mcp_servers/product_search_server.py & uvicorn prod_assistant.router.main:app --host 0.0.0.0 --port 8000 --workers 2"]
