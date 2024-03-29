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


def generate_splunk_query_from_report(search_name):
    path = os.path.join(os.path.dirname(__file__),
                        '../reports')
    env = Environment(loader=FileSystemLoader(path))
    template = env.get_template(f'{search_name}.splunk')
    return template.render()


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
                sendingSupplierName="EMIS",
                requestingSupplierName="TPP"
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:19:00",
                event_type=EventType.EHR_REQUEST.value,
                sendingSupplierName="EMIS",
                requestingSupplierName="TPP"
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:19:00",
                event_type=EventType.EHR_RESPONSE.value,
                sendingSupplierName="EMIS",
                requestingSupplierName="TPP"
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:19:00",
                event_type=EventType.EHR_INTEGRATIONS.value,
                sendingSupplierName="EMIS",
                requestingSupplierName="TPP"
            )),
        sourcetype="myevent")
    # Act

    test_query = generate_splunk_query_from_report('gp2gp_technical_failure_scenario_report')
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
                sendingSupplierName="EMIS",
                requestingSupplierName="TPP"
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:19:00",
                event_type=EventType.EHR_REQUEST.value,
                sendingSupplierName="EMIS",
                requestingSupplierName="TPP"
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:19:00",
                event_type=EventType.EHR_RESPONSE.value,
                sendingSupplierName="EMIS",
                requestingSupplierName="TPP"
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:19:00",
                event_type=EventType.EHR_INTEGRATIONS.value,
                sendingSupplierName="EMIS",
                requestingSupplierName="TPP"
            )),
        sourcetype="myevent")
    # Act

    test_query = generate_splunk_query_from_report('gp2gp_technical_failure_scenario_report')
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
        '.[] | select( .registrationStatus == "INTEGRATED" ) | select( .sendingSupplierName == "EMIS" ) | select( .count == "1" )', telemetry)


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
                sendingSupplierName="EMIS",
                requestingSupplierName="TPP"
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:19:00",
                event_type=EventType.EHR_REQUEST.value,
                sendingSupplierName="EMIS",
                requestingSupplierName="TPP"
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:19:00",
                event_type=EventType.EHR_RESPONSE.value,
                sendingSupplierName="EMIS",
                requestingSupplierName="TPP"
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:19:00",
                event_type=EventType.EHR_INTEGRATIONS.value,
                sendingSupplierName="EMIS",
                requestingSupplierName="TPP"
            )),
        sourcetype="myevent")
    # Act

    test_query = generate_splunk_query_from_report('gp2gp_technical_failure_scenario_report')
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
        '.[] | select( .registrationStatus == "INTEGRATED" ) | select( .requestingSupplierName == "TPP" ) | select( .count == "1" )', telemetry)


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
                sendingSupplierName="EMIS",
                requestingSupplierName="TPP"
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:19:00",
                event_type=EventType.EHR_REQUEST.value,
                sendingSupplierName="EMIS",
                requestingSupplierName="TPP"
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:19:00",
                event_type=EventType.EHR_RESPONSE.value,
                sendingSupplierName="EMIS",
                requestingSupplierName="TPP"
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:19:00",
                event_type=EventType.ERROR.value,
                sendingSupplierName="EMIS",
                requestingSupplierName="TPP",
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
                sendingSupplierName="EMIS",
                requestingSupplierName="TPP"
            )),
        sourcetype="myevent")
    # Act

    test_query = generate_splunk_query_from_report('gp2gp_technical_failure_scenario_report')
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
        '.[] | select( .registrationStatus == "INTEGRATED" ) | select( .requestingSupplierName == "TPP" ) | select( .errorHistory == "EHR_RESPONSE_99" ) | select( .count == "1" )', telemetry)


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
                sendingSupplierName="EMIS",
                requestingSupplierName="TPP"
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:19:00",
                event_type=EventType.EHR_REQUEST.value,
                sendingSupplierName="EMIS",
                requestingSupplierName="TPP"
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:19:00",
                event_type=EventType.EHR_RESPONSE.value,
                sendingSupplierName="EMIS",
                requestingSupplierName="TPP"
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:19:00",
                event_type=EventType.ERROR.value,
                sendingSupplierName="EMIS",
                requestingSupplierName="TPP",
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
                sendingSupplierName="EMIS",
                requestingSupplierName="TPP",
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
                sendingSupplierName="EMIS",
                requestingSupplierName="TPP"
            )),
        sourcetype="myevent")
    # Act

    test_query = generate_splunk_query_from_report('gp2gp_technical_failure_scenario_report')
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
        '.[] | select( .registrationStatus == "INTEGRATED" ) | select( .requestingSupplierName == "TPP" ) | select( .errorHistory  == ["EHR_RESPONSE_80", "EHR_RESPONSE_99"] ) | select( .count == "1" )', telemetry)


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
                sendingSupplierName="EMIS",
                requestingSupplierName="TPP"
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:19:00",
                event_type=EventType.EHR_REQUEST.value,
                sendingSupplierName="EMIS",
                requestingSupplierName="TPP"
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:19:00",
                event_type=EventType.EHR_RESPONSE.value,
                sendingSupplierName="EMIS",
                requestingSupplierName="TPP"
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:19:00",
                event_type=EventType.ERROR.value,
                sendingSupplierName="EMIS",
                requestingSupplierName="TPP",
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
                sendingSupplierName="EMIS",
                requestingSupplierName="TPP",
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
                sendingSupplierName="EMIS",
                requestingSupplierName="TPP"
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
                sendingSupplierName="EMIS",
                requestingSupplierName="TPP"
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:19:00",
                event_type=EventType.EHR_REQUEST.value,
                sendingSupplierName="EMIS",
                requestingSupplierName="TPP"
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:19:00",
                event_type=EventType.EHR_RESPONSE.value,
                sendingSupplierName="EMIS",
                requestingSupplierName="TPP"
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:20:00",
                event_type=EventType.ERROR.value,
                sendingSupplierName="EMIS",
                requestingSupplierName="TPP",
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
                sendingSupplierName="EMIS",
                requestingSupplierName="TPP",
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
                sendingSupplierName="EMIS",
                requestingSupplierName="TPP"
            )),
        sourcetype="myevent")

    # Act

    test_query = generate_splunk_query_from_report('gp2gp_technical_failure_scenario_report')
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
        '.[] | select( .registrationStatus == "INTEGRATED" ) | select( .requestingSupplierName == "TPP" ) | select( .errorHistory  == ["EHR_RESPONSE_80", "EHR_RESPONSE_99"] ) | select( .count == "2" )', telemetry)


