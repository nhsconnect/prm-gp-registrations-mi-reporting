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

LOG = logging.getLogger(__name__)

class EventType(Enum):
    READY_TO_INTEGRATE_STATUSES = 'READY_TO_INTEGRATE_STATUSES'
    REGISTRATIONS = 'REGISTRATIONS'
    EHR_INTEGRATIONS = 'EHR_INTEGRATIONS'
    ERROR = 'ERROR'
    EHR_RESPONSE = 'EHR_RESPONSE'
    EHR_REQUEST = 'EHR_REQUEST'
    TRANSFER_COMPATIBILITY_STATUSES = 'TRANSFER_COMPATIBILITY_STATUSES'


splunk_token = os.environ['SPLUNK_TOKEN']

# defaults to localhost - see README
splunk_host = os.environ.get('SPLUNK_HOST')

service = client.connect(token=splunk_token)


def get_search(search_name):
    path = os.path.join(os.path.dirname(__file__),
                        '../reports', f'{search_name}.splunk')
    return open(path, encoding="utf-8").read()


def savedsearch(test_query):
    return "search "+test_query


def teardown_function():
    """Function delete test_index."""
    service.indexes.delete("test_index")


def test_reporting_window_then_return_event_within() -> None:
    """Function create test index."""
    index = get_or_create_index("test_index", service)

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id="WITHIN_REPORT_WINDOW",
                registration_event_datetime="2023-03-10T00:00:00",
                event_type=EventType.READY_TO_INTEGRATE_STATUSES.value
            )),
        sourcetype="myevent")
    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id="OUTSIDE_REPORT_WINDOW",
                registration_event_datetime="2023-03-20T00:00:00",
                event_type=EventType.READY_TO_INTEGRATE_STATUSES.value
            )),
        sourcetype="myevent")

    test_query = get_search('gp2gp_reporting_window')
    test_query = set_variables_on_query(test_query, {
        "$index$": "test_index",
        "$cutoff$": "2",
        "$report_start$": "2023-03-09",
        "$report_end$": "2023-03-11"
    })

    sleep(2)

    telemetry = get_telemetry_from_splunk(savedsearch(test_query), service)

    assert len(telemetry) == 1
    assert jq.first('.[]._raw | fromjson.conversationId',
                    telemetry) == 'WITHIN_REPORT_WINDOW'


@pytest.mark.skip(reason="need to implement test for existing saved search.")
def test_reporting_window_as_savedsearch():
    index = get_or_create_index("test_index", service)

    service.saved_searches.create(
        'gp2gp_reporting_window', get_search('gp2gp_reporting_window'))

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id="WITHIN_REPORT_WINDOW",
                registration_event_datetime="2023-03-10T00:00:00",
                event_type=EventType.READY_TO_INTEGRATE_STATUSES.value
            )),
        sourcetype="myevent")
    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id="OUTSIDE_REPORT_WINDOW",
                registration_event_datetime="2023-03-20T00:00:00",
                event_type=EventType.READY_TO_INTEGRATE_STATUSES.value
            )),
        sourcetype="myevent")

    test_query = get_search('gp2gp_reporting_proccess')
    test_query = set_variables_on_query(test_query, {
        "$index$": "test_index",
        "$cutoff$": "2",
        "$report_start$": "2023-03-09",
        "$report_end$": "2023-03-11"
    })

    sleep(2)

    telemetry = get_telemetry_from_splunk(test_query, service)
    service.saved_searches.delete('gp2gp_reporting_window')
    LOG.debug(jq.all('.[]._raw | fromjson.registrationEventDateTime', telemetry))

    assert len(telemetry) == 1
    assert jq.first('.[]._raw | fromjson.conversationId',
                    telemetry) == 'WITHIN_REPORT_WINDOW'


