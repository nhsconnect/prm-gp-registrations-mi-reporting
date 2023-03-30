## Prerequisites

- Splunk Enterprise installed
- `pip3 install -r requirements.txt`
- pytest

## Running the tests

`SPLUNK_TOKEN='YOUR_LOCAL_API_TOKEN' SPLUNK_HOST='SPLUNK_HOST' pytest`
Or
`export SPLUNK_TOKEN='YOUR_LOCAL_API_TOKEN'`

`pytest`

## Deploy

environment vars:
- `SPLUNK_HOST` the host for splunk, default: localhost:8089
- `SPLUNK_ADMIN_USERNAME` 
- `SPLUNK_APP_ID` the Splunk app to deploy the reports and dashboards to, default: search
- `SPLUNK_TOKEN` the API access token
- `SPLUNK_INDEX` the index to use for all reports and dashboards, default: 'test_index'
- `BUCKET_NAME` the name of the bucket which stores the reports and dashboard data 

### Deploying the reports and dashboards (manually)

There is a GOCD pipeline which will run and publish to Splunk whenever changes are pushed to the main branch. However this can also be done in the local dev environment using the following commands:

- Upload the reports (.splunk) and dashboads (.xml) files to S3
`./tasks upload_data`

- Build and deploy the Splunk Uploader lambda
`./tasks build_and_deploy_splunk_uploader_lambda`

- Run the Splunk Uploader lambda
`./tasks run_splunk_uploader_lambda`

#### Running the lambda locally
`chalice local` 
Note: due to IP restriction Splunk uploading cannot be done from outside of the AWS account.

### Managing the Docker image for the CI pipeline

#### Prerequisites
- docker buildx

#### Updating the Docker image
Only after making changes to the Dockerfile
`./tasks publish_docker`

## MI Api Events
- REGISTRATIONS
- READY_TO_INTEGRATE_STATUSES
- INTEGRATIONS