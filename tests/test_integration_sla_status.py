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

def test_integrated_under_8_days():
    # Arrange

    index_name, index = splunk_index.create(service)

    # reporting window
    report_start = datetime.today().date().replace(day=1)
    report_end = datetime.today().date().replace(day=31)

    try:       

        # test requires a date difference of less than 8 days.
        ehr_response_datetime = datetime.now().replace(day=1)
        ehr_integrated_datetime = datetime.now().replace(day=7)        

        # test - #1.a - within SLA - integrated under 8 days

        conversation_id = 'test_integrated_under_8_days'

        index.submit(
            json.dumps(
                create_sample_event(
                    conversation_id=conversation_id,
                    registration_event_datetime=ehr_response_datetime.strftime("%Y-%m-%dT%H:%M:%S"),
                    event_type=EventType.EHR_RESPONSES.value                    
                )),
            sourcetype="myevent")
        
        index.submit(
            json.dumps(
                create_sample_event(
                    conversation_id=conversation_id,
                    registration_event_datetime=ehr_integrated_datetime.strftime("%Y-%m-%dT%H:%M:%S"),
                    event_type=EventType.EHR_INTEGRATIONS.value                    
                )),
            sourcetype="myevent")
        
        # test - #1.b - outside SLA - integrated over 8 days     

        conversation_id = 'test_integrated_over_8_days'

        index.submit(
            json.dumps(
                create_sample_event(
                    conversation_id=conversation_id,
                    registration_event_datetime=datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                    event_type=EventType.EHR_RESPONSES.value                    
                )),
            sourcetype="myevent")
        
        index.submit(
            json.dumps(
                create_sample_event(
                    conversation_id=conversation_id,
                    registration_event_datetime=(datetime.now() + timedelta(days=9)).strftime("%Y-%m-%dT%H:%M:%S"),
                    event_type=EventType.EHR_INTEGRATIONS.value                    
                )),
            sourcetype="myevent")
       
        # Act

        test_query = get_search('gp2gp_integration_sla_status')
        test_query = set_variables_on_query(test_query, {
            "$index$": index_name,
            "$report_start$": report_start.strftime("%Y-%m-%d"),
            "$report_end$": report_end.strftime("%Y-%m-%d")
        })

        sleep(2)

        telemetry = get_telemetry_from_splunk(savedsearch(test_query), service)
        LOG.info(f'telemetry: {telemetry}')

        # Assert
        assert jq.first(
            '.[] ' +
            '| select( .total_integrated_under_8_days=="1" )', telemetry)

    finally:
        splunk_index.delete(index_name)