def test_business_process_report_integrated_within_8_days():

    # Arrange

    index = get_or_create_index("test_index", service)

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id="INTEGRATED_WITHIN_8_DAYS",
                registration_event_datetime="2023-03-10T08:00:00",
                event_type=EventType.REGISTRATIONS.value
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id="INTEGRATED_WITHIN_8_DAYS",
                registration_event_datetime="2023-03-10T08:19:00",
                event_type=EventType.EHR_INTEGRATIONS.value
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id="INTEGRATED_WITHIN_8_DAYS",
                registration_event_datetime="2023-03-14T10:00:00",
                event_type=EventType.READY_TO_INTEGRATE_STATUSES.value
            )),
        sourcetype="myevent")

    # Act

    test_query = get_search('gp2gp_business_process_report')
    test_query = set_variables_on_query(test_query, {
        "$index$": "test_index",
        "$cutoff$": "10",
        "$report_start$": "2023-03-09",
        "$report_end$": "2023-03-20"
    })

    sleep(2)

    telemetry = get_telemetry_from_splunk(savedsearch(test_query), service)

    # Assert

    assert len(telemetry) == 4
    assert jq.first('.[] | select( .label == "INTERGRATED_LESS_THAN_8_DAYS") | .count',
                    telemetry) == '1'


def test_business_process_report_not_integrated_within_8_days():

    # Arrange

    index = get_or_create_index("test_index", service)

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id="NOT_INTERGRATED_LESS_THAN_8_DAYS",
                registration_event_datetime="2023-03-10T08:00:00",
                event_type=EventType.REGISTRATIONS.value
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id="NOT_INTERGRATED_LESS_THAN_8_DAYS",
                registration_event_datetime="2023-03-10T08:19:00",
                event_type=EventType.READY_TO_INTEGRATE_STATUSES.value
            )),
        sourcetype="myevent")

    # Act

    test_query = get_search('gp2gp_business_process_report')
    test_query = set_variables_on_query(test_query, {
        "$index$": "test_index",
        "$cutoff$": "7",
        "$report_start$": "2023-03-09",
        "$report_end$": "2023-03-20"
    })

    sleep(2)

    telemetry = get_telemetry_from_splunk(savedsearch(test_query), service)

    # Assert

    assert len(telemetry) == 4
    assert jq.first('.[] | select( .label == "NOT_INTERGRATED_LESS_THAN_8_DAYS") | .count',
                    telemetry) == '1'


def test_business_process_report_integrated_over_8_days():

    # Arrange

    index = get_or_create_index("test_index", service)

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id="INTERGRATED_MORE_THAN_8_DAYS",
                registration_event_datetime="2023-03-10T08:00:00",
                event_type=EventType.REGISTRATIONS.value
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id="INTERGRATED_MORE_THAN_8_DAYS",
                registration_event_datetime="2023-03-10T08:19:00",
                event_type=EventType.READY_TO_INTEGRATE_STATUSES.value
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id="INTERGRATED_MORE_THAN_8_DAYS",
                registration_event_datetime="2023-03-19T10:00:00",
                event_type=EventType.EHR_INTEGRATIONS.value
            )),
        sourcetype="myevent")

    # Act

    test_query = get_search('gp2gp_business_process_report')
    test_query = set_variables_on_query(test_query, {
        "$index$": "test_index",
        "$cutoff$": "15",
        "$report_start$": "2023-03-09",
        "$report_end$": "2023-03-29"
    })

    sleep(2)

    telemetry = get_telemetry_from_splunk(savedsearch(test_query), service)

    # Assert

    assert len(telemetry) == 4
    assert jq.first('.[] | select( .label == "INTERGRATED_MORE_THAN_8_DAYS") | .count',
                    telemetry) == '1'


def test_business_process_report_not_integrated_over_8_days():

    # Arrange

    index = get_or_create_index("test_index", service)

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id="NOT_INTERGRATED_MORE_THAN_8_DAYS",
                registration_event_datetime="2023-03-10T08:00:00",
                event_type=EventType.REGISTRATIONS.value
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id="NOT_INTERGRATED_MORE_THAN_8_DAYS",
                registration_event_datetime="2023-03-10T08:19:00",
                event_type=EventType.READY_TO_INTEGRATE_STATUSES.value
            )),
        sourcetype="myevent")

    # Act

    test_query = get_search('gp2gp_business_process_report')
    test_query = set_variables_on_query(test_query, {
        "$index$": "test_index",
        "$cutoff$": "15",
        "$report_start$": "2023-03-09",
        "$report_end$": "2023-03-29"
    })

    sleep(2)

    telemetry = get_telemetry_from_splunk(savedsearch(test_query), service)

    # Assert

    assert len(telemetry) == 4
    assert jq.first('.[] | select( .label == "NOT_INTERGRATED_MORE_THAN_8_DAYS") | .count',
                    telemetry) == '1'


