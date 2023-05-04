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


def test_total_eligible_for_electronic_transfer():
    
    # Arrange

    index = get_or_create_index("test_index", service)
    

    index.submit(
        json.dumps(
            create_sample_event(
                'test_total_eligible_for_electronic_transfer_1',
                registration_event_datetime="2023-03-10T08:00:00",
                event_type= EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                sendingPracticeSupplierName="EMIS",
                requestingPracticeSupplierName="TPP",
                payload=create_transfer_compatibility_payload(
                    internalTransfer=False,
                    transferCompatible=True,
                    reason="test1"
                )
                
            )),
        sourcetype="myevent")
    
    index.submit(
        json.dumps(
            create_sample_event(
                'test_total_eligible_for_electronic_transfer_2',
                registration_event_datetime="2023-03-10T09:00:00",
                event_type= EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                sendingPracticeSupplierName="EMIS",
                requestingPracticeSupplierName="TPP",
                payload=create_transfer_compatibility_payload(
                    internalTransfer=False,
                    transferCompatible=True,
                    reason="test2"
                )
                
            )),
    sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                'test_total_eligible_for_electronic_transfer_3',
                registration_event_datetime="2023-03-10T10:00:00",
                event_type= EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                sendingPracticeSupplierName="EMIS",
                requestingPracticeSupplierName="TPP",
                payload=create_transfer_compatibility_payload(
                    internalTransfer=True,
                    transferCompatible=True,
                    reason="test1"
                )
                
            )),
    sourcetype="myevent")

   
    # Act

    test_query = get_search('gp2gp_transfer_status_report')
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
        '.[] | select( .total_eligible_for_electronic_transfer == "2" ) ', telemetry)
    
def test_successfully_integrated():

    # Arrange

    index = get_or_create_index("test_index", service)    

    # successfully integrated - #1

    index.submit(
        json.dumps(
            create_sample_event(
                'test_successfully_integrated_1',
                registration_event_datetime="2023-03-10T09:00:00",
                event_type= EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                sendingPracticeSupplierName="EMIS",
                requestingPracticeSupplierName="TPP",
                payload=create_transfer_compatibility_payload(
                    internalTransfer=False,
                    transferCompatible=True,
                    reason="test1"
                )
                
            )),
    sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                'test_successfully_integrated_1',
                registration_event_datetime="2023-03-10T08:00:00",
                event_type=EventType.EHR_INTEGRATIONS.value,
                payload = create_integration_payload(outcome="INTEGRATED")                
            )),
        sourcetype="myevent")  
    
    # successfully integrated - #2

    index.submit(
        json.dumps(
            create_sample_event(
                'test_successfully_integrated_2',
                registration_event_datetime="2023-03-10T09:00:00",
                event_type= EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                sendingPracticeSupplierName="EMIS",
                requestingPracticeSupplierName="TPP",
                payload=create_transfer_compatibility_payload(
                    internalTransfer=False,
                    transferCompatible=True,
                    reason="test1"
                )
                
            )),
    sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                'test_successfully_integrated_2',
                registration_event_datetime="2023-03-10T08:10:00",
                event_type=EventType.EHR_INTEGRATIONS.value,
                payload = create_integration_payload(outcome="INTEGRATED_AND_SUPPRESSED")                
            )),
        sourcetype="myevent")  
    
    # successfully integrated - #3

    index.submit(
        json.dumps(
            create_sample_event(
                'test_successfully_integrated_3',
                registration_event_datetime="2023-03-10T09:00:00",
                event_type= EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                sendingPracticeSupplierName="EMIS",
                requestingPracticeSupplierName="TPP",
                payload=create_transfer_compatibility_payload(
                    internalTransfer=False,
                    transferCompatible=True,
                    reason="test1"
                )
                
            )),
    sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                'test_successfully_integrated_3',
                registration_event_datetime="2023-03-10T08:20:00",
                event_type=EventType.EHR_INTEGRATIONS.value,
                payload = create_integration_payload(outcome="SUPPRESSED_AND_REACTIVATED")                
            )),
        sourcetype="myevent")   

    
    
    # rejected

    index.submit(
        json.dumps(
            create_sample_event(
                'test_successfully_integrated_rejected',
                registration_event_datetime="2023-03-10T09:00:00",
                event_type= EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                sendingPracticeSupplierName="EMIS",
                requestingPracticeSupplierName="TPP",
                payload=create_transfer_compatibility_payload(
                    internalTransfer=False,
                    transferCompatible=True,
                    reason="test1"
                )
                
            )),
    sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                'test_successfully_integrated_rejected',
                registration_event_datetime="2023-03-10T09:00:00",
                event_type=EventType.EHR_INTEGRATIONS.value,
                payload = create_integration_payload(outcome="REJECTED")                
            )),
        sourcetype="myevent") 
    
    # failed to integrate # 1

    index.submit(
        json.dumps(
            create_sample_event(
                'test_successfully_integrated_failed_to_integrate_#1',
                registration_event_datetime="2023-03-10T09:00:00",
                event_type= EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                sendingPracticeSupplierName="EMIS",
                requestingPracticeSupplierName="TPP",
                payload=create_transfer_compatibility_payload(
                    internalTransfer=False,
                    transferCompatible=True,
                    reason="test1"
                )
                
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                'test_successfully_integrated_failed_to_integrate_#1',
                registration_event_datetime="2023-03-10T09:10:00",
                event_type=EventType.EHR_INTEGRATIONS.value,
                payload = create_integration_payload(outcome="FAILED_TO_INTEGRATE")                
            )),
        sourcetype="myevent")  
    
    # failed to integrate # 2

    index.submit(
        json.dumps(
            create_sample_event(
                'test_successfully_integrated_failed_to_integrate_#2',
                registration_event_datetime="2023-03-10T09:00:00",
                event_type= EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                sendingPracticeSupplierName="EMIS",
                requestingPracticeSupplierName="TPP",
                payload=create_transfer_compatibility_payload(
                    internalTransfer=False,
                    transferCompatible=True,
                    reason="test1"
                )
                
            )),
        sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                'test_successfully_integrated_failed_to_integrate_#2',
                registration_event_datetime="2023-03-10T09:10:00",
                event_type=EventType.EHR_INTEGRATIONS.value,
                payload = create_integration_payload(outcome="FAILED_TO_INTEGRATE")                
            )),
        sourcetype="myevent")  

   
    # Act

    test_query = get_search('gp2gp_transfer_status_report')
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
        '.[] '+
        '| select( .total_eligible_for_electronic_transfer=="6" )' +
        '| select( .count_successfully_integrated == "3")' +
        '| select( .percentage_successfully_integrated == "50.00")'        
        , telemetry)
    

