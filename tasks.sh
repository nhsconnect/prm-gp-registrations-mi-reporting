#!/usr/bin/env bash

set -e

# if [ ! -f .env ]
# then
export $(cat .env | xargs)
# fi

readonly aws_region=eu-west-2
readonly IMAGE_NAME="nhsdev/prm-gp-registrations-mi-reporting"

export AWS_CLI_AUTO_PROMPT=off

function assume_ci_role() {
  role_arn_param="/registrations/prod/user-input/cross-account-admin-role"
  if [ "$role_arn_param" != "null" ]; then
    role_arn=$(aws ssm get-parameters --region ${aws_region} --names ${role_arn_param} --query 'Parameters[0].Value' --output text)
    echo "got cross account role"
    session_name="registrations-dashboard-${env_name}-session"

    sts=$(
      aws sts assume-role \
        --role-arn $role_arn \
        --role-session-name $session_name \
        --output json
    )

    export AWS_ACCESS_KEY_ID=$(echo $sts | jq -r .Credentials.AccessKeyId)
    export AWS_SECRET_ACCESS_KEY=$(echo $sts | jq -r .Credentials.SecretAccessKey)
    export AWS_SESSION_TOKEN=$(echo $sts | jq -r .Credentials.SessionToken)
  fi

}

function clear_assumed_iam_role() {
  unset AWS_ACCESS_KEY_ID
  unset AWS_SECRET_ACCESS_KEY
  unset AWS_SESSION_TOKEN
}

function get_ssm_parameter() {
  echo "$(aws ssm get-parameter --region ${aws_region} --name $1 --query Parameter.Value --output text)"
}

function get_encrypted_ssm_parameter() {
  echo "$(aws ssm get-parameter --region ${aws_region} --name $1 --with-decryption --query Parameter.Value --output text)"
}

function check_env {
  if [[ -z "${ENVIRONMENT}" ]]; then
    echo "Must set ENVIRONMENT"
    exit 1
  fi
}

function confirm_current_role {
  sts=$(aws sts get-caller-identity)
  if [[ $? -eq 254 ]]; then
    echo ${sts}
    return 1
  fi

  echo ${sts}
  read -p "Is this the intended role (y/n)? " -n 1 -r
  echo
  if ! [[ $REPLY =~ ^[Yy]$ ]]; then
    exit
  fi
}

readonly command="$1"
case "${command}" in
install-ui-dependencies)
  cd ui
  npm ci
  cd ..
  ;;
upload_data)
  # check_env
  assume_ci_role
  echo $DOCKER_IMAGE
  docker run --name upload_container --rm \
    -v $(pwd):/usr/src/app -i \
    -e AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY -e AWS_SESSION_TOKEN=$AWS_SESSION_TOKEN -e AWS_REGION=$AWS_REGION \
    $DOCKER_IMAGE \
    ./tasks.sh _upload_data
  ;;
build_and_publish)
  # check_env
  assume_ci_role
  docker run --name build_publish_container --rm \
    -v $(pwd):/usr/src/app -i \
    -e AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY -e AWS_SESSION_TOKEN=$AWS_SESSION_TOKEN -e AWS_REGION=$AWS_REGION \ 
    $DOCKER_IMAGE \
    ./tasks.sh _build_and_publish
  ;;
build_and_deploy_splunk_uploader_lambda)
  assume_ci_role
  docker run --name publish_lambdas_container --rm \
    -v $(pwd):/usr/src/app -i \
    -e AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY -e AWS_SESSION_TOKEN=$AWS_SESSION_TOKEN -e AWS_REGION=$AWS_REGION \
    $DOCKER_IMAGE \
    ./tasks.sh _build_and_deploy_splunk_uploader_lambda
  ;;
run_splunk_uploader_lambda)
  assume_ci_role
  docker run --name run_splunk_container --rm \
    -v $(pwd):/usr/src/app -i \
    -e AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY -e AWS_SESSION_TOKEN=$AWS_SESSION_TOKEN -e AWS_REGION=$AWS_REGION \
    $DOCKER_IMAGE \
    ./tasks.sh _run_splunk_uploader_lambda
  ;;
publish_docker)
  IMAGE_TAG=$(date +%s%3N | shasum -a 256 | head -c 40)
  docker_username=$(get_encrypted_ssm_parameter "/repo/prod/user-input/prm-team-dockerhub-username")
  docker_password=$(get_encrypted_ssm_parameter "/repo/prod/user-input/prm-team-dockerhub-password")
  echo $docker_password | docker login --username $docker_username --password-stdin
  echo "Logged in"
  docker buildx build --platform=linux/amd64,linux/arm64 -t $IMAGE_NAME:$IMAGE_TAG -t $IMAGE_NAME:latest --push .
  #docker buildx push ${IMAGE_NAME}:${IMAGE_TAG}
  ;;
_upload_data) #private method
  /bin/bash -c ./scripts/upload-dashboards-and-reports-datasets.sh
  ;;
_build_and_deploy_splunk_uploader_lambda) #private method
  #TODO
  # - Set lambda ENV variable with the Splunk API key ( pulled from parameter store )
  export SPLUNK_TOKEN=$(get_encrypted_ssm_parameter /registrations/prod/user-input/splunk-api-token)
  export SPLUNK_HOST=$(get_ssm_parameter /registrations/prod/user-input/splunk-base-url)
  export SPLUNK_ADMIN_USERNAME=$(get_encrypted_ssm_parameter /registrations/prod/user-input/splunk-admin-username)

  # - Run build_and_deploy.sh
  /bin/bash -c ./scripts/build-and-publish.sh
  ;;
_run_splunk_uploader_lambda)
  # - Invoke CLI command to trigger lambdas

  export SPLUNK_TOKEN=$(get_encrypted_ssm_parameter /registrations/prod/user-input/splunk-api-token)
  
  /bin/bash -c ./scripts/splunk-push.sh
  ;;
*)
  echo "make $@"
  make "$@"
  ;;
esac
