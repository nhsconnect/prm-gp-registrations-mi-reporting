#!/bin/bash

set -o pipefail

BUCKET_ROOT_NAME=prm-gp-registrations-mi-reporting
ENV=prod
export BUCKET_NAME="${BUCKET_ROOT_NAME}-${ENV}"

aws s3api head-bucket --bucket "${BUCKET_NAME}" 2>&1 | grep -q 'Not Found'
BUCKET_EXISTS=$?

set -e

chalice package build/

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

aws cloudformation package \
  --template-file build/sam.json \
  --s3-bucket "${BUCKET_NAME}" \
  --output-template-file "./build/packaged-cf.json" \
  --use-json

# L.F Todo create bucket as part of cf so all in same stack.
aws cloudformation deploy --template-file ./build/packaged-cf.json --stack-name prm-gp-registrations-mi-reporting --capabilities CAPABILITY_IAM
