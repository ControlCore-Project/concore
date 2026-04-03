FROM ubuntu:20.04

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        tzdata wget xorg unzip libxtst6 libxt6 libglu1 libxrandr2 x11-utils \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir /mcr-install \
     && mkdir /opt/mcr

WORKDIR /mcr-install

ARG MATLAB_RUNTIME_SHA256="b821022690804e498d2e5ad814dccb64aab17c5e4bc10a1e2a12498ef5364e0d"
ENV MATLAB_RUNTIME_SHA256=${MATLAB_RUNTIME_SHA256}

RUN wget https://ssd.mathworks.com/supportfiles/downloads/R2021a/Release/1/deployment_files/installer/complete/glnxa64/MATLAB_Runtime_R2021a_Update_1_glnxa64.zip \
    && echo "${MATLAB_RUNTIME_SHA256}  MATLAB_Runtime_R2021a_Update_1_glnxa64.zip" | sha256sum -c - \
    && unzip MATLAB_Runtime_R2021a_Update_1_glnxa64.zip \
    && ./install -destinationFolder /opt/mcr -agreeToLicense yes -mode silent \
    && cd / \
    && rm -rf mcr-install

COPY . /src
WORKDIR /src

