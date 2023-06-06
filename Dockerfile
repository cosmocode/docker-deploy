FROM alpine:3.11

COPY fabfile.py /

RUN echo http://dl-cdn.alpinelinux.org/alpine/edge/testing >> /etc/apk/repositories
RUN apk add --no-cache openssh-client curl python3 libffi-dev openssl-dev build-base python3-dev
RUN pip3 install --upgrade pip
RUN pip3 install 'fabric<2.0'

