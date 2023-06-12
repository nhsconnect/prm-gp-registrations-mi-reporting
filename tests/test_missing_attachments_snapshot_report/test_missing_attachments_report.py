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
from tests.test_base import TestBase, EventType
from helpers.date_helper import create_date_time


class TestInternalTransfers(TestBase):

    '''a count where the status is READY_TO_INTEGRATE or INTEGRATION.'''

    def test_total_records_transfered(self):        

        # reporting window
        report_start = datetime.today().date().replace(day=1)
        report_end = datetime.today().date().replace(day=30)

        try:
            # Arrange
            index_name, index = self.create_index()            

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_total_records_transfered_#1',
                        registration_event_datetime=create_date_time(date=report_start,time="09:00:00"),
                        event_type=EventType.EHR_INTEGRATIONS.value,
                        payload=create_integration_payload(outcome="INTEGRATED")
                    )),
                sourcetype="myevent")
           
            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_total_records_transfered_#2',
                        registration_event_datetime=create_date_time(date=report_start,time="10:00:00"),
                        event_type=EventType.READY_TO_INTEGRATE_STATUSES.value                       
                    )),
                sourcetype="myevent")
            
            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_total_records_transfered_#3',
                        registration_event_datetime=create_date_time(date=report_start,time="11:00:00"),
                        event_type=EventType.ERRORS.value,
                        payload=create_error_payload(
                            errorCode="99",
                            errorDescription="Error with EHR Response",
                            failurePoint=EventType.EHR_RESPONSES.value
                        )
                        
                    )),
                sourcetype="myevent")
            
            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_total_records_transfered_#4',                       
                        registration_event_datetime=create_date_time(date=report_start,time="12:00:00"),
                        event_type=EventType.EHR_REQUESTS.value                        
                    )),
                sourcetype="myevent")

            # Act

            test_query = self.get_search('gp2gp_missing_attachments_report')
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
                '| select( .total_records_transfered=="2" )', telemetry)
            
        finally:
            self.delete_index(index_name)



