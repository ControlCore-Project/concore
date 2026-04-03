FROM mtmiller/octave 

USER root
RUN apt-get update && apt-get install -y --no-install-recommends octave-control octave-signal && rm -rf /var/lib/apt/lists/*
RUN echo "pkg load signal;" >> /etc/octave.conf && echo "pkg load control;" >> /etc/octave.conf

COPY . /src
WORKDIR /src
