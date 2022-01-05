FROM ubuntu:20.04

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        tzdata wget xorg unzip libxtst6 libxt6 libglu1 libxrandr2 x11-utils \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir /mcr-install \
     && mkdir /opt/mcr

WORKDIR /mcr-install

RUN wget https://ssd.mathworks.com/supportfiles/downloads/R2021a/Release/1/deployment_files/installer/complete/glnxa64/MATLAB_Runtime_R2021a_Update_1_glnxa64.zip

RUN unzip MATLAB_Runtime_R2021a_Update_1_glnxa64.zip \
    && ./install -destinationFolder /opt/mcr -agreeToLicense yes -mode silent \
    && cd / \
    && rm -rf mcr-install

COPY . /src
WORKDIR /src

