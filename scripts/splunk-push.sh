#!/usr/bin/env bash

set -o pipefail

# aws cli -
aws lambda invoke \
  --cli-binary-format raw-in-base64-out \
  --function-name "prm-gp-registrations-mi-reporting-SplunkUploader-AMaxIEhXb4SB" \
  --log-type Tail \
  --cli-read-timeout 600 \
  splunk_uploader.txt



  # arn:aws:lambda:eu-west-2:836652383940:function:prm-gp-registrations-mi-reporting-SplunkUploader-AMaxIEhXb4SB