def test_percentage_of_all_transfers():

    # Arrange

    index = get_or_create_index("test_index", service)

    conversation_id = 'TRANSFER_1'

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:00:00",
                event_type=EventType.REGISTRATIONS.value,
                sendingSupplierName="EMIS",
                requestingSupplierName="TPP"
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:19:00",
                event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                sendingSupplierName="EMIS",
                requestingSupplierName="TPP",
                payload=create_transfer_compatibility_payload(
                    internalTransfer=False,
                    transferCompatible=True,
                    reason="test"
                )
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:19:00",
                event_type=EventType.EHR_REQUEST.value,
                sendingSupplierName="EMIS",
                requestingSupplierName="TPP"
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:19:00",
                event_type=EventType.EHR_RESPONSE.value,
                sendingSupplierName="EMIS",
                requestingSupplierName="TPP"
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:19:00",
                event_type=EventType.EHR_INTEGRATIONS.value,
                sendingSupplierName="EMIS",
                requestingSupplierName="TPP"
            )),
        sourcetype="myevent")

    conversation_id = 'TRANSFER_2'

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:00:00",
                event_type=EventType.REGISTRATIONS.value,
                sendingSupplierName="TPP",
                requestingSupplierName="EMIS"
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:19:00",
                event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                sendingSupplierName="EMIS",
                requestingSupplierName="TPP",
                payload=create_transfer_compatibility_payload(
                    internalTransfer=False,
                    transferCompatible=True,
                    reason="test"
                )
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:19:00",
                event_type=EventType.EHR_REQUEST.value,
                sendingSupplierName="TPP",
                requestingSupplierName="EMIS"
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:19:00",
                event_type=EventType.EHR_RESPONSE.value,
                sendingSupplierName="TPP",
                requestingSupplierName="EMIS"
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:19:00",
                event_type=EventType.EHR_INTEGRATIONS.value,
                sendingSupplierName="TPP",
                requestingSupplierName="EMIS"
            )),
        sourcetype="myevent")

    conversation_id = 'NOT_A_TRANSFER'

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:19:00",
                event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                sendingSupplierName="EMIS",
                requestingSupplierName="TPP",
                payload=create_transfer_compatibility_payload(
                    internalTransfer=False,
                    transferCompatible=False,
                    reason="New born"
                )
            )),
        sourcetype="myevent")

    # Act

    test_query = generate_splunk_query_from_report('gp2gp_technical_failure_scenario_report')
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
        '.[] | select( .registrationStatus == "INTEGRATED" ) | select( .percentageOfAllTransfers == "50" ) | select( .count == "1" )', telemetry)


def test_multiple_transfer_compatibility_event():

    # Arrange

    index = get_or_create_index("test_index", service)

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id='TRANSFER_1',
                registration_event_datetime="2023-03-10T08:00:00",
                event_type=EventType.REGISTRATIONS.value,
                sendingSupplierName="EMIS_One",
                requestingSupplierName="TPP_One"
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id='TRANSFER_1',
                registration_event_datetime="2023-03-10T08:19:00",
                event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                sendingSupplierName="EMIS_One",
                requestingSupplierName="TPP_One",
                payload=create_transfer_compatibility_payload(
                    internalTransfer=False,
                    transferCompatible=True,
                    reason="test"
                )
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id='TRANSFER_1',
                registration_event_datetime="2023-03-10T08:20:00",
                event_type=EventType.EHR_REQUEST.value,
                sendingSupplierName="EMIS_One",
                requestingSupplierName="TPP_One"
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id='TRANSFER_1',
                registration_event_datetime="2023-03-10T08:25:00",
                event_type=EventType.EHR_RESPONSE.value,
                sendingSupplierName="EMIS_One",
                requestingSupplierName="TPP_One"
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id='TRANSFER_1',
                registration_event_datetime="2023-03-10T08:30:00",
                event_type=EventType.EHR_INTEGRATIONS.value,
                sendingSupplierName="EMIS_One",
                requestingSupplierName="TPP_One"
            )),
        sourcetype="myevent")

    # Conversation two

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id='TRANSFER_2',
                registration_event_datetime="2023-03-10T08:35:00",
                event_type=EventType.REGISTRATIONS.value,
                sendingSupplierName="EMIS_two",
                requestingSupplierName="TPP_two"
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id='TRANSFER_2',
                registration_event_datetime="2023-03-10T08:40:00",
                event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                sendingSupplierName="EMIS_two",
                requestingSupplierName="TPP_two",
                payload=create_transfer_compatibility_payload(
                    internalTransfer=False,
                    transferCompatible=True,
                    reason="test"
                )
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id='TRANSFER_2',
                registration_event_datetime="2023-03-10T08:45:00",
                event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                sendingSupplierName="EMI_two",
                requestingSupplierName="TPP_two",
                payload=create_transfer_compatibility_payload(
                    internalTransfer=False,
                    transferCompatible=False,
                    reason="test"
                )
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id='TRANSFER_2',
                registration_event_datetime="2023-03-10T08:50:00",
                event_type=EventType.EHR_REQUEST.value,
                sendingSupplierName="TPP_two",
                requestingSupplierName="EMIS_two"
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id='TRANSFER_2',
                registration_event_datetime="2023-03-10T08:19:00",
                event_type=EventType.EHR_RESPONSE.value,
                sendingSupplierName="TPP_two",
                requestingSupplierName="EMIS_two"
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id='TRANSFER_2',
                registration_event_datetime="2023-03-10T08:19:00",
                event_type=EventType.EHR_INTEGRATIONS.value,
                sendingSupplierName="TPP_two",
                requestingSupplierName="EMIS_two"
            )),
        sourcetype="myevent")

    conversation_id = 'NOT_A_TRANSFER'

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:30:00",
                event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                sendingSupplierName="EMIS_three",
                requestingSupplierName="TPP_three",
                payload=create_transfer_compatibility_payload(
                    internalTransfer=False,
                    transferCompatible=False,
                    reason="New born"
                )
            )),
        sourcetype="myevent")

    # Act

    test_query = generate_splunk_query_from_report('gp2gp_technical_failure_scenario_report')
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
        '.[] | select( .registrationStatus == "INTEGRATED" ) | select( .percentageOfAllTransfers == "100" ) | select( .count == "1" )', telemetry)


def test_status_INTEGRATION():

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

    test_query = generate_splunk_query_from_report('gp2gp_technical_failure_scenario_report')
    test_query = set_variables_on_query(test_query, {
        "$index$": "test_index",
        "$report_start$": "2023-03-09",
        "$report_end$": "2023-03-29"
    })

    sleep(10)
    sleep(2)

    telemetry = get_telemetry_from_splunk(savedsearch(test_query), service)
    LOG.info(f'telemetry: {telemetry}')

    # Assert
    assert jq.first(
        '.[] | select( .registrationStatus == "INTEGRATION" ) | .count', telemetry) == '1'


def test_status_EHR_SENT_sla_NOT_READY_TO_INTEGRATE_OUTSIDE_SLA():
    '''
    Test scenario - EHR_RESPONSE received, no READY_TO_INTEGRATE event within 20mins.
    '''

    # Arrange

    index = get_or_create_index("test_index", service)

    conversation_id = 'test_status_EHR_SENT_sla_NOT_READY_TO_INTEGRATE_OUTSIDE_SLA'

    # reporting window
    yesterday = datetime.today() - timedelta(hours=24)
    tomorrow = datetime.today() + timedelta(hours=24)
     
    now_minus_1_hr = datetime.today() - timedelta(hours=1)

     # test requires a time greater than 20mins
    now_minus_20_mins = datetime.today() - timedelta(hours=0, minutes=21)  
  

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime=now_minus_1_hr.strftime("%Y-%m-%dT%H:%M:%S"),
                event_type=EventType.EHR_REQUEST.value
            )),
        sourcetype="myevent")   
    
    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime=now_minus_20_mins.strftime("%Y-%m-%dT%H:%M:%S"),
                event_type=EventType.EHR_RESPONSE.value
            )),
        sourcetype="myevent")    

    # Act

    test_query = generate_splunk_query_from_report('gp2gp_technical_failure_scenario_report')
    test_query = set_variables_on_query(test_query, {
        "$index$": "test_index",
        "$report_start$": yesterday.strftime("%Y-%m-%dT%H:%M:%S"),
        "$report_end$": tomorrow.strftime("%Y-%m-%dT%H:%M:%S")
    })

    sleep(2)

    telemetry = get_telemetry_from_splunk(savedsearch(test_query), service)
    LOG.info(f'telemetry: {telemetry}')

    # Assert
    assert jq.first(
        '.[] | select( .registrationStatus == "EHR_SENT" ) | select( .slaStatus == "NOT_READY_TO_INTEGRATE_OUTSIDE_SLA" ) | .count', telemetry) == '1'


def test_status_EHR_REQUESTED_sla_NO_EHR_RESPONSE_OUTSIDE_SLA():

    # Arrange

    index = get_or_create_index("test_index", service)

    conversation_id = 'test_status_EHR_REQUESTED_sla_NO_EHR_RESPONSE_OUTSIDE_SLA'

     # test requires a response within 24 hours
    todayMinus24Hours = datetime.today() - timedelta(hours=24, minutes=0)

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime=todayMinus24Hours.strftime("%Y-%m-%dT%H:%M:%S"),
                event_type=EventType.EHR_REQUEST.value
            )),
        sourcetype="myevent")


    # Act

    test_query = generate_splunk_query_from_report('gp2gp_technical_failure_scenario_report')
    test_query = set_variables_on_query(test_query, {
        "$index$": "test_index",
        "$report_start$": todayMinus24Hours.strftime("%Y-%m-%dT%H:%M:%S"),
        "$report_end$": datetime.today().strftime("%Y-%m-%dT%H:%M:%S")
    })

    sleep(2)

    telemetry = get_telemetry_from_splunk(savedsearch(test_query), service)
    LOG.info(f'telemetry: {telemetry}')


    # Assert
    assert jq.first(
        '.[] | select( .registrationStatus == "EHR_REQUESTED" ) | select( .slaStatus == "NO_EHR_RESPONSE_OUTSIDE_SLA" )  | .count', telemetry) == '1'


def test_status_ELIGIBLE_FOR_TRANSFER_sla_NOT_EHR_REQUESTED_OUTSIDE_SLA():

    # Arrange
    index = get_or_create_index("test_index", service)

    conversation_id = 'test_status_ELIGIBLE_FOR_TRANSFER_sla_NOT_EHR_REQUESTED_OUTSIDE_SLA'    

    # reporting window
    yesterday = datetime.today() - timedelta(hours=24)
    tomorrow = datetime.today() + timedelta(hours=24)

    # test requires a datetime less than 20mins
    now_minus_20_mins = datetime.today() - timedelta(hours=0, minutes=21)
    LOG.info(f"now_minus_20_mins: {now_minus_20_mins}")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime=now_minus_20_mins.strftime("%Y-%m-%dT%H:%M:%S"),
                event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                payload=create_transfer_compatibility_payload(
                    internalTransfer=False,
                    transferCompatible=True
                )
            )),
        sourcetype="myevent")

    # Act

    test_query = generate_splunk_query_from_report('gp2gp_technical_failure_scenario_report')
    test_query = set_variables_on_query(test_query, {
        "$index$": "test_index",
        "$report_start$": yesterday.strftime("%Y-%m-%dT%H:%M:%S"),
        "$report_end$": tomorrow.strftime("%Y-%m-%dT%H:%M:%S")
    })

    sleep(2)

    telemetry = get_telemetry_from_splunk(savedsearch(test_query), service)
    LOG.info(f'telemetry: {telemetry}')

    # Assert
    assert jq.first(
        '.[] | select( .registrationStatus == "ELIGIBLE_FOR_TRANSFER" )  | select( .slaStatus == "NOT_EHR_REQUESTED_OUTSIDE_SLA" )  | .count', telemetry) == '1'

def test_status_INTEGRATION_outcome_SUCCESS_should_not_be_in_report():    

      # Arrange

    index = get_or_create_index("test_index", service)

    conversation_id = 'test_status_INTEGRATION_outcome_SUCCESS_should_not_be_in_report'

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id,
                registration_event_datetime="2023-03-10T08:00:00",
                event_type=EventType.EHR_INTEGRATIONS.value,
                payload = create_integration_payload(outcome="INTEGRATED")                
            )),
        sourcetype="myevent")    

    # Act

    test_query = generate_splunk_query_from_report('gp2gp_technical_failure_scenario_report')
    test_query = set_variables_on_query(test_query, {
        "$index$": "test_index",
        "$report_start$": "2023-03-09",
        "$report_end$": "2023-03-29"
    })
    
    sleep(2)

    telemetry = get_telemetry_from_splunk(savedsearch(test_query), service)
    LOG.info(f'telemetry: {telemetry}')

    # Assert
    assert len(telemetry) == 0
   