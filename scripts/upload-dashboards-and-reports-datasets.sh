#!/bin/bash

set -o pipefail

BUCKET_ROOT_NAME=prm-gp-registrations-mi-reporting
ENV=prod
BUCKET_NAME="${BUCKET_ROOT_NAME}-${ENV}"

aws s3api head-bucket --bucket "${BUCKET_NAME}" 2>&1 | grep -q 'Not Found'
BUCKET_EXISTS=$?

set -e

if [ "${BUCKET_EXISTS}" -ne 1 ]; then
  echo "Deployment bucket does not exist, creating..."
  aws s3api create-bucket \
    --bucket "${BUCKET_NAME}" \
    --acl private \
    --create-bucket-configuration '{ "LocationConstraint": "eu-west-2" }'
  aws s3api wait bucket-exists --bucket "${BUCKET_NAME}"
  aws s3api put-bucket-versioning --bucket "${BUCKET_NAME}" --versioning-configuration Status=Enabled
  aws s3api put-public-access-block \
    --bucket "${BUCKET_NAME}" \
    --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
else
  echo "Deployment bucket already exists"
fi

# copy local files to s3 bucket
aws s3 cp --recursive ./reports/ s3://${BUCKET_NAME}/reports --include "*.splunk"
aws s3 cp --recursive ./dashboards/ s3://${BUCKET_NAME}/dashboards --include "*.xml"