def test_moa_outcome_SUCCESS_status_INTEGRATED():

    # Arrange

    index = get_or_create_index("test_index", service)

    conversation_id = 'OUTCOME_SUCCESS_REG_STATUS_INTEGRATION'

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:00:00",
                event_type=EventType.REGISTRATIONS.value
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:19:00",
                event_type=EventType.READY_TO_INTEGRATE_STATUSES.value
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:19:00",
                event_type=EventType.EHR_INTEGRATIONS.value
            )),
        sourcetype="myevent")

    # Act

    test_query = get_search('gp2gp_moa_report')
    test_query = set_variables_on_query(test_query, {
        "$index$": "test_index",
        "$report_start$": "2023-03-09",
        "$report_end$": "2023-03-29"
    })

    sleep(2)

    telemetry = get_telemetry_from_splunk(savedsearch(test_query), service)
    LOG.debug(f'telemetry: {telemetry}')

    # Assert

    # assert len(telemetry) == 4
    assert jq.first(
        '.[] | select( .outcome == "SUCCESS" ) | select( .registration_status == "INTEGRATED" ) | .count', telemetry) == '1'


def test_moa_outcome_REJECTED_status_INTEGRATED():

    # Arrange

    index = get_or_create_index("test_index", service)

    conversation_id = 'OUTCOME_REJECTED_REG_STATUS_INTEGRATED'

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:00:00",
                event_type=EventType.REGISTRATIONS.value
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:19:00",
                event_type=EventType.READY_TO_INTEGRATE_STATUSES.value
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:19:00",
                event_type=EventType.EHR_INTEGRATIONS.value,
                payload=create_integration_payload(outcome="REJECTED")
            )),
        sourcetype="myevent")

    # Act

    test_query = get_search('gp2gp_moa_report')
    test_query = set_variables_on_query(test_query, {
        "$index$": "test_index",
        "$report_start$": "2023-03-09",
        "$report_end$": "2023-03-29"
    })

    sleep(10)
    sleep(2)

    telemetry = get_telemetry_from_splunk(savedsearch(test_query), service)
    LOG.debug(f'telemetry: {telemetry}')

    # Assert
    assert jq.first(
        '.[] | select( .outcome == "REJECTED" ) | select( .registration_status == "INTEGRATED" ) | .count', telemetry) == '1'


def test_moa_outcome_TECHNICAL_FAILURE_status_INTEGRATED():

    # Arrange

    index = get_or_create_index("test_index", service)

    conversation_id = 'OUTCOME_TECHNICAL_FAILURE_REG_STATUS_INTEGRATED'

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:00:00",
                event_type=EventType.REGISTRATIONS.value
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:19:00",
                event_type=EventType.READY_TO_INTEGRATE_STATUSES.value
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:19:00",
                event_type=EventType.EHR_INTEGRATIONS.value,
                payload=create_integration_payload(
                    outcome="FAILED_TO_INTEGRATE")
            )),
        sourcetype="myevent")

    # Act

    test_query = get_search('gp2gp_moa_report')
    test_query = set_variables_on_query(test_query, {
        "$index$": "test_index",
        "$report_start$": "2023-03-09",
        "$report_end$": "2023-03-29"
    })

    sleep(10)
    sleep(2)

    telemetry = get_telemetry_from_splunk(savedsearch(test_query), service)
    LOG.debug(f'telemetry: {telemetry}')

    # Assert
    assert jq.first(
        '.[] | select( .outcome == "TECHNICAL_FAILURE" ) | select( .registration_status == "INTEGRATED" ) | .count', telemetry) == '1'


def test_moa_outcome_AWAITING_INTEGRATION_status_READY_TO_INTEGRATE():

    # Arrange

    index = get_or_create_index("test_index", service)

    conversation_id = 'OUTCOME_AWAITING_INTEGRATION_REG_STATUS_READY_TO_INTEGRATE'

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:00:00",
                event_type=EventType.REGISTRATIONS.value
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:19:00",
                event_type=EventType.READY_TO_INTEGRATE_STATUSES.value
            )),
        sourcetype="myevent")

    # Act

    test_query = get_search('gp2gp_moa_report')
    test_query = set_variables_on_query(test_query, {
        "$index$": "test_index",
        "$report_start$": "2023-03-09",
        "$report_end$": "2023-03-29"
    })

    sleep(2)

    telemetry = get_telemetry_from_splunk(savedsearch(test_query), service)
    LOG.debug(f'telemetry: {telemetry}')

    # Assert
    assert jq.first(
        '.[] | select( .outcome == "AWAITING_INTEGRATION" ) | select( .registration_status == "READY_TO_INTEGRATE" ) | .count', telemetry) == '1'


