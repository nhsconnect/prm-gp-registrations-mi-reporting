## Prerequisites

- Splunk Enterprise installed
- `pip3 install -r requirements.txt`
- pytest

## Running the tests

`SPLUNK_TOKEN='YOUR_API_TOKEN' SPLUNK_HOST='SPLUNK_HOST' pytest`

Or

`export SPLUNK_TOKEN='YOUR_API_TOKEN'`

`pytest`

## MI Api Events
- REGISTRATIONS
- READY_TO_INTEGRATE_STATUSES
- INTEGRATIONS