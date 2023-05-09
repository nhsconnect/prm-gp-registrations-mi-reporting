import logging
import os
from enum import Enum
import pytest
import json
from time import sleep
from splunklib import client
import jq
from helpers.splunk \
    import get_telemetry_from_splunk, get_or_create_index, create_sample_event, set_variables_on_query, \
    create_integration_payload,  create_error_payload, create_transfer_compatibility_payload
from datetime import datetime, timedelta
from jinja2 import Environment, FileSystemLoader
from .base_test_report import splunk_index

LOG = logging.getLogger(__name__)


class EventType(Enum):
    READY_TO_INTEGRATE_STATUSES = 'READY_TO_INTEGRATE_STATUSES'
    REGISTRATIONS = 'REGISTRATIONS'
    EHR_INTEGRATIONS = 'EHR_INTEGRATIONS'
    ERRORS = 'ERRORS'
    EHR_RESPONSES = 'EHR_RESPONSES'
    EHR_REQUESTS = 'EHR_REQUESTS'
    TRANSFER_COMPATIBILITY_STATUSES = 'TRANSFER_COMPATIBILITY_STATUSES'


splunk_token = os.environ['SPLUNK_TOKEN']

# defaults to localhost - see README
splunk_host = os.environ.get('SPLUNK_HOST')

service = client.connect(token=splunk_token)


def get_search(search_name):
    path = os.path.join(os.path.dirname(__file__),
                        '../reports')
    env = Environment(loader=FileSystemLoader(path))
    template = env.get_template(f'{search_name}.splunk')
    return template.render()


def savedsearch(test_query):
    return "search "+test_query


def test_outcome_successful_integration():

    # Arrange

    index_name, index = splunk_index.create(service)

    conversation_id = 'test_outcome_successful_integration'

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:00:00",
                event_type=EventType.EHR_INTEGRATIONS.value,
                payload=create_integration_payload(outcome="INTEGRATED")

            )),
        sourcetype="myevent")
    # Act

    test_query = get_search('gp2gp_outcome_report')
    test_query = set_variables_on_query(test_query, {
        "$index$": index_name,
        "$report_start$": "2023-03-01",
        "$report_end$": "2023-03-31"
    })

    sleep(2)

    telemetry = get_telemetry_from_splunk(savedsearch(test_query), service)
    LOG.info(f'telemetry: {telemetry}')

    # Assert - check that there is 1 event each (count), 3 events in total (totalCount) and the percentage is 33.3
    assert jq.first(
        '.[] | select( .outcome == "SUCCESSFUL_INTEGRATION" ) | select( .count == "1" )', telemetry)

    splunk_index.delete(index_name)


def test_outcome_rejected():

    # Arrange

    index_name, index = splunk_index.create(service)

    conversation_id = 'test_outcome_rejected'

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:00:00",
                event_type=EventType.EHR_INTEGRATIONS.value,
                payload=create_integration_payload(outcome="REJECTED")

            )),
        sourcetype="myevent")
    # Act

    test_query = get_search('gp2gp_outcome_report')
    test_query = set_variables_on_query(test_query, {
        "$index$": index_name,
        "$report_start$": "2023-03-01",
        "$report_end$": "2023-03-31"
    })

    sleep(2)

    telemetry = get_telemetry_from_splunk(savedsearch(test_query), service)
    LOG.info(f'telemetry: {telemetry}')

    # Assert - check that there is 1 event each (count), 3 events in total (totalCount) and the percentage is 33.3
    assert jq.first(
        '.[] | select( .outcome == "REJECTED" ) | select( .count == "1" )', telemetry)

    splunk_index.delete(index_name)