def test_moa_outcome_IN_PROGRESS_status_EHR_SENT():

    # Arrange

    index = get_or_create_index("test_index", service)

    conversation_id = 'OUTCOME_IN_PROGRESS_REG_STATUS_EHR_SENT'

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:00:00",
                event_type=EventType.REGISTRATIONS.value
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:19:00",
                event_type=EventType.READY_TO_INTEGRATE_STATUSES.value
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:50:00",
                event_type=EventType.EHR_REQUEST.value
            )),
        sourcetype="myevent")

    # test requires a response within 24 hours
    d = datetime.today() - timedelta(hours=23, minutes=0)

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime=d.strftime("%Y-%m-%dT%H:%M:%S"),
                event_type=EventType.EHR_RESPONSE.value
            )),
        sourcetype="myevent")

    # Act

    test_query = get_search('gp2gp_moa_report')
    test_query = set_variables_on_query(test_query, {
        "$index$": "test_index",
        "$report_start$": "2023-03-09",
        "$report_end$": "2023-03-29"
    })

    sleep(2)

    telemetry = get_telemetry_from_splunk(savedsearch(test_query), service)
    LOG.debug(f'telemetry: {telemetry}')

    # Assert
    assert jq.first(
        '.[] | select( .outcome == "IN_PROGRESS" ) | select( .registration_status == "EHR_SENT" ) | .count', telemetry) == '1'


def test_moa_outcome_TECHNICAL_FAILURE_status_EHR_SENT():

    # Arrange

    index = get_or_create_index("test_index", service)

    conversation_id = 'OUTCOME_TECHNICAL_FAILURE_REG_STATUS_EHR_SENT'

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:00:00",
                event_type=EventType.REGISTRATIONS.value
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:19:00",
                event_type=EventType.READY_TO_INTEGRATE_STATUSES.value
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:50:00",
                event_type=EventType.EHR_REQUEST.value
            )),
        sourcetype="myevent")

    # test requires a datetime 24 hours+
    d = datetime.today() - timedelta(hours=24, minutes=0)
    LOG.debug(f"D: {d}")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime=d.strftime("%Y-%m-%dT%H:%M:%S"),
                event_type=EventType.EHR_RESPONSE.value
            )),
        sourcetype="myevent")

    # Act

    test_query = get_search('gp2gp_moa_report')
    test_query = set_variables_on_query(test_query, {
        "$index$": "test_index",
        "$report_start$": "2023-03-09",
        "$report_end$": "2023-03-29"
    })

    sleep(2)

    telemetry = get_telemetry_from_splunk(savedsearch(test_query), service)
    LOG.debug(f'telemetry: {telemetry}')

    # Assert
    assert jq.first(
        '.[] | select( .outcome == "TECHNICAL_FAILURE" ) | select( .registration_status == "EHR_SENT" ) | .count', telemetry) == '1'


def test_moa_outcome_IN_PROGRESS_status_EHR_REQUESTED():

    # Arrange

    index = get_or_create_index("test_index", service)

    conversation_id = 'OUTCOME_IN_PROGRESS_REG_STATUS_EHR_REQUESTED'

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:00:00",
                event_type=EventType.REGISTRATIONS.value
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:19:00",
                event_type=EventType.READY_TO_INTEGRATE_STATUSES.value
            )),
        sourcetype="myevent")

    # test requires a datetime less than 20mins
    d = datetime.today() - timedelta(hours=0, minutes=19)
    LOG.debug(f"D: {d}")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime=d.strftime("%Y-%m-%dT%H:%M:%S"),
                event_type=EventType.EHR_REQUEST.value
            )),
        sourcetype="myevent")

    # Act

    test_query = get_search('gp2gp_moa_report')
    test_query = set_variables_on_query(test_query, {
        "$index$": "test_index",
        "$report_start$": "2023-03-09",
        "$report_end$": "2023-03-29"
    })

    sleep(2)

    telemetry = get_telemetry_from_splunk(savedsearch(test_query), service)
    LOG.debug(f'telemetry: {telemetry}')

    # Assert
    assert jq.first(
        '.[] | select( .outcome == "IN_PROGRESS" ) | select( .registration_status == "EHR_REQUESTED" ) | .count', telemetry) == '1'


