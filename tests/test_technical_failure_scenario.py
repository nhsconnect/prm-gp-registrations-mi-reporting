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

@pytest.mark.skip(reason="Being used as an example for other tests here.")
def test_technical_failure_scenario_table():
    '''Tests the output for the technical failure scenario table'''

    # Arrange

    index = get_or_create_index("wed3", service)

    # Create an event for every technical failure scenario

    # Event 1 - TECHNICAL_FAULURE_INTEGRATED - error with EHR response

    conversation_id = 'OUTCOME_TECHNICAL_FAILURE_REG_STATUS_INTEGRATED'

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:00:00",
                event_type=EventType.REGISTRATIONS.value,
                sendingPracticeSupplierName="EMIS",
                requestingPracticeSupplierName="TPP"
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:19:00",
                event_type=EventType.EHR_REQUEST.value,
                sendingPracticeSupplierName="EMIS",
                requestingPracticeSupplierName="TPP"
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:19:00",
                event_type=EventType.EHR_RESPONSE.value,
                sendingPracticeSupplierName="EMIS",
                requestingPracticeSupplierName="TPP"
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:19:00",
                event_type=EventType.ERROR.value,
                sendingPracticeSupplierName="EMIS",
                requestingPracticeSupplierName="TPP",
                payload=create_error_payload(
                    errorCode="90",
                    errorDescription="Error with EHR Response",
                    failurePoint=EventType.EHR_RESPONSE.value
                )
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:19:00",
                event_type=EventType.EHR_INTEGRATIONS.value,
                sendingPracticeSupplierName="EMIS",
                requestingPracticeSupplierName="TPP",
                payload=create_integration_payload(
                    outcome="FAILED_TO_INTEGRATE")
            )),
        sourcetype="myevent")

    # Event 2 - outcome_REJECTED_status_INTEGRATED

    conversation_id = 'OUTCOME_TECHNICAL_FAILURE_REG_STATUS_INTEGRATED_1'

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:00:00",
                event_type=EventType.REGISTRATIONS.value,
                sendingPracticeSupplierName="TPP",
                requestingPracticeSupplierName="EMIS"
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:19:00",
                event_type=EventType.EHR_REQUEST.value,
                sendingPracticeSupplierName="TPP",
                requestingPracticeSupplierName="EMIS"
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:19:00",
                event_type=EventType.EHR_RESPONSE.value,
                sendingPracticeSupplierName="TPP",
                requestingPracticeSupplierName="EMIS"
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:19:00",
                event_type=EventType.ERROR.value,
                sendingPracticeSupplierName="TPP",
                requestingPracticeSupplierName="EMIS",
                payload=create_error_payload(
                    errorCode="99",
                    errorDescription="Error with EHR Response",
                    failurePoint=EventType.EHR_RESPONSE.value
                )
            )),
        sourcetype="myevent")
    
    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:19:00",
                event_type=EventType.ERROR.value,
                sendingPracticeSupplierName="TPP",
                requestingPracticeSupplierName="EMIS",
                payload=create_error_payload(
                    errorCode="80",
                    errorDescription="Error with EHR Response",
                    failurePoint=EventType.EHR_RESPONSE.value
                )
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:19:00",
                event_type=EventType.EHR_INTEGRATIONS.value,
                sendingPracticeSupplierName="TPP",
                requestingPracticeSupplierName="EMIS",
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
                event_type=EventType.REGISTRATIONS.value,
                sendingPracticeSupplierName="TPP",
                requestingPracticeSupplierName="EMIS"
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:19:00",
                event_type=EventType.EHR_REQUEST.value,
                sendingPracticeSupplierName="TPP",
                requestingPracticeSupplierName="EMIS"
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:19:00",
                event_type=EventType.EHR_RESPONSE.value,
                sendingPracticeSupplierName="TPP",
                requestingPracticeSupplierName="EMIS"
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:19:00",
                event_type=EventType.ERROR.value,
                sendingPracticeSupplierName="TPP",
                requestingPracticeSupplierName="EMIS",
                payload=create_error_payload(
                    errorCode="80",
                    errorDescription="Error with EHR Response",
                    failurePoint=EventType.EHR_RESPONSE.value
                )
            )),
        sourcetype="myevent")
    
    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:19:00",
                event_type=EventType.ERROR.value,
                sendingPracticeSupplierName="TPP",
                requestingPracticeSupplierName="EMIS",
                payload=create_error_payload(
                    errorCode="99",
                    errorDescription="Error with EHR Response",
                    failurePoint=EventType.EHR_RESPONSE.value
                )
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:19:00",
                event_type=EventType.EHR_INTEGRATIONS.value,
                sendingPracticeSupplierName="TPP",
                requestingPracticeSupplierName="EMIS",
                payload=create_integration_payload(
                    outcome="FAILED_TO_INTEGRATE")
            )),
        sourcetype="myevent")

    # Act

    test_query = get_search('gp2gp_technical_failure_scenario_report')
    test_query = set_variables_on_query(test_query, {
        "$index$": "test_index",
        "$report_start$": "2023-03-01",
        "$report_end$": "2023-03-31"
    })

    sleep(2)

    telemetry = get_telemetry_from_splunk(savedsearch(test_query), service)
    LOG.info(f'telemetry: {telemetry}')

    # Assert - check that there is 1 event each (count), 3 events in total (totalCount) and the percentage is 33.3
    assert jq.first(
        '.[] | select( .outcome == "TECHNICAL_FAILURE" ) | select( .registration_status == "INTEGRATED" ) | select( .sending_supplier == "EMIS" ) | select( .receiving_supplier == "TPP" ) | select( .error_code_history == "90" ) | select( .count =="1")', telemetry)


def test_metrics_by_reg_status():

    # Arrange

    index = get_or_create_index("test_index", service)

    conversation_id = 'REG_STATUS_INTEGRATED'

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:00:00",
                event_type=EventType.REGISTRATIONS.value,
                sendingPracticeSupplierName="EMIS",
                requestingPracticeSupplierName="TPP"
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:19:00",
                event_type=EventType.EHR_REQUEST.value,
                sendingPracticeSupplierName="EMIS",
                requestingPracticeSupplierName="TPP"
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:19:00",
                event_type=EventType.EHR_RESPONSE.value,
                sendingPracticeSupplierName="EMIS",
                requestingPracticeSupplierName="TPP"
            )),
        sourcetype="myevent")
   

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:19:00",
                event_type=EventType.EHR_INTEGRATIONS.value,
                sendingPracticeSupplierName="EMIS",
                requestingPracticeSupplierName="TPP"               
            )),
        sourcetype="myevent")
    # Act

    test_query = get_search('gp2gp_technical_failure_scenario_report')
    test_query = set_variables_on_query(test_query, {
        "$index$": "test_index",
        "$report_start$": "2023-03-01",
        "$report_end$": "2023-03-31"
    })

    sleep(2)

    telemetry = get_telemetry_from_splunk(savedsearch(test_query), service)
    LOG.info(f'telemetry: {telemetry}')

    # Assert - check that there is 1 event each (count), 3 events in total (totalCount) and the percentage is 33.3
    assert jq.first(
        '.[] | select( .registrationStatus == "INTEGRATED" ) | select( .count == "1" )', telemetry)


def test_metrics_by_sending_supplier():
    pass

def test_metrics_by_receiving_supplier():
    pass

def test_metrics_by_single_error_code():
    pass

def test_metrics_by_multiple_error_codes():
    pass

def test_metrics_by_unordered_error_codes():
    pass

def test_metrics_by_no_error_codes():
    pass