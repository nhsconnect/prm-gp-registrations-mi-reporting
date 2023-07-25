import json
from datetime import datetime
from time import sleep

import jq
import pytest

from helpers.datetime_helper import create_date_time
from helpers.splunk import (create_ehr_response_payload,
                            create_registration_payload, create_sample_event,
                            get_telemetry_from_splunk, set_variables_on_query)
from tests.test_base import EventType, TestBase


class TestMissingAttachmentsTrendingOutputs(TestBase):

    def test_total_num_missing_attachments_report(self):

        # reporting window
        report_start = datetime.today().date().replace(day=1)
        report_end = datetime.today().date().replace(day=28)
        cutoff = "0"

        try:
            # Arrange
            index_name, index = self.create_index()

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_#1',
                        registration_event_datetime=create_date_time(
                            date=report_start, time="08:00:00"),
                        event_type=EventType.EHR_RESPONSES.value,
                        payload=create_ehr_response_payload(
                            number_of_placeholders=5)
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_#2',
                        registration_event_datetime=create_date_time(
                            date=report_start, time="08:05:00"),
                        event_type=EventType.EHR_RESPONSES.value,
                        payload=create_ehr_response_payload(
                            number_of_placeholders=2)
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_#3',
                        registration_event_datetime=create_date_time(
                            date=report_start, time="08:10:00"),
                        event_type=EventType.EHR_RESPONSES.value,
                        payload=create_ehr_response_payload(
                            number_of_placeholders=3)
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_#3',
                        registration_event_datetime=create_date_time(
                            date=report_start, time="08:15:00"),
                        event_type=EventType.EHR_RESPONSES.value,
                        payload=create_ehr_response_payload(
                            number_of_placeholders=0)
                    )),
                sourcetype="myevent")

            # Act
            test_query = self.generate_splunk_query_from_report(
                'gp2gp_missing_attachments_trending_report/'
                'gp2gp_missing_attachments_trending_report_num_missing_attachments')

            test_query = set_variables_on_query(test_query, {
                "$index$": index_name,
                "$start_time$": report_start.strftime("%Y-%m-%dT%H:%m:%s"),
                "$end_time$": report_end.strftime("%Y-%m-%dT%H:%m:%s"),
                "$cutoff$": cutoff
            })

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service)
            self.LOG.info(f'telemetry: {telemetry}')

            # Assert
            expected_values = {"total_num_missing_attachments": "10"}

            for idx, (key, value) in enumerate(expected_values.items()):
                self.LOG.info(f'.[{idx}] | select( .label=="{key}") | select (.count=="{value}")')
                assert jq.first(
                    f'.[{idx}] | select( .{key}=="{value}")', telemetry)

        finally:
            self.delete_index(index_name)

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
                '.[] | select( ."Transferred with no missing attachments" == "1" ) ', telemetry)


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
                '.[] | select( ."Transferred with no missing attachments" == "100.00" ) ', telemetry)


        finally:
            self.delete_index(index_name)

    @pytest.mark.parametrize("cutoff, registrationStatus",
                             [(1, "REGISTRATION"), (7, "EHR_REQUESTED"), (11, "EHR_SENT"), (19, "READY_TO_INTEGRATE")])
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
                        registration_event_datetime=create_date_time(date=report_start.replace(day=12),
                                                                     time="05:00:00"),
                        event_type=EventType.EHR_RESPONSES.value,
                        payload=create_ehr_response_payload(number_of_placeholders=2)
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversationId,
                        registration_event_datetime=create_date_time(date=report_start.replace(day=20),
                                                                     time="03:00:00"),
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

    @pytest.mark.parametrize("report_type, time_period, output",
                             [
                                 ("count", "day", {"0": {"time_period": "23-07-01",
                                                         "Transferred with missing attachments": "0",
                                                         "Transferred with no missing attachments": "1"},
                                                   "1": {"time_period": "23-07-02",
                                                         "Transferred with missing attachments": "1",
                                                         "Transferred with no missing attachments": "0"},
                                                   "2": {"time_period": "23-07-08",
                                                         "Transferred with missing attachments": "1",
                                                         "Transferred with no missing attachments": "0"}
                                                   }
                                  ),
                                 ("count", "week", {"0": {"time_period": "23-07-26",
                                                          "Transferred with missing attachments": "1",
                                                          "Transferred with no missing attachments": "1"},
                                                    "1": {"time_period": "23-07-27",
                                                          "Transferred with missing attachments": "1",
                                                          "Transferred with no missing attachments": "0"}
                                                    }
                                  ),
                                 ("count", "month", {"0": {"time_period": "23-07",
                                                           "Transferred with missing attachments": "2",
                                                           "Transferred with no missing attachments": "1"}
                                                     }
                                  ),
                                 ("percentages", "day", {"0": {"time_period": "23-07-01",
                                                               "Transferred with missing attachments": "0.00",
                                                               "Transferred with no missing attachments": "100.00"},
                                                         "1": {"time_period": "23-07-02",
                                                               "Transferred with missing attachments": "100.00",
                                                               "Transferred with no missing attachments": "0.00"},
                                                         "2": {"time_period": "23-07-08",
                                                               "Transferred with missing attachments": "100.00",
                                                               "Transferred with no missing attachments": "0.00"}
                                                         }
                                  ),
                                 ("percentages", "week", {"0": {"time_period": "23-07-26",
                                                                "Transferred with missing attachments": "50.00",
                                                                "Transferred with no missing attachments": "50.00"},
                                                          "1": {"time_period": "23-07-27",
                                                                "Transferred with missing attachments": "100.00",
                                                                "Transferred with no missing attachments": "0.00"}
                                                          }
                                  ),
                                 ("percentages", "month", {"0": {"time_period": "23-07",
                                                                 "Transferred with missing attachments": "66.67",
                                                                 "Transferred with no missing attachments": "33.33"}
                                                           }
                                  ),
                             ])
    def test_missing_attachments_report_time_period(self, report_type, time_period, output):
        """This test ensures that new conversations are at a different stage based on cutoff."""

        # Arrange
        index_name, index = self.create_index()

        report_start = "2023-07-01T00:00:00"
        report_end = "2023-07-28T00:00:00"

        try:

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id="test_1",
                        registration_event_datetime=create_date_time(date=datetime(2023, 7, 1), time="08:00:00"),
                        event_type=EventType.EHR_RESPONSES.value,
                        payload=create_ehr_response_payload(number_of_placeholders=0)
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id="test_1",
                        registration_event_datetime=create_date_time(date=datetime(2023, 7, 1), time="08:05:00"),
                        event_type=EventType.READY_TO_INTEGRATE_STATUSES.value,
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id="test_2",
                        registration_event_datetime=create_date_time(date=datetime(2023, 7, 2), time="05:03:00"),
                        event_type=EventType.EHR_RESPONSES.value,
                        payload=create_ehr_response_payload(number_of_placeholders=2)
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id="test_2",
                        registration_event_datetime=create_date_time(date=datetime(2023, 7, 2), time="08:05:00"),
                        event_type=EventType.READY_TO_INTEGRATE_STATUSES.value,
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id="test_3",
                        registration_event_datetime=create_date_time(date=datetime(2023, 7, 8), time="05:00:00"),
                        event_type=EventType.EHR_RESPONSES.value,
                        payload=create_ehr_response_payload(number_of_placeholders=2)
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id="test_3",
                        registration_event_datetime=create_date_time(date=datetime(2023, 7, 8), time="08:05:00"),
                        event_type=EventType.READY_TO_INTEGRATE_STATUSES.value,
                    )),
                sourcetype="myevent")

            # Act
            test_query = self.generate_splunk_query_from_report(
                f'gp2gp_missing_attachments_trending_report/gp2gp_missing_attachments_trending_report_{report_type}')

            test_query = set_variables_on_query(test_query, {
                "$index$": index_name,
                "$start_time$": report_start,
                "$end_time$": report_end,
                "$cutoff$": "0",
                "$time_period$": time_period
            })

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service)
            self.LOG.info(f'telemetry: {telemetry}')

            # Assert

            expected_values = output

            for row, row_values in expected_values.items():
                row_values_as_jq_str = ' '.join(
                    [f"| select(.\"{key}\"==\"{value}\") " for key, value in row_values.items()]
                )
                self.LOG.info(f'.[{row}] {row_values_as_jq_str} ')
                assert jq.first(
                    f'.[{row}] {row_values_as_jq_str} ', telemetry)

        finally:
            self.delete_index(index_name)