def test_integrated_over_8_days():
    # Arrange

    index_name, index = splunk_index.create(service)

    # reporting window
    report_start = datetime.today().date().replace(day=1)
    report_end = datetime.today().date().replace(day=31)

    try:              

         # test - #1.a - outside SLA - integrated over 8 days     

        conversation_id = 'test_integrated_over_8_days'

        index.submit(
            json.dumps(
                create_sample_event(
                    conversation_id=conversation_id,
                    registration_event_datetime=datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                    event_type=EventType.EHR_RESPONSES.value                    
                )),
            sourcetype="myevent")
        
        #registration_event_datetime must be over 8 days from EHR_RESPONSE event datetime.        
        index.submit(
            json.dumps(
                create_sample_event(
                    conversation_id=conversation_id,
                    registration_event_datetime=(datetime.now() + timedelta(days=9)).strftime("%Y-%m-%dT%H:%M:%S"), 
                    event_type=EventType.EHR_INTEGRATIONS.value                    
                )),
            sourcetype="myevent")

        # test - #1.b - within SLA - integrated under 8 days

        conversation_id = 'test_integrated_under_8_days'

        index.submit(
            json.dumps(
                create_sample_event(
                    conversation_id=conversation_id,
                    registration_event_datetime=datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                    event_type=EventType.EHR_RESPONSES.value                    
                )),
            sourcetype="myevent")
        
        index.submit(
            json.dumps(
                create_sample_event(
                    conversation_id=conversation_id,
                    registration_event_datetime=(datetime.now() + timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%S"),
                    event_type=EventType.EHR_INTEGRATIONS.value                    
                )),
            sourcetype="myevent")
        
       
       
        # Act

        test_query = get_search('gp2gp_integration_sla_status')
        test_query = set_variables_on_query(test_query, {
            "$index$": index_name,
            "$report_start$": report_start.strftime("%Y-%m-%d"),
            "$report_end$": report_end.strftime("%Y-%m-%d")
        })

        sleep(2)

        telemetry = get_telemetry_from_splunk(savedsearch(test_query), service)
        LOG.info(f'telemetry: {telemetry}')

        # Assert
        assert jq.first(
            '.[] ' +
            '| select( .total_integrated_over_8_days=="1" )', telemetry)

    finally:
        splunk_index.delete(index_name)


def test_not_integrated_over_8_days():
    # Arrange

    index_name, index = splunk_index.create(service)

    # reporting window
    report_start = datetime.today().date().replace(day=1)
    report_end = datetime.today().date().replace(day=31)

    try:              

         # test - #1.a - outside SLA - not integrated over 8 days

        conversation_id = 'test_not_integrated_over_8_days'

        # registration_event_datetime must be more than 8 days from now
        index.submit(
            json.dumps(
                create_sample_event(
                    conversation_id=conversation_id,
                    registration_event_datetime=(datetime.now() - timedelta(days=9)).strftime("%Y-%m-%dT%H:%M:%S"),
                    event_type=EventType.EHR_RESPONSES.value                    
                )),
            sourcetype="myevent")
        
        index.submit(
            json.dumps(
                create_sample_event(
                    conversation_id=conversation_id,
                    registration_event_datetime=(datetime.now()).strftime("%Y-%m-%dT%H:%M:%S"),
                    event_type=EventType.READY_TO_INTEGRATE_STATUSES.value                    
                )),
            sourcetype="myevent")  

        # test - #1.b - within SLA - no integrated under 8 days 

        conversation_id = 'test_not_integrated_under_8_days'

        # registration_event_datetime must be less than 8 days from now
        index.submit(
            json.dumps(
                create_sample_event(
                    conversation_id=conversation_id,
                    registration_event_datetime=(datetime.now() - timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%S"),
                    event_type=EventType.EHR_RESPONSES.value                    
                )),
            sourcetype="myevent")
                
        index.submit(
            json.dumps(
                create_sample_event(
                    conversation_id=conversation_id,
                    registration_event_datetime=datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), 
                    event_type=EventType.READY_TO_INTEGRATE_STATUSES.value                    
                )),
            sourcetype="myevent")      
        
       
       
        # Act

        test_query = get_search('gp2gp_integration_sla_status')
        test_query = set_variables_on_query(test_query, {
            "$index$": index_name,
            "$report_start$": report_start.strftime("%Y-%m-%d"),
            "$report_end$": report_end.strftime("%Y-%m-%d")
        })

        sleep(2)

        telemetry = get_telemetry_from_splunk(savedsearch(test_query), service)
        LOG.info(f'telemetry: {telemetry}')

        # Assert
        assert jq.first(
            '.[] ' +
            '| select( .total_not_integrated_over_8_days=="1" )', telemetry)

    finally:
        splunk_index.delete(index_name)


def test_not_integrated_under_8_days():
    # Arrange

    index_name, index = splunk_index.create(service)

    # reporting window
    report_start = datetime.today().date().replace(day=1)
    report_end = datetime.today().date().replace(day=31)

    try:              

         # test - #1.a - inside SLA - not integrated under 8 days

        conversation_id = 'test_not_integrated_under_8_days'

        # registration_event_datetime must be less than 8 days from now
        index.submit(
            json.dumps(
                create_sample_event(
                    conversation_id=conversation_id,
                    registration_event_datetime=(datetime.now() - timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%S"),
                    event_type=EventType.EHR_RESPONSES.value                    
                )),
            sourcetype="myevent")
                
        index.submit(
            json.dumps(
                create_sample_event(
                    conversation_id=conversation_id,
                    registration_event_datetime=datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), 
                    event_type=EventType.READY_TO_INTEGRATE_STATUSES.value                    
                )),
            sourcetype="myevent") 

 

        # test - #1.b - within SLA - no integrated over 8 days 

     
        conversation_id = 'test_not_integrated_over_8_days'

        # registration_event_datetime must be more than 8 days from now
        index.submit(
            json.dumps(
                create_sample_event(
                    conversation_id=conversation_id,
                    registration_event_datetime=(datetime.now() - timedelta(days=9)).strftime("%Y-%m-%dT%H:%M:%S"),
                    event_type=EventType.EHR_RESPONSES.value                    
                )),
            sourcetype="myevent")
        
        index.submit(
            json.dumps(
                create_sample_event(
                    conversation_id=conversation_id,
                    registration_event_datetime=(datetime.now()).strftime("%Y-%m-%dT%H:%M:%S"),
                    event_type=EventType.READY_TO_INTEGRATE_STATUSES.value                    
                )),
            sourcetype="myevent") 
       
       
        # Act

        test_query = get_search('gp2gp_integration_sla_status')
        test_query = set_variables_on_query(test_query, {
            "$index$": index_name,
            "$report_start$": report_start.strftime("%Y-%m-%d"),
            "$report_end$": report_end.strftime("%Y-%m-%d")
        })

        sleep(2)

        telemetry = get_telemetry_from_splunk(savedsearch(test_query), service)
        LOG.info(f'telemetry: {telemetry}')

        # Assert
        assert jq.first(
            '.[] ' +
            '| select( .total_not_integrated_under_8_days=="1" )', telemetry)

    finally:
        splunk_index.delete(index_name)