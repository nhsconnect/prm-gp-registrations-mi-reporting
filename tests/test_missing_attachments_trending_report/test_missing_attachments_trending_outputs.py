import logging
import os
from enum import Enum
import pytest
import json
from time import sleep
from splunklib import client
import jq
from helpers.datetime_helper import datetime_utc_now, create_date_time
from helpers.splunk \
    import get_telemetry_from_splunk, create_sample_event, set_variables_on_query, \
    create_registration_payload, create_ehr_response_payload
from datetime import datetime, timedelta
from jinja2 import Environment, FileSystemLoader
from tests.test_base import TestBase, EventType


class TestMissingAttachmentsTrendingOutputs(TestBase):

    def test_missing_attachments_report_trending_count_with_start_end_times_as_datetimes(self):

        # Arrange
        index_name, index = self.create_index()

        # reporting window
        report_start = datetime.today().date().replace(day=1)
        report_end = datetime.today().date().replace(day=28)
        cutoff = "0"

        try:

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_#1',
                        registration_event_datetime=create_date_time(
                            date=report_start, time="08:00:00"),
                        event_type=EventType.EHR_RESPONSES.value,
                        payload=create_ehr_response_payload(
                            number_of_placeholders=0)
                    )),
                sourcetype="myevent")
            
            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_#1',
                        registration_event_datetime=create_date_time(
                            date=report_start, time="09:00:00"),
                        event_type=EventType.READY_TO_INTEGRATE_STATUSES.value                      
                    )),
                sourcetype="myevent")

            # Act
            test_query = self.generate_splunk_query_from_report(
                'gp2gp_missing_attachments_trending_report/gp2gp_missing_attachments_trending_report_count')

            test_query = set_variables_on_query(test_query, {
                "$index$": index_name,
                "$start_time$": report_start.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "$end_time$": report_end.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "$cutoff$": cutoff,
                "$time_period$": "month"
            })

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service)
            self.LOG.info(f'telemetry: {telemetry}')

            # Assert
            assert jq.first(
                '.[] | select( ."Transfered with no missing attachments" == "1" ) ', telemetry)


        finally:
            self.delete_index(index_name)

    def test_missing_attachments_report_trending_percentages_with_start_end_times_as_datetimes(self):

        # Arrange
        index_name, index = self.create_index()

        # reporting window
        report_start = datetime.today().date().replace(day=1)
        report_end = datetime.today().date().replace(day=28)
        cutoff = "0"

        try:

            conversationId = 'transfered_with_no_missing_attachments'

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversationId,
                        registration_event_datetime=create_date_time(
                            date=report_start, time="08:00:00"),
                        event_type=EventType.EHR_RESPONSES.value,
                        payload=create_ehr_response_payload(
                            number_of_placeholders=0)
                    )),
                sourcetype="myevent")
            
            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversationId,
                        registration_event_datetime=create_date_time(
                            date=report_start, time="09:00:00"),
                        event_type=EventType.READY_TO_INTEGRATE_STATUSES.value                      
                    )),
                sourcetype="myevent")

            # Act
            test_query = self.generate_splunk_query_from_report(
                'gp2gp_missing_attachments_trending_report/gp2gp_missing_attachments_trending_report_percentages')

            test_query = set_variables_on_query(test_query, {
                "$index$": index_name,
                "$start_time$": report_start.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "$end_time$": report_end.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "$cutoff$": cutoff,
                "$time_period$": "month"
            })

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service)
            self.LOG.info(f'telemetry: {telemetry}')

            # Assert
            assert jq.first(
                '.[] | select( ."Transfered with no missing attachments" == "100.00" ) ', telemetry)


        finally:
            self.delete_index(index_name)

    @pytest.mark.parametrize("cutoff, registrationStatus",[(1,"REGISTRATION"),(7,"EHR_REQUESTED"),(11,"EHR_SENT"),(19,"READY_TO_INTEGRATE")])
    def test_missing_attachments_report_cutoffs(self, cutoff, registrationStatus):
            """This test ensures that new conversations are at a different stage based on cutoff."""

            self.LOG.info(f"cutoff:{cutoff}, regstat:{registrationStatus}")

            # Arrange
            index_name, index = self.create_index()

            report_start = datetime.today().date().replace(day=1)
            report_end = datetime.today().date().replace(day=2)

            try:

                conversationId = "test_cutoffs"

                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id=conversationId,
                            registration_event_datetime=create_date_time(date=report_start.replace(day=1), time="08:00:00"),
                            event_type=EventType.REGISTRATIONS.value,
                            payload=create_registration_payload()
                        )),
                    sourcetype="myevent")

                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id=conversationId,
                            registration_event_datetime=create_date_time(date=report_start.replace(day=8), time="05:03:00"),
                            event_type=EventType.EHR_REQUESTS.value,
                        )),
                    sourcetype="myevent")

                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id=conversationId,
                            registration_event_datetime=create_date_time(date=report_start.replace(day=12), time="05:00:00"),
                            event_type=EventType.EHR_RESPONSES.value,
                            payload=create_ehr_response_payload(number_of_placeholders=2)
                        )),
                    sourcetype="myevent")

                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id=conversationId,
                            registration_event_datetime=create_date_time(date=report_start.replace(day=20), time="03:00:00"),
                            event_type=EventType.READY_TO_INTEGRATE_STATUSES.value,
                        )),
                    sourcetype="myevent")

                # Act
                test_query = self.generate_splunk_query_from_report(
                    'gp2gp_missing_attachments_trending_report/gp2gp_missing_attachments_trending_report_base')

                test_query = set_variables_on_query(test_query, {
                    "$index$": index_name,    
                    "$start_time$": report_start.strftime("%Y-%m-%dT%H:%m:%s"),
                    "$end_time$": report_end.strftime("%Y-%m-%dT%H:%m:%s"),          
                    "$cutoff$": str(cutoff)
                })

                sleep(2)

                telemetry = get_telemetry_from_splunk(
                    self.savedsearch(test_query), self.splunk_service)
                self.LOG.info(f'telemetry: {telemetry}')

                # Assert
                
                assert jq.first(
                f'.[] | select( .registrationStatus=="{registrationStatus}")', telemetry)

            finally:
                self.delete_index(index_name)