FROM python:3.10-slim
 
WORKDIR /src
RUN apt-get update && apt-get install -y build-essential g++ libgl1-mesa-glx libx11-6 && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