def test_outcome_technical_failure_1():

    # Arrange

    index_name, index = splunk_index.create(service)

    conversation_id = 'test_outcome_technical_failure'

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:00:00",
                event_type=EventType.EHR_INTEGRATIONS.value,
                payload=create_integration_payload(
                    outcome="FAILED_TO_INTEGRATE")

            )),
        sourcetype="myevent")
    # Act

    test_query = get_search('gp2gp_outcome_report')
    test_query = set_variables_on_query(test_query, {
        "$index$": index_name,
        "$report_start$": "2023-03-01",
        "$report_end$": "2023-03-31"
    })

    sleep(2)

    telemetry = get_telemetry_from_splunk(savedsearch(test_query), service)
    LOG.info(f'telemetry: {telemetry}')

    # Assert - check that there is 1 event each (count), 3 events in total (totalCount) and the percentage is 33.3
    assert jq.first(
        '.[] | select( .outcome == "TECHNICAL_FAILURE" ) | select( .count == "1" )', telemetry)

    splunk_index.delete(index_name)


def test_outcome_awaiting_integration():

    # Arrange

    index_name, index = splunk_index.create(service)

    conversation_id = 'test_outcome_awaiting_integration'

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:00:00",
                event_type=EventType.READY_TO_INTEGRATE_STATUSES.value)
        ),
        sourcetype="myevent")
    # Act

    test_query = get_search('gp2gp_outcome_report')
    test_query = set_variables_on_query(test_query, {
        "$index$": index_name,
        "$report_start$": "2023-03-01",
        "$report_end$": "2023-03-31"
    })

    sleep(2)

    telemetry = get_telemetry_from_splunk(savedsearch(test_query), service)
    LOG.info(f'telemetry: {telemetry}')

    # Assert - check that there is 1 event each (count), 3 events in total (totalCount) and the percentage is 33.3
    assert jq.first(
        '.[] | select( .outcome == "AWAITING_INTEGRATION" ) | select( .count == "1" )', telemetry)

    splunk_index.delete(index_name)


def test_outcome_technical_failure_2():

    # Arrange

    index_name, index = splunk_index.create(service)

    conversation_id = 'test_outcome_technical_failure'

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:00:00",
                event_type=EventType.EHR_RESPONSES.value
            )),
        sourcetype="myevent")
    # Act

    test_query = get_search('gp2gp_outcome_report')
    test_query = set_variables_on_query(test_query, {
        "$index$": index_name,
        "$report_start$": "2023-03-01",
        "$report_end$": "2023-03-31"
    })

    sleep(2)

    telemetry = get_telemetry_from_splunk(savedsearch(test_query), service)
    LOG.info(f'telemetry: {telemetry}')

    # Assert - check that there is 1 event each (count), 3 events in total (totalCount) and the percentage is 33.3
    assert jq.first(
        '.[] | select( .outcome == "TECHNICAL_FAILURE" ) | select( .count == "1" )', telemetry)

    splunk_index.delete(index_name)


def test_outcome_in_progress():

    # Arrange

    index_name, index = splunk_index.create(service)

    conversation_id = 'test_outcome_in_progress'

    # registration_event_datetime="2023-03-10T08:00:00",

    # test requires a datetime less than 24hrs
    now_minus_23_hours = datetime.today() - timedelta(hours=23, minutes=0)
    LOG.info(f"now_minus_23_hours: {now_minus_23_hours}")

    index.submit(
        json.dumps(
            create_sample_event(
                "test_ehr_requesting_outside_sla_test#1.a",
                registration_event_datetime="2023-05-09T06:15:00",
                event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                payload=create_transfer_compatibility_payload(
                    internalTransfer=False,
                    transferCompatible=True
                )
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-05-09T07:00:00",
                event_type=EventType.EHR_REQUESTS.value
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-05-09T08:00:00",
                event_type=EventType.EHR_RESPONSES.value
            )),
        sourcetype="myevent")
    # Act

    test_query = get_search('gp2gp_outcome_report')
    test_query = set_variables_on_query(test_query, {
        "$index$": index_name,
        "$report_start$": "2023-03-01",
        "$report_end$": "2023-03-31"
    })

    sleep(2)

    telemetry = get_telemetry_from_splunk(savedsearch(test_query), service)
    LOG.info(f'telemetry: {telemetry}')

    # Assert - check that there is 1 event each (count), 3 events in total (totalCount) and the percentage is 33.3
    assert jq.first(
        '.[] | select( .outcome == "IN_PROGRESS" ) | select( .count == "1" )', telemetry)

    splunk_index.delete(index_name)
