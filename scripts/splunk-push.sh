#!/usr/bin/env bash

set -o pipefail

# aws cli -
aws lambda invoke \
  --cli-binary-format raw-in-base64-out \
  --function-name "splunk-uploader" \
  --log-type Tail \
  splunk_uploader.txt