def test_rejected():

    # Arrange

    index = get_or_create_index("test_index", service)    

    # successfully integrated - #1

    index.submit(
        json.dumps(
            create_sample_event(
                'test_rejected_1',
                registration_event_datetime="2023-03-10T09:00:00",
                event_type= EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                sendingPracticeSupplierName="EMIS",
                requestingPracticeSupplierName="TPP",
                payload=create_transfer_compatibility_payload(
                    internalTransfer=False,
                    transferCompatible=True,
                    reason="test1"
                )
                
            )),
    sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                'test_rejected_1',
                registration_event_datetime="2023-03-10T08:00:00",
                event_type=EventType.EHR_INTEGRATIONS.value,
                payload = create_integration_payload(outcome="INTEGRATED")                
            )),
        sourcetype="myevent")  
    
    # successfully integrated - #2

    index.submit(
        json.dumps(
            create_sample_event(
                'test_rejected_2',
                registration_event_datetime="2023-03-10T09:00:00",
                event_type= EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                sendingPracticeSupplierName="EMIS",
                requestingPracticeSupplierName="TPP",
                payload=create_transfer_compatibility_payload(
                    internalTransfer=False,
                    transferCompatible=True,
                    reason="test1"
                )
                
            )),
    sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                'test_rejected_2',
                registration_event_datetime="2023-03-10T08:10:00",
                event_type=EventType.EHR_INTEGRATIONS.value,
                payload = create_integration_payload(outcome="INTEGRATED_AND_SUPPRESSED")                
            )),
        sourcetype="myevent")  
    
    # successfully integrated - #3

    index.submit(
        json.dumps(
            create_sample_event(
                'test_rejected_3',
                registration_event_datetime="2023-03-10T09:00:00",
                event_type= EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                sendingPracticeSupplierName="EMIS",
                requestingPracticeSupplierName="TPP",
                payload=create_transfer_compatibility_payload(
                    internalTransfer=False,
                    transferCompatible=True,
                    reason="test1"
                )
                
            )),
    sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                'test_rejected_3',
                registration_event_datetime="2023-03-10T08:20:00",
                event_type=EventType.EHR_INTEGRATIONS.value,
                payload = create_integration_payload(outcome="SUPPRESSED_AND_REACTIVATED")                
            )),
        sourcetype="myevent")   

    
    
    # rejected

    index.submit(
        json.dumps(
            create_sample_event(
                'test_rejected_4',
                registration_event_datetime="2023-03-10T09:00:00",
                event_type= EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                sendingPracticeSupplierName="EMIS",
                requestingPracticeSupplierName="TPP",
                payload=create_transfer_compatibility_payload(
                    internalTransfer=False,
                    transferCompatible=True,
                    reason="test1"
                )
                
            )),
    sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                'test_rejected_4',
                registration_event_datetime="2023-03-10T09:00:00",
                event_type=EventType.EHR_INTEGRATIONS.value,
                payload = create_integration_payload(outcome="REJECTED")                
            )),
        sourcetype="myevent")
   
    # Act

    test_query = get_search('gp2gp_transfer_status_report')
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
        '.[] '+
        '| select( .total_eligible_for_electronic_transfer=="4" )' +
        '| select( .count_rejected == "1")' +
        '| select( .percentage_rejected == "25.00")'        
        , telemetry)
    

