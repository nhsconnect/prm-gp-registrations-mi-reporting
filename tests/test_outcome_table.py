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
from datetime import datetime, timedelta, date
from jinja2 import Environment, FileSystemLoader
from .base_test_report import splunk_index
from helpers.date_helper import create_date_time

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
    '''
    STATUS = EHR_SENT AND TOTAL TRANSFER TIME OUTSIDE SLA 24 HOURS = true
    '''

    # Arrange
    index_name, index = splunk_index.create(service)

    # reporting window       
    report_start = datetime.today().date().replace(day=1)   
    report_end = datetime.today().date().replace(day=31)    
    
    try:

         # test requires a datetime less than 24hrs
        now_minus_23_hours = datetime.today() - timedelta(hours=23, minutes=0)
        LOG.info(f"now_minus_23_hours: {now_minus_23_hours}")

        now_minus_25_hours = datetime.today() - timedelta(hours=25, minutes=0)
        LOG.info(f"now_minus_25_hours: {now_minus_25_hours}")  

        # Outside SLA
        index.submit(
            json.dumps(
                create_sample_event(
                    conversation_id='outside_sla_24_hours',
                    registration_event_datetime=now_minus_25_hours.strftime("%Y-%m-%dT%H:%M:%S"), # needs to be outside 24 hours
                    event_type=EventType.EHR_RESPONSES.value,
                    sendingPracticeSupplierName="EMIS",
                    requestingPracticeSupplierName="TPP"
                )),
            sourcetype="myevent")

        # Inside SLA

        index.submit(
            json.dumps(
                create_sample_event(
                    conversation_id='inside_sla_24_hours',
                    registration_event_datetime=now_minus_23_hours.strftime("%Y-%m-%dT%H:%M:%S"), # needs to be within 24 hours
                    event_type=EventType.EHR_RESPONSES.value,
                    sendingPracticeSupplierName="EMIS",
                    requestingPracticeSupplierName="TPP"
                )),
            sourcetype="myevent")

        # Act

        test_query = get_search('gp2gp_outcome_report')
        test_query = set_variables_on_query(test_query, {
            "$index$": index_name,
            "$report_start$": report_start.strftime("%Y-%m-%d"),
            "$report_end$": report_end.strftime("%Y-%m-%d")
        })

        sleep(2)

        telemetry = get_telemetry_from_splunk(savedsearch(test_query), service)
        LOG.info(f'telemetry: {telemetry}')

        # Assert - check that there is 1 event each (count), 3 events in total (totalCount) and the percentage is 33.3
        assert jq.first(
            '.[] | select( .outcome == "TECHNICAL_FAILURE" ) | select( .count == "1" )', telemetry)
      

    finally:        
        splunk_index.delete(index_name)


def test_outcome_in_progress_1():
    '''
    This test requires EHR_REQUEST and EHR_RESPONSE events within 24 hours to get an EHR_REQUESTING_OUTSIDE_SLA = false (test 1.a).
    Test (1.b) is there to validate the test 1.a is the only one with EHR_REQUESTING_OUTSIDE_SLA = false.
    Registraion status for this test should be EHR_SENT.    
    '''

    # Arrange

    index_name, index = splunk_index.create(service)   

    # reporting window       
    report_start = datetime.today().date().replace(day=1)   
    report_end = datetime.today().date().replace(day=31)     

    try:

        # test 1.a - inside SLA

        conversation_id = 'test_outcome_in_progress_inside_sla'

        # test requires a datetime less than 24hrs
        now_minus_23_hours = datetime.today() - timedelta(hours=23, minutes=0)
        LOG.info(f"now_minus_23_hours: {now_minus_23_hours}")

        index.submit(
            json.dumps(
                create_sample_event(
                    conversation_id=conversation_id,
                    registration_event_datetime="2023-05-10T04:00:00",
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
                    registration_event_datetime="2023-05-10T05:00:00",
                    event_type=EventType.EHR_REQUESTS.value
                )),
            sourcetype="myevent")

        index.submit(
            json.dumps(
                create_sample_event(
                    conversation_id=conversation_id,
                    registration_event_datetime=now_minus_23_hours.strftime("%Y-%m-%dT%H:%M:%S"),
                    event_type=EventType.EHR_RESPONSES.value
                )),
            sourcetype="myevent")
        
        # test 1.b - outside SLA

        conversation_id = 'test_outcome_in_progress_outside_sla'

        index.submit(
            json.dumps(
                create_sample_event(
                    conversation_id=conversation_id,
                    registration_event_datetime="2023-05-01T04:00:00",
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
                    registration_event_datetime="2023-05-01T05:00:00",
                    event_type=EventType.EHR_REQUESTS.value
                )),
            sourcetype="myevent")

        index.submit(
            json.dumps(
                create_sample_event(
                    conversation_id=conversation_id,
                    registration_event_datetime="2023-05-05T07:00:00",
                    event_type=EventType.EHR_RESPONSES.value
                )),
            sourcetype="myevent")

        # Act

        test_query = get_search('gp2gp_outcome_report')
        test_query = set_variables_on_query(test_query, {
            "$index$": index_name,
            "$report_start$": report_start.strftime("%Y-%m-%d"),
            "$report_end$": report_end.strftime("%Y-%m-%d")
        })

        sleep(2)

        telemetry = get_telemetry_from_splunk(savedsearch(test_query), service)
        LOG.info(f'telemetry: {telemetry}')

        # Assert - check that there is 1 event each (count), 3 events in total (totalCount) and the percentage is 33.3
        assert jq.first(
            '.[] | select( .outcome == "IN_PROGRESS" ) | select( .count == "1" )', telemetry)


    finally:
        splunk_index.delete(index_name)

