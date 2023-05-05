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
    service.indexes.delete("test_index")

def test_total_transfer_time_outside_sla_24_hours():

   # Arrange

    index = get_or_create_index("test_index", service)    

    # test - #1

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id='outside_sla_24_hours_1',
                registration_event_datetime="2023-03-10T09:00:00",
                event_type= EventType.EHR_RESPONSES.value,
                sendingPracticeSupplierName="EMIS",
                requestingPracticeSupplierName="TPP" 
            )),
    sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id='inside_sla_24_hours_1',
                registration_event_datetime="2023-05-05T10:00:00",#needs to be within 24 hours
                event_type= EventType.EHR_RESPONSES.value,
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
                event_type= EventType.EHR_RESPONSES.value,
                sendingPracticeSupplierName="EMIS",
                requestingPracticeSupplierName="TPP" 
            )),
    sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id='test_2_outside_sla',
                registration_event_datetime="2023-03-15T09:00:00",
                event_type= EventType.READY_TO_INTEGRATE_STATUSES.value,
                sendingPracticeSupplierName="EMIS",
                requestingPracticeSupplierName="TPP"
            )),
    sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id='test_2_inside_sla',
                registration_event_datetime="2023-03-10T09:00:00",
                event_type= EventType.EHR_RESPONSES.value,
                sendingPracticeSupplierName="EMIS",
                requestingPracticeSupplierName="TPP" 
            )),
    sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id='test_2_inside_sla',
                registration_event_datetime="2023-03-10T11:00:00",
                event_type= EventType.READY_TO_INTEGRATE_STATUSES.value,
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
                event_type= EventType.EHR_RESPONSES.value,
                sendingPracticeSupplierName="EMIS",
                requestingPracticeSupplierName="TPP" 
            )),
    sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id='test_3_outside_sla',
                registration_event_datetime="2023-03-15T09:00:00",
                event_type= EventType.READY_TO_INTEGRATE_STATUSES.value,
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
                payload = create_integration_payload(outcome="REJECTED")                
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id='test_3_inside_sla',
                registration_event_datetime="2023-03-10T09:00:00",
                event_type= EventType.EHR_RESPONSES.value,
                sendingPracticeSupplierName="EMIS",
                requestingPracticeSupplierName="TPP" 
            )),
    sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                conversation_id='test_3_inside_sla',
                registration_event_datetime="2023-03-10T11:00:00",
                event_type= EventType.READY_TO_INTEGRATE_STATUSES.value,
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
                payload = create_integration_payload(outcome="INTEGRATED")                
            )),
        sourcetype="myevent")

    

     # Act

    test_query = get_search('gp2gp_sla_outcomes')
    test_query = set_variables_on_query(test_query, {
        "$index$": "test_index",
        "$report_start$": "2023-03-01",
        "$report_end$": "2023-05-31"
    })

    sleep(2)

    telemetry = get_telemetry_from_splunk(savedsearch(test_query), service)
    LOG.info(f'telemetry: {telemetry}')

    # Assert
    assert jq.first(
        '.[] '+
        '| select( .totalTransferTimeOutsideSla24Hours=="3" )'           
        , telemetry)   