def test_awaiting_integration():

    # Arrange

    index = get_or_create_index("test_index", service)    

    # awaiting_integration - #1

    index.submit(
        json.dumps(
            create_sample_event(
                'awaiting_integration_1',
                registration_event_datetime="2023-03-10T09:00:00",
                event_type= EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                sendingPracticeSupplierName="EMIS",
                requestingPracticeSupplierName="TPP",
                payload=create_transfer_compatibility_payload(
                    internalTransfer=False,
                    transferCompatible=True,
                    reason="test1"
                )
                
            )),
    sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                'awaiting_integration_1',
                registration_event_datetime="2023-03-10T09:10:00",
                event_type=EventType.READY_TO_INTEGRATE_STATUSES.value                        
            )),
        sourcetype="myevent")  
    
    # awaiting_integration - #2

    index.submit(
        json.dumps(
            create_sample_event(
                'awaiting_integration_2',
                registration_event_datetime="2023-03-10T09:20:00",
                event_type= EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                sendingPracticeSupplierName="EMIS",
                requestingPracticeSupplierName="TPP",
                payload=create_transfer_compatibility_payload(
                    internalTransfer=False,
                    transferCompatible=True,
                    reason="test1"
                )
                
            )),
    sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                'awaiting_integration_2',
                registration_event_datetime="2023-03-10T09:30:00",
                event_type=EventType.READY_TO_INTEGRATE_STATUSES.value                               
            )),
        sourcetype="myevent")      
    
    # rejected

    index.submit(
        json.dumps(
            create_sample_event(
                'awaiting_integration_3',
                registration_event_datetime="2023-03-10T09:00:00",
                event_type= EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                sendingPracticeSupplierName="EMIS",
                requestingPracticeSupplierName="TPP",
                payload=create_transfer_compatibility_payload(
                    internalTransfer=False,
                    transferCompatible=True,
                    reason="test1"
                )
                
            )),
    sourcetype="myevent")

    index.submit(
        json.dumps(
            create_sample_event(
                'awaiting_integration_3',
                registration_event_datetime="2023-03-10T09:00:00",
                event_type=EventType.EHR_INTEGRATIONS.value,
                payload = create_integration_payload(outcome="REJECTED")                
            )),
        sourcetype="myevent")
   
    # Act

    test_query = get_search('gp2gp_transfer_status_report')
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
        '.[] '+
        '| select( .total_eligible_for_electronic_transfer=="3" )' +
        '| select( .count_awaiting_integration == "2")' +
        '| select( .percentage_awaiting_integration == "66.67")' +
        '| select( .percentage_rejected == "33.33")'        
        , telemetry)   
    
@pytest.mark.skip(reason="work in progress...")
def test_in_progress():

    # Arrange

    index = get_or_create_index("test_index", service)    

    # 

   
   
    # Act

    test_query = get_search('gp2gp_transfer_status_report')
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
        '.[] '+
        '| select( .total_eligible_for_electronic_transfer=="3" )' +
        '| select( .count_awaiting_integration == "2")' +
        '| select( .percentage_awaiting_integration == "66.67")' +
        '| select( .percentage_rejected == "33.33")'        
        , telemetry)   
  