def test_outcome_technical_failure_3():
    '''   
    Registraion status for this test should be EHR_REQUESTED. EHR_SENDING_OUTSIDE_SLA = true.
    Note: SLA for this is 20mins
    '''

    # Arrange

    index_name, index = splunk_index.create(service)   

    # reporting window       
    report_start = datetime.today().date().replace(day=1)   
    report_end = datetime.today().date().replace(day=31)     
   

    try:

        # test 1.a - outside SLA

        conversation_id = 'test_outcome_technical_failure_3_outside_sla'      

       
        index.submit(
            json.dumps(
                create_sample_event(
                    conversation_id=conversation_id,
                    registration_event_datetime="2023-05-02T10:00:00",
                    event_type=EventType.EHR_REQUESTS.value
                )),
            sourcetype="myevent")      
        
        # test 1.b - inside SLA

        # Notes-
        # use new create_date_time helper to generate event requested datetime inside the sla of 20mins
        # test should still pass as only looking for outside SLA.

        # 

        conversation_id = 'test_outcome_technical_failure_3_inside_sla'   

         # test requires a datetime less than 24hrs
        now_minus_18_mins = datetime.today() - timedelta(hours=0, minutes=18)
        LOG.info(f"now_minus_18_mins: {now_minus_18_mins}")   

       
        index.submit(
            json.dumps(
                create_sample_event(
                    conversation_id=conversation_id,
                    registration_event_datetime=now_minus_18_mins.strftime("%Y-%m-%dT%H:%M:%S"),
                    event_type=EventType.EHR_REQUESTS.value
                )),
            sourcetype="myevent") 
        

        # Act

        test_query = get_search('gp2gp_outcome_report')
        test_query = set_variables_on_query(test_query, {
            "$index$": index_name,
            "$report_start$": report_start.strftime("%Y-%m-%d"),
            "$report_end$": report_end.strftime("%Y-%m-%d")
        })

        sleep(2)

        telemetry = get_telemetry_from_splunk(savedsearch(test_query), service)
        LOG.info(f'telemetry: {telemetry}')

        # Assert - 
        assert jq.first(
            '.[] | select( .outcome == "TECHNICAL_FAILURE" ) | select( .count == "1" )', telemetry)


    finally:
        splunk_index.delete(index_name)

def test_outcome_in_progress_2():
    '''
    This test requires EHR_REQUEST and EHR_RESPONSE events within 24 hours to get an EHR_REQUESTING_OUTSIDE_SLA = false (test 1.a).
    Test (1.b) is there to validate the test 1.a is the only one with EHR_REQUESTING_OUTSIDE_SLA = false.
    Registraion status for this test should be EHR_SENT.    
    '''

    # Arrange

    index_name, index = splunk_index.create(service)   

    # reporting window       
    report_start = datetime.today().date().replace(day=1)   
    report_end = datetime.today().date().replace(day=31)     

    try:

        # test 1.a - inside SLA

        conversation_id = 'test_outcome_in_progress_2_inside_sla'

        # test requires a datetime less than 20mins
        now_minus_18_mins = datetime.today() - timedelta(hours=0, minutes=18)
        LOG.info(f"now_minus_18_mins: {now_minus_18_mins}")       

        index.submit(
            json.dumps(
                create_sample_event(
                    conversation_id=conversation_id,
                    registration_event_datetime=now_minus_18_mins.strftime("%Y-%m-%dT%H:%M:%S"),
                    event_type=EventType.EHR_REQUESTS.value
                )),
            sourcetype="myevent")       
        
        # test 1.b - outside SLA

        conversation_id = 'test_outcome_in_progress_2_outside_sla'       

        index.submit(
            json.dumps(
                create_sample_event(
                    conversation_id=conversation_id,
                    registration_event_datetime="2023-05-01T05:00:00",
                    event_type=EventType.EHR_REQUESTS.value
                )),
            sourcetype="myevent")       

        # Act

        test_query = get_search('gp2gp_outcome_report')
        test_query = set_variables_on_query(test_query, {
            "$index$": index_name,
            "$report_start$": report_start.strftime("%Y-%m-%d"),
            "$report_end$": report_end.strftime("%Y-%m-%d")
        })

        sleep(2)

        telemetry = get_telemetry_from_splunk(savedsearch(test_query), service)
        LOG.info(f'telemetry: {telemetry}')

        # Assert -
        assert jq.first(
            '.[] | select( .outcome == "IN_PROGRESS" ) | select( .count == "1" )', telemetry)


    finally:
        splunk_index.delete(index_name)