def test_moa_outcome_TECHNICAL_FAILURE_status_SLOW_EHR_REQUESTED():

    # Arrange

    index = get_or_create_index("test_index", service)

    conversation_id = 'OUTCOME_TECHNICAL_FAILURE_REG_STATUS_SLOW_EHR_REQUESTED'

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:00:00",
                event_type=EventType.REGISTRATIONS.value
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:19:00",
                event_type=EventType.READY_TO_INTEGRATE_STATUSES.value
            )),
        sourcetype="myevent")

    # test requires a datetime equal to or greater than 20mins
    d = datetime.today() - timedelta(hours=0, minutes=25)
    LOG.debug(f"D: {d}")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime=d.strftime("%Y-%m-%dT%H:%M:%S"),
                event_type=EventType.EHR_REQUEST.value
            )),
        sourcetype="myevent")

    # Act

    test_query = get_search('gp2gp_moa_report')
    test_query = set_variables_on_query(test_query, {
        "$index$": "test_index",
        "$report_start$": "2023-03-09",
        "$report_end$": "2023-03-29"
    })

    sleep(2)

    telemetry = get_telemetry_from_splunk(savedsearch(test_query), service)
    LOG.debug(f'telemetry: {telemetry}')

    # Assert
    assert jq.first(
        '.[] | select( .outcome == "TECHNICAL_FAILURE" ) | select( .registration_status == "SLOW_EHR_REQUESTED" ) | .count', telemetry) == '1'


def test_moa_outcome_IN_PROGRESS_status_TRANSFER_NOT_STARTED():

    # Arrange
    index = get_or_create_index("test_index", service)

    conversation_id = 'OUTCOME_IN_PROGRESS_REG_STATUS_TRANSFER_NOT_STARTED'

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:00:00",
                event_type=EventType.REGISTRATIONS.value
            )),
        sourcetype="myevent")

    # test requires a datetime less than 20mins
    d = datetime.today() - timedelta(hours=0, minutes=19)
    LOG.debug(f"D: {d}")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime=d.strftime("%Y-%m-%dT%H:%M:%S"),
                event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                payload=create_transfer_compatibility_payload(
                    internalTransfer=False,
                    transferCompatible=True
                )
            )),
        sourcetype="myevent")

    # Act

    test_query = get_search('gp2gp_moa_report')
    test_query = set_variables_on_query(test_query, {
        "$index$": "test_index",
        "$report_start$": "2023-03-09",
        "$report_end$": "2023-03-29"
    })

    sleep(2)

    telemetry = get_telemetry_from_splunk(savedsearch(test_query), service)
    LOG.debug(f'telemetry: {telemetry}')

    # Assert
    assert jq.first(
        '.[] | select( .outcome == "IN_PROGRESS" ) | select( .registration_status == "TRANSFER_NOT_STARTED" ) | .count', telemetry) == '1'

def test_moa_outcome_TECHNICAL_FAILURE_status_SLOW_TRANSFER_NOT_STARTED():

    # Arrange
    index = get_or_create_index("test_index", service)

    conversation_id = 'OUTCOME_TECHNICAL_FAILURE_REG_STATUS_SLOW_TRANSFER_NOT_STARTED'

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:00:00",
                event_type=EventType.REGISTRATIONS.value
            )),
        sourcetype="myevent")

    # test requires a datetime greater than or equal to 20mins
    d = datetime.today() - timedelta(hours=0, minutes=20)
    LOG.debug(f"D: {d}")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime=d.strftime("%Y-%m-%dT%H:%M:%S"),
                event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                payload=create_transfer_compatibility_payload(
                    internalTransfer=False,
                    transferCompatible=True
                )
            )),
        sourcetype="myevent")

    # Act

    test_query = get_search('gp2gp_moa_report')
    test_query = set_variables_on_query(test_query, {
        "$index$": "test_index",
        "$report_start$": "2023-03-09",
        "$report_end$": "2023-03-29"
    })

    sleep(2)

    telemetry = get_telemetry_from_splunk(savedsearch(test_query), service)
    LOG.debug(f'telemetry: {telemetry}')

    # Assert
    assert jq.first(
        '.[] | select( .outcome == "TECHNICAL_FAILURE" ) | select( .registration_status == "SLOW_TRANSFER_NOT_STARTED" ) | .count', telemetry) == '1'
    
