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
    create_integration_payload,  create_error_payload, create_transfer_compatibility_payload, create_registration_payload
from datetime import datetime, timedelta, date
from helpers.datetime_helper import datetime_utc_now
from jinja2 import Environment, FileSystemLoader
from helpers.datetime_helper import create_date_time
from tests.test_base import TestBase, EventType


"""
This test file tests the outcome scenarios as defined in the Mural board - "Enhanced MI Reporting Requirements".
https://app.mural.co/t/nhsdigital8118/m/nhsdigital8118/1678789024199/eb0e25c47a42b88883d07af78f4814d8da521c13?sender=ud36bdee691db869bb8a35429
"""

class TestOutcomeTable(TestBase):

    def test_outcome_successful_integration(self):

        # Arrange
        index_name, index = self.create_index()

        try:
            conversation_id = 'test_outcome_successful_integration'

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id,
                        registration_event_datetime="2023-03-10T08:00:00+0000",
                        event_type=EventType.EHR_INTEGRATIONS.value,
                        payload=create_integration_payload(outcome="INTEGRATED")

                    )),
                sourcetype="myevent")
            # Act

            test_query = self.generate_splunk_query_from_report('gp2gp_outcome_report')
            test_query = set_variables_on_query(test_query, {
                "$index$": index_name,
                "$report_start$": "2023-03-01",
                "$report_end$": "2023-03-31"
            })

            sleep(2)

            telemetry = get_telemetry_from_splunk(self.savedsearch(test_query), self.splunk_service)
            self.LOG.info(f'telemetry: {telemetry}')

            # Assert - check that there is 1 event each (count), 3 events in total (totalCount) and the percentage is 33.3
            assert jq.first(
                '.[] | select( .outcome == "Successful integration" ) | select( .count == "1" )', telemetry)

        finally:
            self.delete_index(index_name)        


    def test_outcome_rejected(self):

        # Arrange

        index_name, index = self.create_index()

        try:

            conversation_id = 'test_outcome_rejected'

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id,
                        registration_event_datetime="2023-03-10T08:00:00+0000",
                        event_type=EventType.EHR_INTEGRATIONS.value,
                        payload=create_integration_payload(outcome="REJECTED")

                    )),
                sourcetype="myevent")
            # Act

            test_query = self.generate_splunk_query_from_report('gp2gp_outcome_report')
            test_query = set_variables_on_query(test_query, {
                "$index$": index_name,
                "$report_start$": "2023-03-01",
                "$report_end$": "2023-03-31"
            })

            sleep(2)

            telemetry = get_telemetry_from_splunk(self.savedsearch(test_query), self.splunk_service)
            self.LOG.info(f'telemetry: {telemetry}')

            # Assert - check that there is 1 event each (count), 3 events in total (totalCount) and the percentage is 33.3
            assert jq.first(
                '.[] | select( .outcome == "Rejected" ) | select( .count == "1" )', telemetry)

        finally:
            self.delete_index(index_name)


    def test_outcome_technical_failure_1(self):

        # Arrange

        index_name, index = self.create_index()

        try:

            conversation_id = 'test_outcome_technical_failure'

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id,
                        registration_event_datetime="2023-03-10T08:00:00+0000",
                        event_type=EventType.EHR_INTEGRATIONS.value,
                        payload=create_integration_payload(
                            outcome="FAILED_TO_INTEGRATE")

                    )),
                sourcetype="myevent")
            # Act

            test_query = self.generate_splunk_query_from_report('gp2gp_outcome_report')
            test_query = set_variables_on_query(test_query, {
                "$index$": index_name,
                "$report_start$": "2023-03-01",
                "$report_end$": "2023-03-31"
            })

            sleep(2)

            telemetry = get_telemetry_from_splunk(self.savedsearch(test_query), self.splunk_service)
            self.LOG.info(f'telemetry: {telemetry}')

            # Assert - check that there is 1 event each (count), 3 events in total (totalCount) and the percentage is 33.3
            assert jq.first(
                '.[] | select( .outcome == "Technical failure" ) | select( .count == "1" )', telemetry)

        finally:
            self.delete_index(index_name)


    def test_outcome_awaiting_integration(self):

        # Arrange

        index_name, index = self.create_index()

        try:

            conversation_id = 'test_outcome_awaiting_integration'

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id,
                        registration_event_datetime="2023-03-10T08:00:00+0000",
                        event_type=EventType.READY_TO_INTEGRATE_STATUSES.value)
                ),
                sourcetype="myevent")
            # Act

            test_query = self.generate_splunk_query_from_report('gp2gp_outcome_report')
            test_query = set_variables_on_query(test_query, {
                "$index$": index_name,
                "$report_start$": "2023-03-01",
                "$report_end$": "2023-03-31"
            })

            sleep(2)

            telemetry = get_telemetry_from_splunk(self.savedsearch(test_query), self.splunk_service)
            self.LOG.info(f'telemetry: {telemetry}')

            # Assert - check that there is 1 event each (count), 3 events in total (totalCount) and the percentage is 33.3
            assert jq.first(
                '.[] | select( .outcome == "Awaiting integration" ) | select( .count == "1" )', telemetry)

        finally:
            self.delete_index(index_name)            


    def test_outcome_in_progress_1(self):

        # Arrange

        index_name, index = self.create_index()

        # reporting window
        report_start = datetime_utc_now().date().replace(day=1)
        report_end = datetime_utc_now().date().replace(day=28)

        try:

            conversation_id_1 = 'test_outcome_in_progress_1_1'

            now_minus_23_hours = datetime_utc_now() - timedelta(hours=23, minutes=0)

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversation_id_1,
                        registration_event_datetime="2023-05-10T04:00:00+0000",
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
                        conversation_id=conversation_id_1,
                        registration_event_datetime="2023-05-10T05:00:00+0000",
                        event_type=EventType.EHR_REQUESTS.value
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversation_id_1,
                        registration_event_datetime=now_minus_23_hours.strftime(
                            "%Y-%m-%dT%H:%M:%S%z"),
                        event_type=EventType.EHR_RESPONSES.value
                    )),
                sourcetype="myevent")

            conversation_id_2 = 'test_outcome_in_progress_1_2'

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversation_id_2,
                        registration_event_datetime="2023-05-01T04:00:00+0000",
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
                        conversation_id=conversation_id_2,
                        registration_event_datetime="2023-05-01T05:00:00+0000",
                        event_type=EventType.EHR_REQUESTS.value
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversation_id_2,
                        registration_event_datetime="2023-05-05T07:00:00+0000",
                        event_type=EventType.EHR_RESPONSES.value
                    )),
                sourcetype="myevent")

            # Act

            test_query = self.generate_splunk_query_from_report('gp2gp_outcome_report')
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
                '.[] | select( .outcome == "In progress" ) | select( .count == "2" )', telemetry)

        finally:
            self.delete_index(index_name)
            

    def test_outcome_in_progress_2(self):

        # Arrange

        index_name, index = self.create_index()

        # reporting window
        report_start = datetime_utc_now().date().replace(day=1)
        report_end = datetime_utc_now().date().replace(day=28)

        try:

            conversation_id_1 = 'test_outcome_in_progress_2_1'

            # test requires a datetime less than 20mins
            now_minus_18_mins = datetime_utc_now() - timedelta(hours=0, minutes=18)

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversation_id_1,
                        registration_event_datetime=now_minus_18_mins.strftime(
                            "%Y-%m-%dT%H:%M:%S%z"),
                        event_type=EventType.EHR_REQUESTS.value
                    )),
                sourcetype="myevent")

            conversation_id_2 = 'test_outcome_in_progress_2_2'

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversation_id_2,
                        registration_event_datetime="2023-05-01T05:00:00+0000",
                        event_type=EventType.EHR_REQUESTS.value
                    )),
                sourcetype="myevent")

            # Act

            test_query = self.generate_splunk_query_from_report('gp2gp_outcome_report')
            test_query = set_variables_on_query(test_query, {
                "$index$": index_name,
                "$report_start$": report_start.strftime("%Y-%m-%d"),
                "$report_end$": report_end.strftime("%Y-%m-%d")
            })

            sleep(2)

            telemetry = get_telemetry_from_splunk(self.savedsearch(test_query), self.splunk_service)
            self.LOG.info(f'telemetry: {telemetry}')

            # Assert -
            assert jq.first(
                '.[] | select( .outcome == "In progress" ) | select( .count == "2" )', telemetry)

        finally:
            self.delete_index(index_name)            


    def test_outcome_in_progress_3(self):

        # Arrange

        index_name, index = self.create_index()

        # reporting window
        report_start = datetime_utc_now().date().replace(day=1)
        report_end = datetime_utc_now().date().replace(day=28)

        try:

            now_minus_18_mins = datetime_utc_now() - timedelta(hours=0, minutes=18)

            conversation_id_1 = 'test_outcome_in_progress_3_1'

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversation_id_1,
                        registration_event_datetime= now_minus_18_mins.strftime("%Y-%m-%dT%H:%M:%S%z"),
                        event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                        payload=create_transfer_compatibility_payload(
                            internalTransfer=False,
                            transferCompatible=True
                        )
                    )),
                sourcetype="myevent")             

            conversation_id_2 = 'test_outcome_in_progress_3_2'

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversation_id_2,
                        registration_event_datetime=create_date_time(datetime_utc_now(), "04:30:00+0000"),
                        event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                        payload=create_transfer_compatibility_payload(
                            internalTransfer=False,
                            transferCompatible=True
                        )
                    )),
                sourcetype="myevent")  
        

            # Act

            test_query = self.generate_splunk_query_from_report('gp2gp_outcome_report')
            test_query = set_variables_on_query(test_query, {
                "$index$": index_name,
                "$report_start$": report_start.strftime("%Y-%m-%d"),
                "$report_end$": report_end.strftime("%Y-%m-%d")
            })

            sleep(2)

            telemetry = get_telemetry_from_splunk(self.savedsearch(test_query), self.splunk_service)
            self.LOG.info(f'telemetry: {telemetry}')

            # Assert -
            assert jq.first(
                '.[] | select( .outcome == "In progress" ) | select( .count == "2" )', telemetry)

        finally:
           self.delete_index(index_name)


    def test_not_eligible_for_electronic_transfer(self):
        '''
        This test checks transfer compatibility payload (test 1.a) and demographic trace status (DTS) payload (test 1.b)   
        '''

        # Arrange

        index_name, index = self.create_index()

        # reporting window
        report_start = datetime_utc_now().date().replace(day=1)
        report_end = datetime_utc_now().date().replace(day=28)

        try:

            # test 1.a - NOT ELIGIBLE FOR ELECTRONIC TRANSFER - transfer_compatible = false       

            conversation_id = 'test_not_eligible_for_electronic_transfer_compatible_false'

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversation_id,
                        registration_event_datetime=create_date_time(datetime_utc_now(), "07:00:00+0000"),
                        event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                        payload=create_transfer_compatibility_payload(
                            internalTransfer=False,
                            transferCompatible=False
                        )
                    )),
                sourcetype="myevent")             

        

            # test 1.b - NOT ELIGIBLE FOR ELECTRONIC TRANSFER - status = REGISTRATION and D.T.S matched = false

            conversation_id = 'test_not_eligible_for_electronic_transfer_dts_trace_false'      

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversation_id,
                        registration_event_datetime=create_date_time(datetime_utc_now(), "04:30:00+0000"),
                        event_type=EventType.REGISTRATIONS.value,
                        payload=create_registration_payload(dtsMatched=False)
                    )),
                sourcetype="myevent")  
        

            # Act

            test_query = self.generate_splunk_query_from_report('gp2gp_outcome_report')
            test_query = set_variables_on_query(test_query, {
                "$index$": index_name,
                "$report_start$": report_start.strftime("%Y-%m-%d"),
                "$report_end$": report_end.strftime("%Y-%m-%d")
            })

            sleep(2)

            telemetry = get_telemetry_from_splunk(self.savedsearch(test_query), self.splunk_service)
            self.LOG.info(f'telemetry: {telemetry}')

            # Assert -
            assert jq.first(
                '.[] | select( .outcome == "Not eligible for electronic transfer" ) | select( .count == "2" )',
                telemetry)

        finally:
            self.delete_index(index_name)
            