FROM python:3.6-slim

RUN apt-get update && apt-get install -y ca-certificates \
    && update-ca-certificates \
    && python3 -m ensurepip --default-pip \
    && pip install --upgrade pip setuptools wheel

COPY requirements.txt /tmp/requirements.txt   
RUN pip install -r /tmp/requirements.txt   

WORKDIR /fri   
COPY server /fri   
   
USER root       
RUN useradd fri && chown -R fri /fri  
     
USER fri        
CMD ["gunicorn", "--timeout=180", "--workers=4", "--bind=0.0.0.0:8080", "--access-logfile=-", "main:app"]