def test_moa_outcome_IN_PROGRESS_status_INTERNAL_TRANSFER():

    # Arrange
    index = get_or_create_index("test_index", service)

    conversation_id = 'OUTCOME_TECHNICAL_FAILURE_REG_STATUS_INTERNAL_TRANSFER'

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:00:00",
                event_type=EventType.REGISTRATIONS.value
            )),
        sourcetype="myevent")

   

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T09:00:00",
                event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                payload=create_transfer_compatibility_payload(
                    internalTransfer=True,
                    transferCompatible=True
                )
            )),
        sourcetype="myevent")

    # Act

    test_query = get_search('gp2gp_moa_report')
    test_query = set_variables_on_query(test_query, {
        "$index$": "test_index",
        "$report_start$": "2023-03-09",
        "$report_end$": "2023-03-29"
    })

    sleep(2)

    telemetry = get_telemetry_from_splunk(savedsearch(test_query), service)
    LOG.debug(f'telemetry: {telemetry}')

    # Assert
    assert jq.first(
        '.[] | select( .outcome == "IN_PROGRESS" ) | select( .registration_status == "INTERNAL_TRANSFER" ) | .count', telemetry) == '1'
    
def test_moa_outcome_NOT_COMPATIBLE_status_INTERNAL_TRANSFER():

    # Arrange
    index = get_or_create_index("test_index", service)

    conversation_id = 'OUTCOME_NOT_COMPATIBLE_REG_STATUS_INTERNAL_TRANSFER'

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:00:00",
                event_type=EventType.REGISTRATIONS.value
            )),
        sourcetype="myevent")

   

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T09:00:00",
                event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                payload=create_transfer_compatibility_payload(
                    internalTransfer=True,
                    transferCompatible=False
                )
            )),
        sourcetype="myevent")

    # Act

    test_query = get_search('gp2gp_moa_report')
    test_query = set_variables_on_query(test_query, {
        "$index$": "test_index",
        "$report_start$": "2023-03-09",
        "$report_end$": "2023-03-29"
    })

    sleep(2)

    telemetry = get_telemetry_from_splunk(savedsearch(test_query), service)
    LOG.debug(f'telemetry: {telemetry}')

    # Assert
    assert jq.first(
        '.[] | select( .outcome == "NOT_COMPATIBLE" ) | select( .registration_status == "INTERNAL_TRANSFER" ) | .count', telemetry) == '1'
    
def test_moa_outcome_NOT_COMPATIBLE_status_ELECTRONIC_TRANSFER():

    # Arrange
    index = get_or_create_index("test_index", service)

    conversation_id = 'OUTCOME_NOT_COMPATIBLE_REG_STATUS_ELECTRONIC_TRANSFER'

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:00:00",
                event_type=EventType.REGISTRATIONS.value
            )),
        sourcetype="myevent")

   

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T09:00:00",
                event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                payload=create_transfer_compatibility_payload(
                    internalTransfer=False,
                    transferCompatible=False
                )
            )),
        sourcetype="myevent")

    # Act

    test_query = get_search('gp2gp_moa_report')
    test_query = set_variables_on_query(test_query, {
        "$index$": "test_index",
        "$report_start$": "2023-03-09",
        "$report_end$": "2023-03-29"
    })

    sleep(2)

    telemetry = get_telemetry_from_splunk(savedsearch(test_query), service)
    LOG.debug(f'telemetry: {telemetry}')

    # Assert
    assert jq.first(
        '.[] | select( .outcome == "NOT_COMPATIBLE" ) | select( .registration_status == "ELECTRONIC_TRANSFER" ) | .count', telemetry) == '1'
    
