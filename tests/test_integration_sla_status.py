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
from helpers.datetime_helper import datetime_utc_now
from datetime import datetime, timedelta
from jinja2 import Environment, FileSystemLoader
from tests.test_base import TestBase, EventType


class TestIntegrationSlaStatus(TestBase):

    def test_integrated_under_8_days(self):
        # Arrange

        index_name, index = self.create_index()

        # reporting window
        report_start = datetime_utc_now().date().replace(day=1)
        report_end = datetime_utc_now().date().replace(day=28)

        try:       

            # test requires a date difference of less than 8 days.
            ehr_response_datetime = datetime_utc_now().replace(day=1)
            ehr_integrated_datetime = datetime_utc_now().replace(day=7)        

            # test - #1.a - within SLA - integrated under 8 days

            conversation_id = 'test_integrated_under_8_days'

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversation_id,
                        registration_event_datetime=ehr_response_datetime.strftime("%Y-%m-%dT%H:%M:%S%z"),
                        event_type=EventType.EHR_RESPONSES.value                    
                    )),
                sourcetype="myevent")
            
            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversation_id,
                        registration_event_datetime=ehr_integrated_datetime.strftime("%Y-%m-%dT%H:%M:%S%z"),
                        event_type=EventType.EHR_INTEGRATIONS.value                    
                    )),
                sourcetype="myevent")
            
            # test - #1.b - outside SLA - integrated over 8 days     

            conversation_id = 'test_integrated_over_8_days'

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversation_id,
                        registration_event_datetime=datetime_utc_now().strftime("%Y-%m-%dT%H:%M:%S%z"),
                        event_type=EventType.EHR_RESPONSES.value                    
                    )),
                sourcetype="myevent")
            
            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversation_id,
                        registration_event_datetime=(
                                datetime_utc_now() + timedelta(days=9)
                        ).strftime("%Y-%m-%dT%H:%M:%S%z"),
                        event_type=EventType.EHR_INTEGRATIONS.value                    
                    )),
                sourcetype="myevent")
        
            # Act

            test_query = self.get_search('gp2gp_integration_sla_status')
            test_query = set_variables_on_query(test_query, {
                "$index$": index_name,
                "$report_start$": report_start.strftime("%Y-%m-%d"),
                "$report_end$": report_end.strftime("%Y-%m-%d")
            })

            sleep(2)

            telemetry = get_telemetry_from_splunk(self.savedsearch(test_query), self.splunk_service)
            self.LOG.info(f'telemetry: {telemetry}')

            # Assert
            assert jq.first(
                '.[] ' +
                '| select( .total_integrated_under_8_days=="1" )', telemetry)

        finally:
            self.delete_index(index_name)

    def test_integrated_over_8_days(self):
        # Arrange

        index_name, index = self.create_index()

        # reporting window
        report_start = datetime_utc_now().date().replace(day=1)
        report_end = datetime_utc_now().date().replace(day=28)

        try:              

            # test - #1.a - outside SLA - integrated over 8 days     

            conversation_id = 'test_integrated_over_8_days'

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversation_id,
                        registration_event_datetime=datetime_utc_now().strftime("%Y-%m-%dT%H:%M:%S%z"),
                        event_type=EventType.EHR_RESPONSES.value                    
                    )),
                sourcetype="myevent")
            
            # registration_event_datetime must be over 8 days from EHR_RESPONSE event datetime.
            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversation_id,
                        registration_event_datetime=(
                                datetime_utc_now() + timedelta(days=9)
                        ).strftime("%Y-%m-%dT%H:%M:%S%z"),
                        event_type=EventType.EHR_INTEGRATIONS.value                    
                    )),
                sourcetype="myevent")

            # test - #1.b - within SLA - integrated under 8 days

            conversation_id = 'test_integrated_under_8_days'

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversation_id,
                        registration_event_datetime=datetime_utc_now().strftime("%Y-%m-%dT%H:%M:%S%z"),
                        event_type=EventType.EHR_RESPONSES.value                    
                    )),
                sourcetype="myevent")
            
            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversation_id,
                        registration_event_datetime=(
                                datetime_utc_now() + timedelta(days=7)
                        ).strftime("%Y-%m-%dT%H:%M:%S%z"),
                        event_type=EventType.EHR_INTEGRATIONS.value                    
                    )),
                sourcetype="myevent")
            
        
        
            # Act

            test_query = self.get_search('gp2gp_integration_sla_status')
            test_query = set_variables_on_query(test_query, {
                "$index$": index_name,
                "$report_start$": report_start.strftime("%Y-%m-%d"),
                "$report_end$": report_end.strftime("%Y-%m-%d")
            })

            sleep(2)

            telemetry = get_telemetry_from_splunk(self.savedsearch(test_query), self.splunk_service)
            self.LOG.info(f'telemetry: {telemetry}')

            # Assert
            assert jq.first(
                '.[] ' +
                '| select( .total_integrated_over_8_days=="1" )', telemetry)

        finally:
            self.delete_index(index_name)


    def test_not_integrated_over_8_days(self):
        # Arrange

        index_name, index = self.create_index()

        # reporting window
        report_start = datetime_utc_now().date().replace(day=1)
        report_end = datetime_utc_now().date().replace(day=28)

        try:              

            # test - #1.a - outside SLA - not integrated over 8 days

            conversation_id = 'test_not_integrated_over_8_days'

            # registration_event_datetime must be more than 8 days from now
            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversation_id,
                        registration_event_datetime=(
                                datetime_utc_now() - timedelta(days=9)
                        ).strftime("%Y-%m-%dT%H:%M:%S%z"),
                        event_type=EventType.EHR_RESPONSES.value                    
                    )),
                sourcetype="myevent")
            
            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversation_id,
                        registration_event_datetime=(datetime_utc_now()).strftime("%Y-%m-%dT%H:%M:%S%z"),
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
                        registration_event_datetime=(
                                datetime_utc_now() - timedelta(days=2)
                        ).strftime("%Y-%m-%dT%H:%M:%S%z"),
                        event_type=EventType.EHR_RESPONSES.value                    
                    )),
                sourcetype="myevent")
                    
            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversation_id,
                        registration_event_datetime=datetime_utc_now().strftime("%Y-%m-%dT%H:%M:%S%z"),
                        event_type=EventType.READY_TO_INTEGRATE_STATUSES.value                    
                    )),
                sourcetype="myevent")      
            
        
        
            # Act

            test_query = self.get_search('gp2gp_integration_sla_status')
            test_query = set_variables_on_query(test_query, {
                "$index$": index_name,
                "$report_start$": report_start.strftime("%Y-%m-%d"),
                "$report_end$": report_end.strftime("%Y-%m-%d")
            })

            sleep(2)

            telemetry = get_telemetry_from_splunk(self.savedsearch(test_query), self.splunk_service)
            self.LOG.info(f'telemetry: {telemetry}')

            # Assert
            assert jq.first(
                '.[] ' +
                '| select( .total_not_integrated_over_8_days=="1" )', telemetry)

        finally:
            self.delete_index(index_name)


    def test_not_integrated_under_8_days(self):
        # Arrange

        index_name, index = self.create_index()

        # reporting window
        report_start = datetime_utc_now().date().replace(day=1)
        report_end = datetime_utc_now().date().replace(day=28)

        try:              

            # test - #1.a - inside SLA - not integrated under 8 days

            conversation_id = 'test_not_integrated_under_8_days'

            # registration_event_datetime must be less than 8 days from now
            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversation_id,
                        registration_event_datetime=(
                                datetime_utc_now() - timedelta(days=2)
                        ).strftime("%Y-%m-%dT%H:%M:%S%z"),
                        event_type=EventType.EHR_RESPONSES.value                    
                    )),
                sourcetype="myevent")
                    
            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversation_id,
                        registration_event_datetime=datetime_utc_now().strftime("%Y-%m-%dT%H:%M:%S%z"),
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
                        registration_event_datetime=(
                                datetime_utc_now() - timedelta(days=9)
                        ).strftime("%Y-%m-%dT%H:%M:%S%z"),
                        event_type=EventType.EHR_RESPONSES.value                    
                    )),
                sourcetype="myevent")
            
            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversation_id,
                        registration_event_datetime=(datetime_utc_now()).strftime("%Y-%m-%dT%H:%M:%S%z"),
                        event_type=EventType.READY_TO_INTEGRATE_STATUSES.value                    
                    )),
                sourcetype="myevent") 
        
        
            # Act

            test_query = self.get_search('gp2gp_integration_sla_status')
            test_query = set_variables_on_query(test_query, {
                "$index$": index_name,
                "$report_start$": report_start.strftime("%Y-%m-%d"),
                "$report_end$": report_end.strftime("%Y-%m-%d")
            })

            sleep(2)

            telemetry = get_telemetry_from_splunk(self.savedsearch(test_query), self.splunk_service)
            self.LOG.info(f'telemetry: {telemetry}')

            # Assert
            assert jq.first(
                '.[] ' +
                '| select( .total_not_integrated_under_8_days=="1" )', telemetry)

        finally:
            self.delete_index(index_name)