FROM centos/python-36-centos7
COPY requirements.txt /tmp/requirements.txt   
RUN pip install -r /tmp/requirements.txt       
WORKDIR /fri   
COPY server /fri       
USER root       
RUN useradd fri && chown -R fri /fri       
USER fri        
CMD ["gunicorn", "--timeout=180", "--workers=4", "--bind=0.0.0.0:8080", "--access-logfile=-", "main:app"]