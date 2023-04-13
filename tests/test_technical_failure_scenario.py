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
    
    # Arrange

    index = get_or_create_index("test_index", service)

    conversation_id = 'METRICS_BY_SENDING_SUPPLIER'

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
        '.[] | select( .registrationStatus == "INTEGRATED" ) | select( .sendingPracticeSupplierName == "EMIS" ) | select( .count == "1" )', telemetry)

def test_metrics_by_receiving_supplier():
    
    # Arrange

    index = get_or_create_index("test_index", service)

    conversation_id = 'METRICS_BY_RECEIVING_SUPPLIER'

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
        '.[] | select( .registrationStatus == "INTEGRATED" ) | select( .requestingPracticeSupplierName == "TPP" ) | select( .count == "1" )', telemetry)

def test_metrics_by_single_error_code():
    
    # Arrange

    index = get_or_create_index("test_index", service)

    conversation_id = 'METRICS_BY_SINGLE_ERROR'

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
        '.[] | select( .registrationStatus == "INTEGRATED" ) | select( .requestingPracticeSupplierName == "TPP" ) | select( .errorHistory == "EHR_RESPONSE_99" ) | select( .count == "1" )', telemetry)

def test_metrics_by_multiple_error_codes():
    
    # Arrange

    index = get_or_create_index("test_index", service)

    conversation_id = 'METRICS_BY_SINGLE_ERROR'

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
                sendingPracticeSupplierName="EMIS",
                requestingPracticeSupplierName="TPP",
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

    # Assert
    assert jq.first(
        '.[] | select( .registrationStatus == "INTEGRATED" ) | select( .requestingPracticeSupplierName == "TPP" ) | select( .errorHistory  == ["EHR_RESPONSE_80", "EHR_RESPONSE_99"] ) | select( .count == "1" )', telemetry)

def test_metrics_by_unordered_error_codes():

     # Arrange

    index = get_or_create_index("test_index", service)

    # Conversation 1
    conversation_id = 'METRICS_BY_UNORDERED_ERROR_1'

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
                sendingPracticeSupplierName="EMIS",
                requestingPracticeSupplierName="TPP",
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
                sendingPracticeSupplierName="EMIS",
                requestingPracticeSupplierName="TPP"               
            )),
        sourcetype="myevent")
    
    # Conversation 2

    conversation_id = 'METRICS_BY_UNORDERED_ERROR_2'

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
                registration_event_datetime="2023-03-10T08:20:00",
                event_type=EventType.ERROR.value,
                sendingPracticeSupplierName="EMIS",
                requestingPracticeSupplierName="TPP",
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
                registration_event_datetime="2023-03-10T08:30:30",
                event_type=EventType.ERROR.value,
                sendingPracticeSupplierName="EMIS",
                requestingPracticeSupplierName="TPP",
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

    # Assert
    assert jq.first(
        '.[] | select( .registrationStatus == "INTEGRATED" ) | select( .requestingPracticeSupplierName == "TPP" ) | select( .errorHistory  == ["EHR_RESPONSE_80", "EHR_RESPONSE_99"] ) | select( .count == "2" )', telemetry)
   
 