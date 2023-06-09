ARG ALPINE_VERSION=3.17
FROM python:3.11-alpine${ALPINE_VERSION} as builder

ARG AWS_CLI_VERSION=2.11.4
RUN apk add --no-cache git unzip groff build-base libffi-dev cmake
RUN git clone --single-branch --depth 1 -b ${AWS_CLI_VERSION} https://github.com/aws/aws-cli.git

WORKDIR aws-cli
RUN ./configure --with-install-type=portable-exe --with-download-deps
RUN make
RUN make install

# reduce image size: remove autocomplete and examples
RUN rm -rf \
    /usr/local/lib/aws-cli/aws_completer \
    /usr/local/lib/aws-cli/awscli/data/ac.index \
    /usr/local/lib/aws-cli/awscli/examples
RUN find /usr/local/lib/aws-cli/awscli/data -name completions-1*.json -delete
RUN find /usr/local/lib/aws-cli/awscli/botocore/data -name examples-1.json -delete
RUN (cd /usr/local/lib/aws-cli; for a in *.so*; do test -f /lib/$a && rm $a; done)

# build the final image
FROM alpine:${ALPINE_VERSION}
COPY --from=builder /usr/local/lib/aws-cli/ /usr/local/lib/aws-cli/
RUN ln -s /usr/local/lib/aws-cli/aws /usr/local/bin/aws


# required to fix pycryto error
RUN apk add gcc g++ make libffi-dev openssl-dev

RUN apk add python3

# required to fix pycryto error
RUN apk add python3-dev build-base --update-cache

RUN python3 -m ensurepip --upgrade

RUN apk add --no-cache bash
RUN apk add --no-cache jq

WORKDIR /usr/src/app

# COPY requirements.txt ./
# RUN pip3 install --no-cache-dir -r requirements.txt

# Create a new user without specifying the UID and GID
RUN addgroup -S mygroup
RUN adduser -S -G mygroup -h /home/myuser -s /bin/sh myuser

# Switch to the new user
USER myuser