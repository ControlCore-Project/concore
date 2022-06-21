FROM centos/python-36-centos7

WORKDIR /fri
COPY . /fri

COPY requirements.txt /fri/requirements.txt
RUN pip install -r /fri/requirements.txt


CMD ["gunicorn", "-w", "4", "--bind", "0.0.0.0:8080", "main:app"]
