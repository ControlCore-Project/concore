FROM python:3.10-slim
 
WORKDIR /src
RUN apt-get update && apt-get install -y build-essential g++ libgl1 libx11-6 && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir numpy pyzmq
COPY . .
# generated node build dirs only have a requirements.txt if the node's .dir provides one
RUN if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi

