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


def teardown_function():
    """Function delete test_index."""
    service.indexes.delete("test_index_lorenzo")


def test_total_transfer_time_outside_sla_24_hours():

   # Arrange

    # index_name, index = splunk_index.create(service)
    index = get_or_create_index("test_index_lorenzo", service)

     # reporting window
    yesterday = datetime.today() - timedelta(hours=24)
    tomorrow = datetime.today() + timedelta(hours=24)

    # test requires a datetime less than 24hrs
    now_minus_23_hours = datetime.today() - timedelta(hours=23, minutes=0)
    LOG.info(f"now_minus_20_mins: {now_minus_23_hours}")

    # test - #1

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id='outside_sla_24_hours_1',
                registration_event_datetime="2023-03-10T09:00:00",
                event_type=EventType.EHR_RESPONSES.value,
                sendingPracticeSupplierName="EMIS",
                requestingPracticeSupplierName="TPP"
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id='inside_sla_24_hours_1',
                registration_event_datetime=now_minus_23_hours.strftime("%Y-%m-%dT%H:%M:%S"), # needs to be within 24 hours               
                event_type=EventType.EHR_RESPONSES.value,
                sendingPracticeSupplierName="EMIS",
                requestingPracticeSupplierName="TPP"
            )),
        sourcetype="myevent")

    # test - #2

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id='test_2_outside_sla',
                registration_event_datetime="2023-03-10T09:00:00",
                event_type=EventType.EHR_RESPONSES.value,
                sendingPracticeSupplierName="EMIS",
                requestingPracticeSupplierName="TPP"
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id='test_2_outside_sla',
                registration_event_datetime="2023-03-15T09:00:00",
                event_type=EventType.READY_TO_INTEGRATE_STATUSES.value,
                sendingPracticeSupplierName="EMIS",
                requestingPracticeSupplierName="TPP"
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id='test_2_inside_sla',
                registration_event_datetime="2023-03-10T09:00:00",
                event_type=EventType.EHR_RESPONSES.value,
                sendingPracticeSupplierName="EMIS",
                requestingPracticeSupplierName="TPP"
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id='test_2_inside_sla',
                registration_event_datetime="2023-03-10T11:00:00",
                event_type=EventType.READY_TO_INTEGRATE_STATUSES.value,
                sendingPracticeSupplierName="EMIS",
                requestingPracticeSupplierName="TPP"
            )),
        sourcetype="myevent")

    # test - #3

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id='test_3_outside_sla',
                registration_event_datetime="2023-03-10T09:00:00",
                event_type=EventType.EHR_RESPONSES.value,
                sendingPracticeSupplierName="EMIS",
                requestingPracticeSupplierName="TPP"
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id='test_3_outside_sla',
                registration_event_datetime="2023-03-15T09:00:00",
                event_type=EventType.READY_TO_INTEGRATE_STATUSES.value,
                sendingPracticeSupplierName="EMIS",
                requestingPracticeSupplierName="TPP"
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id='test_3_outside_sla',
                registration_event_datetime="2023-03-10T09:00:00",
                event_type=EventType.EHR_INTEGRATIONS.value,
                payload=create_integration_payload(outcome="REJECTED")
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id='test_3_inside_sla',
                registration_event_datetime="2023-03-10T09:00:00",
                event_type=EventType.EHR_RESPONSES.value,
                sendingPracticeSupplierName="EMIS",
                requestingPracticeSupplierName="TPP"
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id='test_3_inside_sla',
                registration_event_datetime="2023-03-10T11:00:00",
                event_type=EventType.READY_TO_INTEGRATE_STATUSES.value,
                sendingPracticeSupplierName="EMIS",
                requestingPracticeSupplierName="TPP"
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id='test_3_inside_sla',
                registration_event_datetime="2023-03-10T09:00:00",
                event_type=EventType.EHR_INTEGRATIONS.value,
                payload=create_integration_payload(outcome="INTEGRATED")
            )),
        sourcetype="myevent")

    # Act

    test_query = get_search('gp2gp_sla_outcomes')
    test_query = set_variables_on_query(test_query, {
        "$index$": "test_index_lorenzo",
        "$report_start$": "2023-03-01",
        "$report_end$": "2023-05-31"
    })

    sleep(2)

    telemetry = get_telemetry_from_splunk(savedsearch(test_query), service)
    LOG.info(f'telemetry: {telemetry}')

    # Assert
    assert jq.first(
        '.[] ' +
        '| select( .totalTransferTimeOutsideSla24Hours=="3" )', telemetry)
    
    # splunk_index.delete(index_name)


def test_ehr_sending_outside_sla():

    # Arrange

    index_name, index = splunk_index.create(service)

    # test requires a datetime less than 20mins
    now_minus_20_mins = datetime.today() - timedelta(hours=0, minutes=15)
    LOG.info(f"now_minus_20_mins: {now_minus_20_mins}")

    # test - #1 - outside sla

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id='test_ehr_sending_outside_sla_1',
                registration_event_datetime="2023-03-10T09:00:00",
                event_type=EventType.EHR_REQUESTS.value,
                sendingPracticeSupplierName="EMIS",
                requestingPracticeSupplierName="TPP"
            )),
        sourcetype="myevent")

    # test - #2 - inside sla

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id='test_ehr_sending_outside_sla_2',
                registration_event_datetime=now_minus_20_mins.strftime(
                    "%Y-%m-%dT%H:%M:%S"),
                event_type=EventType.EHR_REQUESTS.value,
                sendingPracticeSupplierName="EMIS",
                requestingPracticeSupplierName="TPP"
            )),
        sourcetype="myevent")

    # test - #3 - outside sla READY_TO_INTEGRATE

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id='test_ehr_sending_outside_sla_ready_to_integrate',
                registration_event_datetime="2023-03-10T09:00:00",
                event_type=EventType.EHR_REQUESTS.value,
                sendingPracticeSupplierName="EMIS",
                requestingPracticeSupplierName="TPP"
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id='test_ehr_sending_outside_sla_ready_to_integrate',
                registration_event_datetime="2023-03-10T10:00:00",
                event_type=EventType.EHR_RESPONSES.value,
                sendingPracticeSupplierName="EMIS",
                requestingPracticeSupplierName="TPP"
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id='test_ehr_sending_outside_sla_ready_to_integrate',
                registration_event_datetime="2023-03-10T11:00:00",
                event_type=EventType.READY_TO_INTEGRATE_STATUSES.value,
                sendingPracticeSupplierName="EMIS",
                requestingPracticeSupplierName="TPP"
            )),
        sourcetype="myevent")

    # test - #4 - inside sla READY_TO_INTEGRATE

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id='test_ehr_sending_inside_sla_ready_to_integrate',
                registration_event_datetime="2023-03-10T09:00:00",
                event_type=EventType.EHR_REQUESTS.value,
                sendingPracticeSupplierName="EMIS",
                requestingPracticeSupplierName="TPP"
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id='test_ehr_sending_inside_sla_ready_to_integrate',
                registration_event_datetime="2023-03-10T09:05:00",
                event_type=EventType.EHR_RESPONSES.value,
                sendingPracticeSupplierName="EMIS",
                requestingPracticeSupplierName="TPP"
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id='test_ehr_sending_inside_sla_ready_to_integrate',
                registration_event_datetime="2023-03-10T10:00:00",
                event_type=EventType.READY_TO_INTEGRATE_STATUSES.value,
                sendingPracticeSupplierName="EMIS",
                requestingPracticeSupplierName="TPP"
            )),
        sourcetype="myevent")

    # test - #5 - inside sla INTEGRATED

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id='test_ehr_sending_inside_sla_integrated',
                registration_event_datetime="2023-03-10T09:00:00",
                event_type=EventType.EHR_REQUESTS.value,
                sendingPracticeSupplierName="EMIS",
                requestingPracticeSupplierName="TPP"
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id='test_ehr_sending_inside_sla_integrated',
                registration_event_datetime="2023-03-10T09:05:00",
                event_type=EventType.EHR_RESPONSES.value,
                sendingPracticeSupplierName="EMIS",
                requestingPracticeSupplierName="TPP"
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id='test_ehr_sending_inside_sla_integrated',
                registration_event_datetime="2023-03-10T10:01:00",
                event_type=EventType.READY_TO_INTEGRATE_STATUSES.value,
                sendingPracticeSupplierName="EMIS",
                requestingPracticeSupplierName="TPP"
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id='test_ehr_sending_inside_sla_integrated',
                registration_event_datetime="2023-03-10T10:30:00",
                event_type=EventType.EHR_INTEGRATIONS.value,
                payload=create_integration_payload(outcome="INTEGRATED")
            )),
        sourcetype="myevent")

    # test - #6 - outside sla INTEGRATED

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id='test_ehr_sending_outside_sla_integrated',
                registration_event_datetime="2023-03-10T09:00:00",
                event_type=EventType.EHR_REQUESTS.value,
                sendingPracticeSupplierName="EMIS",
                requestingPracticeSupplierName="TPP"
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id='test_ehr_sending_outside_sla_integrated',
                registration_event_datetime="2023-03-10T10:00:00",
                event_type=EventType.EHR_RESPONSES.value,
                sendingPracticeSupplierName="EMIS",
                requestingPracticeSupplierName="TPP"
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id='test_ehr_sending_outside_sla_integrated',
                registration_event_datetime="2023-03-10T10:01:00",
                event_type=EventType.READY_TO_INTEGRATE_STATUSES.value,
                sendingPracticeSupplierName="EMIS",
                requestingPracticeSupplierName="TPP"
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id='test_ehr_sending_outside_sla_integrated',
                registration_event_datetime="2023-03-10T10:30:00",
                event_type=EventType.EHR_INTEGRATIONS.value,
                payload=create_integration_payload(outcome="INTEGRATED")
            )),
        sourcetype="myevent")

    # test #7 - EHR_SENT - outside sla

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id='test_ehr_sending_outside_sla_ehr_sent',
                registration_event_datetime="2023-03-10T09:00:00",
                event_type=EventType.EHR_REQUESTS.value,
                sendingPracticeSupplierName="EMIS",
                requestingPracticeSupplierName="TPP"
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id='test_ehr_sending_outside_sla_ehr_sent',
                registration_event_datetime="2023-03-10T10:00:00",
                event_type=EventType.EHR_RESPONSES.value,
                sendingPracticeSupplierName="EMIS",
                requestingPracticeSupplierName="TPP"
            )),
        sourcetype="myevent")

    # test #8 - EHR_SENT - inside sla

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id='test_ehr_sending_inside_sla_ehr_sent',
                registration_event_datetime="2023-03-10T09:00:00",
                event_type=EventType.EHR_REQUESTS.value,
                sendingPracticeSupplierName="EMIS",
                requestingPracticeSupplierName="TPP"
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id='test_ehr_sending_inside_sla_ehr_sent',
                registration_event_datetime="2023-03-10T09:15:00",
                event_type=EventType.EHR_RESPONSES.value,
                sendingPracticeSupplierName="EMIS",
                requestingPracticeSupplierName="TPP"
            )),
        sourcetype="myevent")

    # Act

    test_query = get_search('gp2gp_sla_outcomes')
    test_query = set_variables_on_query(test_query, {
        "$index$": index_name,
        "$report_start$": "2023-03-01",
        "$report_end$": "2023-03-31"
    })

    sleep(2)

    telemetry = get_telemetry_from_splunk(savedsearch(test_query), service)
    LOG.info(f'telemetry: {telemetry}')

    # Assert
    assert jq.first(
        '.[] ' +
        '| select( .total_ehr_sending_outside_sla=="4" )', telemetry)
    
    splunk_index.delete(index_name)


def test_ehr_requesting_outside_sla():

    # Arrange

    index_name, index = splunk_index.create(service)

    # test #1.a - Eligibile for transfer outside SLA

    index.submit(
        json.dumps(
            create_sample_event(
                "test_ehr_requesting_outside_sla_test#1.a",
                registration_event_datetime="2023-03-10T09:15:00",
                event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                payload=create_transfer_compatibility_payload(
                    internalTransfer=False,
                    transferCompatible=True
                )
            )),
        sourcetype="myevent")

    # test #1.b - Eligibile for transfer inside SLA

    # test requires a datetime less than 20mins
    now_minus_20_mins = datetime.today() - timedelta(hours=0, minutes=15)
    LOG.info(f"now_minus_20_mins: {now_minus_20_mins}")

    index.submit(
        json.dumps(
            create_sample_event(
                "test_ehr_requesting_outside_sla_test#1.b",
                registration_event_datetime=now_minus_20_mins.strftime(
                    "%Y-%m-%dT%H:%M:%S"),
                event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                payload=create_transfer_compatibility_payload(
                    internalTransfer=False,
                    transferCompatible=True
                )
            )),
        sourcetype="myevent")

    # test #2.a - READY_TO_INTEGRATE outside SLA

    conversation_id = 'test_ehr_requesting_outside_sla_test#2.a'

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id=conversation_id,
                registration_event_datetime="2023-03-10T09:00:00",
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
                conversation_id=conversation_id,
                registration_event_datetime="2023-03-10T09:30:00",
                event_type=EventType.EHR_REQUESTS.value,
                sendingPracticeSupplierName="EMIS",
                requestingPracticeSupplierName="TPP"
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id=conversation_id,
                registration_event_datetime="2023-03-10T10:00:00",
                event_type=EventType.READY_TO_INTEGRATE_STATUSES.value,
                sendingPracticeSupplierName="EMIS",
                requestingPracticeSupplierName="TPP"
            )),
        sourcetype="myevent")

    # test #2.b - READY_TO_INTEGRATE inside SLA

    conversation_id = 'test_ehr_requesting_inside_sla_test#2.b'

    # test requires a datetime less than 20mins
    now_minus_20_mins = datetime.today() - timedelta(hours=0, minutes=15)
    LOG.info(f"now_minus_20_mins: {now_minus_20_mins}")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id=conversation_id,
                registration_event_datetime=datetime.today().strftime("%Y-%m-%dT%H:%M:%S"),
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
                conversation_id=conversation_id,
                registration_event_datetime=now_minus_20_mins.strftime(
                    "%Y-%m-%dT%H:%M:%S"),
                event_type=EventType.EHR_REQUESTS.value,
                sendingPracticeSupplierName="EMIS",
                requestingPracticeSupplierName="TPP"
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id=conversation_id,
                registration_event_datetime="2023-03-10T10:00:00",
                event_type=EventType.READY_TO_INTEGRATE_STATUSES.value,
                sendingPracticeSupplierName="EMIS",
                requestingPracticeSupplierName="TPP"
            )),
        sourcetype="myevent")

    # test #3.a - INTEGRATED outside SLA

    conversation_id = 'test_ehr_requesting_outside_sla_test#3.a'

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id=conversation_id,
                registration_event_datetime="2023-03-10T09:00:00",
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
                conversation_id=conversation_id,
                registration_event_datetime="2023-03-10T09:30:00",
                event_type=EventType.EHR_REQUESTS.value,
                sendingPracticeSupplierName="EMIS",
                requestingPracticeSupplierName="TPP"
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id=conversation_id,
                registration_event_datetime="2023-03-10T10:00:00",
                event_type=EventType.EHR_INTEGRATIONS.value,
                sendingPracticeSupplierName="EMIS",
                requestingPracticeSupplierName="TPP"
            )),
        sourcetype="myevent")

    # test #3.b - INTEGRATED inside SLA

    conversation_id = 'test_ehr_requesting_outside_sla_test#3.b'

    # test requires a datetime less than 20mins
    now_minus_20_mins = datetime.today() - timedelta(hours=0, minutes=15)
    LOG.info(f"now_minus_20_mins: {now_minus_20_mins}")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id=conversation_id,
                registration_event_datetime=datetime.today().strftime("%Y-%m-%dT%H:%M:%S"),
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
                conversation_id=conversation_id,
                registration_event_datetime=now_minus_20_mins.strftime(
                    "%Y-%m-%dT%H:%M:%S"),
                event_type=EventType.EHR_REQUESTS.value,
                sendingPracticeSupplierName="EMIS",
                requestingPracticeSupplierName="TPP"
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id=conversation_id,
                registration_event_datetime="2023-03-10T10:00:00",
                event_type=EventType.EHR_INTEGRATIONS.value,
                sendingPracticeSupplierName="EMIS",
                requestingPracticeSupplierName="TPP"
            )),
        sourcetype="myevent")

    # test #4.a - EHR_SENT outside SLA

    conversation_id = 'test_ehr_requesting_outside_sla_test#4.a'

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id=conversation_id,
                registration_event_datetime="2023-03-10T09:00:00",
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
                conversation_id=conversation_id,
                registration_event_datetime="2023-03-10T09:30:00",
                event_type=EventType.EHR_REQUESTS.value,
                sendingPracticeSupplierName="EMIS",
                requestingPracticeSupplierName="TPP"
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id=conversation_id,
                registration_event_datetime="2023-03-10T10:00:00",
                event_type=EventType.EHR_RESPONSES.value,
                sendingPracticeSupplierName="EMIS",
                requestingPracticeSupplierName="TPP"
            )),
        sourcetype="myevent")

    # test #4.b - EHR_SENT inside SLA

    conversation_id = 'test_ehr_requesting_outside_sla_test#4.b'

    # test requires a datetime less than 20mins
    now_minus_20_mins = datetime.today() - timedelta(hours=0, minutes=15)
    LOG.info(f"now_minus_20_mins: {now_minus_20_mins}")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id=conversation_id,
                registration_event_datetime=datetime.today().strftime("%Y-%m-%dT%H:%M:%S"),
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
                conversation_id=conversation_id,
                registration_event_datetime=now_minus_20_mins.strftime(
                    "%Y-%m-%dT%H:%M:%S"),
                event_type=EventType.EHR_REQUESTS.value,
                sendingPracticeSupplierName="EMIS",
                requestingPracticeSupplierName="TPP"
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id=conversation_id,
                registration_event_datetime="2023-03-10T10:00:00",
                event_type=EventType.EHR_RESPONSES.value,
                sendingPracticeSupplierName="EMIS",
                requestingPracticeSupplierName="TPP"
            )),
        sourcetype="myevent")

    # test #5.a - EHR_REQUESTED outside SLA

    conversation_id = 'test_ehr_requesting_outside_sla_test#5.a'

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id=conversation_id,
                registration_event_datetime="2023-03-10T09:00:00",
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
                conversation_id=conversation_id,
                registration_event_datetime="2023-03-10T09:30:00",
                event_type=EventType.EHR_REQUESTS.value,
                sendingPracticeSupplierName="EMIS",
                requestingPracticeSupplierName="TPP"
            )),
        sourcetype="myevent")

    # test #5.b - EHR_REQUESTED inside SLA

    conversation_id = 'test_ehr_requesting_outside_sla_test#5.b'

    # test requires a datetime less than 20mins
    now_minus_20_mins = datetime.today() - timedelta(hours=0, minutes=15)
    LOG.info(f"now_minus_20_mins: {now_minus_20_mins}")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id=conversation_id,
                registration_event_datetime=datetime.today().strftime("%Y-%m-%dT%H:%M:%S"),
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
                conversation_id=conversation_id,
                registration_event_datetime=now_minus_20_mins.strftime(
                    "%Y-%m-%dT%H:%M:%S"),
                event_type=EventType.EHR_REQUESTS.value,
                sendingPracticeSupplierName="EMIS",
                requestingPracticeSupplierName="TPP"
            )),
        sourcetype="myevent")

    # Act

    test_query = get_search('gp2gp_sla_outcomes')
    test_query = set_variables_on_query(test_query, {
        "$index$": index_name,
        "$report_start$": "2023-03-01",
        "$report_end$": "2023-03-31"
    })

    sleep(2)

    telemetry = get_telemetry_from_splunk(savedsearch(test_query), service)
    LOG.info(f'telemetry: {telemetry}')

    # Assert
    assert jq.first(
        '.[] ' +
        '| select( .total_ehr_requesting_outside_sla=="5" )', telemetry)
    
    splunk_index.delete(index_name)