## Prerequisites

- Splunk Enterprise installed
- `pip3 install -r requirements.txt`
- pytest

## Running the tests

`SPLUNK_TOKEN='YOUR_API_TOKEN' SPLUNK_HOST='SPLUNK_HOST' pytest`

Or

`export SPLUNK_TOKEN='YOUR_API_TOKEN'`

`pytest`

## Deploy

environment vars:
- `SPLUNK_HOST` the host for splunk, default: localhost:8089
- `SPLUNK_ADMIN_USERNAME` 
- `SPLUNK_APP_ID` the Splunk app to deploy the reports and dashboards to, default: search
- `SPLUNK_TOKEN` the API access token
- `SPLUNK_INDEX` the index to use for all reports and dashboards, default: 'test_index'

### Deploying the reports
`python3 ./scripts/deploy_saved_searched.py`

### Deploying the dashboards
`python3 ./scripts/deploy_dashboards.py`

## MI Api Events
- REGISTRATIONS
- READY_TO_INTEGRATE_STATUSES
- INTEGRATIONS