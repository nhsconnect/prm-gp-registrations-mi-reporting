#!/usr/bin/env bash

set -o pipefail

# via chalice (options) -
# 1. chalice invoke -n main?
# 2. curl s3://prm-gp-registrations-mi-reporting-dev/cdb017953dacb99de2059bc769124d2a - wrong.

# aws cli -
aws lambda invoke \
  --cli-binary-format raw-in-base64-out \
  --function-name "splunk-uploader" \
  --log-type Tail \
  splunk_uploader.txt