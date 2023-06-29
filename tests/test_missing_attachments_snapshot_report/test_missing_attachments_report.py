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
    create_integration_payload,  create_error_payload, create_transfer_compatibility_payload,create_ehr_response_payload
from datetime import datetime, timedelta
from jinja2 import Environment, FileSystemLoader
from tests.test_base import TestBase, EventType
from helpers.datetime_helper import create_date_time


class TestMissingAttachments(TestBase):

    def test_count_of_total_records_transferred(self):
        """a count where the status is READY_TO_INTEGRATE or INTEGRATION."""

        # reporting window
        report_start = datetime.today().date().replace(day=1)
        report_end = datetime.today().date().replace(day=30)

        try:
            # Arrange
            index_name, index = self.create_index()            

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_total_records_transferred_#1',
                        registration_event_datetime=create_date_time(date=report_start, time="09:00:00"),
                        event_type=EventType.EHR_INTEGRATIONS.value,
                        payload=create_integration_payload(outcome="INTEGRATED")
                    )),
                sourcetype="myevent")
           
            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_total_records_transferred_#2',
                        registration_event_datetime=create_date_time(date=report_start, time="10:00:00"),
                        event_type=EventType.READY_TO_INTEGRATE_STATUSES.value                       
                    )),
                sourcetype="myevent")
            
            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_total_records_transferred_#3',
                        registration_event_datetime=create_date_time(date=report_start, time="11:00:00"),
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
                        conversation_id='test_total_records_transferred_#4',
                        registration_event_datetime=create_date_time(date=report_start, time="12:00:00"),
                        event_type=EventType.EHR_REQUESTS.value                        
                    )),
                sourcetype="myevent")

            # Act

            test_query = self.generate_splunk_query_from_report(
                'gp2gp_missing_attachments_snapshot_report/gp2gp_missing_attachments_snapshot_report_count'
            )
            test_query = set_variables_on_query(test_query, {
                "$index$": index_name,
                "$report_start$": report_start.strftime("%Y-%m-%d"),
                "$report_end$": report_end.strftime("%Y-%m-%d")
            })

            sleep(2)

            telemetry = get_telemetry_from_splunk(self.savedsearch(test_query), self.splunk_service)
            self.LOG.info(f'telemetry: {telemetry}')

            # Assert
            expected_values = {"Records Transferred": "2"}

            for idx, (key, value) in enumerate(expected_values.items()):
                self.LOG.info(f'.[{idx}] | select( .label=="{key}") | select (.count=="{value}")')
                assert jq.first(
                    f'.[{idx}] | select( .label=="{key}") | select (.count=="{value}")', telemetry)
            
        finally:
            self.delete_index(index_name)

    def test_count_of_transferred_with_no_missing_attachments(self):
        """a count where the outcome is READY_TO_INTEGRATE (or later event) and there are no placeholders (EHR Response)
        and no document migration failures (document-responses)."""

        # reporting window
        report_start = datetime.today().date().replace(day=1)
        report_end = datetime.today().date().replace(day=30)

        try:
            # Arrange
            index_name, index = self.create_index()     

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_#1',
                        registration_event_datetime=create_date_time(date=report_start, time="09:30:00"),
                        event_type=EventType.EHR_RESPONSES.value,
                        payload=create_ehr_response_payload(number_of_placeholders=0)               
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_#1',
                        registration_event_datetime=create_date_time(date=report_start, time="09:00:00"),
                        event_type=EventType.READY_TO_INTEGRATE_STATUSES.value                       
                    )),
                sourcetype="myevent")  
            

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_#2',
                        registration_event_datetime=create_date_time(date=report_start, time="09:00:00"),
                        event_type=EventType.EHR_RESPONSES.value,
                        payload=create_ehr_response_payload(number_of_placeholders=4)               
                    )),
                sourcetype="myevent")       
            
            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_#2',
                        registration_event_datetime=create_date_time(date=report_start, time="09:10:00"),
                        event_type=EventType.READY_TO_INTEGRATE_STATUSES.value                       
                    )),
                sourcetype="myevent")             
            

            # Act

            test_query = self.generate_splunk_query_from_report(
                'gp2gp_missing_attachments_snapshot_report/gp2gp_missing_attachments_snapshot_report_count'
            )
            test_query = set_variables_on_query(test_query, {
                "$index$": index_name,
                "$report_start$": report_start.strftime("%Y-%m-%d"),
                "$report_end$": report_end.strftime("%Y-%m-%d")
            })

            sleep(2)

            telemetry = get_telemetry_from_splunk(self.savedsearch(test_query), self.splunk_service)
            self.LOG.info(f'telemetry: {telemetry}')         
            
             # Assert
            expected_values = {"Records Transferred": "2",
                               "No Missing Attachments": "1"}

            for idx, (key, value) in enumerate(expected_values.items()):
                # self.LOG.info(f'.[{idx}] | select( .label=="{key}") | select (.count=="{value}")')
                assert jq.first(
                    f'.[{idx}] | select( .label=="{key}") | select (.count=="{value}")', telemetry)
            
        finally:
            self.delete_index(index_name)

    def test_count_of_transferred_with_missing_attachments(self):
        """a count where the outcome is READY_TO_INTEGRATE (or later event) and placeholders exist (EHR Response)
        or there is document migration failures (document-responses)."""

        # reporting window
        report_start = datetime.today().date().replace(day=1)
        report_end = datetime.today().date().replace(day=30)

        try:
            # Arrange
            index_name, index = self.create_index()

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_#1',
                        registration_event_datetime=create_date_time(date=report_start, time="09:30:00"),
                        event_type=EventType.EHR_RESPONSES.value,
                        payload=create_ehr_response_payload(number_of_placeholders=0)
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_#1',
                        registration_event_datetime=create_date_time(date=report_start, time="09:00:00"),
                        event_type=EventType.READY_TO_INTEGRATE_STATUSES.value
                    )),
                sourcetype="myevent")


            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_#2',
                        registration_event_datetime=create_date_time(date=report_start, time="09:00:00"),
                        event_type=EventType.EHR_RESPONSES.value,
                        payload=create_ehr_response_payload(number_of_placeholders=4)
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_#2',
                        registration_event_datetime=create_date_time(date=report_start, time="09:10:00"),
                        event_type=EventType.READY_TO_INTEGRATE_STATUSES.value
                    )),
                sourcetype="myevent")


            # Act

            test_query = self.generate_splunk_query_from_report(
                'gp2gp_missing_attachments_snapshot_report/gp2gp_missing_attachments_snapshot_report_count'
            )
            test_query = set_variables_on_query(test_query, {
                "$index$": index_name,
                "$report_start$": report_start.strftime("%Y-%m-%d"),
                "$report_end$": report_end.strftime("%Y-%m-%d")
            })

            sleep(2)

            telemetry = get_telemetry_from_splunk(self.savedsearch(test_query), self.splunk_service)
            self.LOG.info(f'telemetry: {telemetry}')

            # Assert
            expected_values = {"Records Transferred": "2",
                               "No Missing Attachments": "1",
                               "Missing Attachments": "1"}

            for idx, (key, value) in enumerate(expected_values.items()):
                # self.LOG.info(f'.[{idx}] | select( .label=="{key}") | select (.count=="{value}")')
                assert jq.first(
                    f'.[{idx}] | select( .label=="{key}") | select (.count=="{value}")', telemetry)

        finally:
            self.delete_index(index_name)

    def test_percentage_of_transferred_with_no_missing_attachments(self):
        """The percentage of records transferred where the outcome is READY_TO_INTEGRATE (or later event) and there
        are no placeholders (EHR Response) and no document migration failures (document-responses).
        % - count/ number of transfers * 100 to 2 decimal places."""

        # reporting window
        report_start = datetime.today().date().replace(day=1)
        report_end = datetime.today().date().replace(day=30)

        try:
            # Arrange
            index_name, index = self.create_index()

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_#1',
                        registration_event_datetime=create_date_time(date=report_start, time="09:30:00"),
                        event_type=EventType.EHR_RESPONSES.value,
                        payload=create_ehr_response_payload(number_of_placeholders=0)
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_#1',
                        registration_event_datetime=create_date_time(date=report_start, time="09:00:00"),
                        event_type=EventType.READY_TO_INTEGRATE_STATUSES.value
                    )),
                sourcetype="myevent")


            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_#2',
                        registration_event_datetime=create_date_time(date=report_start, time="09:00:00"),
                        event_type=EventType.EHR_RESPONSES.value,
                        payload=create_ehr_response_payload(number_of_placeholders=4)
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_#2',
                        registration_event_datetime=create_date_time(date=report_start, time="09:10:00"),
                        event_type=EventType.READY_TO_INTEGRATE_STATUSES.value
                    )),
                sourcetype="myevent")


            # Act

            test_query = self.generate_splunk_query_from_report(
                'gp2gp_missing_attachments_snapshot_report/gp2gp_missing_attachments_snapshot_report_percentages'
            )
            test_query = set_variables_on_query(test_query, {
                "$index$": index_name,
                "$report_start$": report_start.strftime("%Y-%m-%d"),
                "$report_end$": report_end.strftime("%Y-%m-%d")
            })

            sleep(2)

            telemetry = get_telemetry_from_splunk(self.savedsearch(test_query), self.splunk_service)
            self.LOG.info(f'telemetry: {telemetry}')

            # Assert
            expected_values = {"No Missing Attachments": "50.00"}

            for idx, (key, value) in enumerate(expected_values.items()):
                # self.LOG.info(f'.[{idx}] | select( .label=="{key}") | select (.count=="{value}")')
                assert jq.first(
                    f'.[{idx}] | select( .label=="{key}") | select (.count=="{value}")', telemetry)

        finally:
            self.delete_index(index_name)


    def test_percentage_of_transferred_with_missing_attachments(self):

        # reporting window
        report_start = datetime.today().date().replace(day=1)
        report_end = datetime.today().date().replace(day=30)

        try:
            # Arrange
            index_name, index = self.create_index()

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_#1',
                        registration_event_datetime=create_date_time(date=report_start, time="09:30:00"),
                        event_type=EventType.EHR_RESPONSES.value,
                        payload=create_ehr_response_payload(number_of_placeholders=0)
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_#1',
                        registration_event_datetime=create_date_time(date=report_start, time="09:00:00"),
                        event_type=EventType.READY_TO_INTEGRATE_STATUSES.value
                    )),
                sourcetype="myevent")


            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_#2',
                        registration_event_datetime=create_date_time(date=report_start, time="09:00:00"),
                        event_type=EventType.EHR_RESPONSES.value,
                        payload=create_ehr_response_payload(number_of_placeholders=4)
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_#2',
                        registration_event_datetime=create_date_time(date=report_start, time="09:10:00"),
                        event_type=EventType.READY_TO_INTEGRATE_STATUSES.value
                    )),
                sourcetype="myevent")


            # Act

            test_query = self.generate_splunk_query_from_report(
                'gp2gp_missing_attachments_snapshot_report/gp2gp_missing_attachments_snapshot_report_percentages'
            )
            test_query = set_variables_on_query(test_query, {
                "$index$": index_name,
                "$report_start$": report_start.strftime("%Y-%m-%d"),
                "$report_end$": report_end.strftime("%Y-%m-%d")
            })

            sleep(2)

            telemetry = get_telemetry_from_splunk(self.savedsearch(test_query), self.splunk_service)
            self.LOG.info(f'telemetry: {telemetry}')

            # Assert
            expected_values = {"No Missing Attachments": "50.00",
                               "Missing Attachments": "50.00"}

            for idx, (key, value) in enumerate(expected_values.items()):
                # self.LOG.info(f'.[{idx}] | select( .label=="{key}") | select (.count=="{value}")')
                assert jq.first(
                    f'.[{idx}] | select( .label=="{key}") | select (.count=="{value}")', telemetry)

        finally:
            self.delete_index(index_name)