def test_moa_percentage_of_all_transfers():
    '''Tests that the result contains the % of all transers'''

    # Arrange

    index = get_or_create_index("test_index", service)    

    # Create three registrations with different event types.
   
    # Event 1 - outcome_SUCCESS_status_INTEGRATED

    conversation_id = 'OUTCOME_SUCCESS_REG_STATUS_INTEGRATION'

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:00:00",
                event_type=EventType.REGISTRATIONS.value
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:19:00",
                event_type=EventType.READY_TO_INTEGRATE_STATUSES.value
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:19:00",
                event_type=EventType.EHR_INTEGRATIONS.value
            )),
        sourcetype="myevent")
    
    # Event 2 - outcome_REJECTED_status_INTEGRATED

    conversation_id = 'OUTCOME_REJECTED_REG_STATUS_INTEGRATED'

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:00:00",
                event_type=EventType.REGISTRATIONS.value
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:19:00",
                event_type=EventType.READY_TO_INTEGRATE_STATUSES.value
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:19:00",
                event_type=EventType.EHR_INTEGRATIONS.value,
                payload=create_integration_payload(outcome="REJECTED")
            )),
        sourcetype="myevent")
    
    # Event 3 - outcome: Tehnical Failure, reg Status: Integrated
    
    conversation_id = 'OUTCOME_TECHNICAL_FAILURE_REG_STATUS_INTEGRATED'

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:00:00",
                event_type=EventType.REGISTRATIONS.value
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:19:00",
                event_type=EventType.READY_TO_INTEGRATE_STATUSES.value
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:19:00",
                event_type=EventType.EHR_INTEGRATIONS.value,
                payload=create_integration_payload(
                    outcome="FAILED_TO_INTEGRATE")
            )),
        sourcetype="myevent")

    # Act

    test_query = get_search('gp2gp_moa_report')
    test_query = set_variables_on_query(test_query, {
        "$index$": "test_index",
        "$report_start$": "2023-03-09",
        "$report_end$": "2023-03-29"
    })

    sleep(2)

    telemetry = get_telemetry_from_splunk(savedsearch(test_query), service)
    LOG.debug(f'telemetry: {telemetry}')

    # Assert - check that there is 1 event each (count), 3 events in total (totalCount) and the percentage is 33.3
    assert jq.all(
        '.[] | select( .total_events == "3" ) | select( .count =="1") | select( .percentage_of_all_transfers | startswith("33.3")) ',telemetry)    


def test_moa_percentage_of_technical_failures():
    '''Tests that the result contains the % of technical_failures'''

    # Arrange

    index = get_or_create_index("test_index", service)    

    # Create three registrations with two being technical failure. Should give a result of 66.6%.
   
    # Event 1 - outcome_SUCCESS_status_INTEGRATED

    conversation_id = 'OUTCOME_SUCCESS_REG_STATUS_INTEGRATION'

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:00:00",
                event_type=EventType.REGISTRATIONS.value
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:19:00",
                event_type=EventType.READY_TO_INTEGRATE_STATUSES.value
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:19:00",
                event_type=EventType.EHR_INTEGRATIONS.value
            )),
        sourcetype="myevent")
    
    # Event 2 - outcome_REJECTED_status_INTEGRATED

    conversation_id = 'OUTCOME_TECHNICAL_FAILURE_REG_STATUS_INTEGRATED_1'

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:00:00",
                event_type=EventType.REGISTRATIONS.value
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:19:00",
                event_type=EventType.READY_TO_INTEGRATE_STATUSES.value
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:19:00",
                event_type=EventType.EHR_INTEGRATIONS.value,
                payload=create_integration_payload(
                    outcome="FAILED_TO_INTEGRATE")
            )),
        sourcetype="myevent")
    
    # Event 3 - outcome: Tehnical Failure, reg Status: Integrated
    
    conversation_id = 'OUTCOME_TECHNICAL_FAILURE_REG_STATUS_INTEGRATED_2'

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:00:00",
                event_type=EventType.REGISTRATIONS.value
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:19:00",
                event_type=EventType.READY_TO_INTEGRATE_STATUSES.value
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:19:00",
                event_type=EventType.EHR_INTEGRATIONS.value,
                payload=create_integration_payload(
                    outcome="FAILED_TO_INTEGRATE")
            )),
        sourcetype="myevent")

    # Act

    test_query = get_search('gp2gp_moa_report')
    test_query = set_variables_on_query(test_query, {
        "$index$": "test_index",
        "$report_start$": "2023-03-09",
        "$report_end$": "2023-03-29"
    })

    sleep(2)

    telemetry = get_telemetry_from_splunk(savedsearch(test_query), service)
    LOG.info(f'telemetry: {telemetry}')

    # Assert - check that there is 1 event each (count), 3 events in total (totalCount) and the percentage is 33.3
    assert jq.all(
        '.[] | select( .total_events == "3" ) | select( .count =="2") | select( .percentage_of_all_transfers | startswith("66.6")) | select( .percentage_of_technical_failures | startswith("66.6")) ',telemetry)   