import logging
import os
from enum import Enum
import pytest
import json
from time import sleep, strftime
from splunklib import client
import jq
from helpers.splunk import (
    get_telemetry_from_splunk,
    get_or_create_index,
    create_sample_event,
    set_variables_on_query,
    create_integration_payload,
    create_error_payload,
    create_transfer_compatibility_payload,
    create_ehr_response_payload,
)
from datetime import date, timedelta, datetime
from jinja2 import Environment, FileSystemLoader
from helpers.datetime_helper import (
    create_date_time,
    generate_report_start_date,
    generate_report_end_date,
    datetime_utc_now,
)
import uuid
from tests.test_base import TestBase, EventType

class TestTechnicalFailuresTrendingGraphs(TestBase):
    def test_errors_graph_count(self):
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
                        conversation_id='test_error_code_06',
                        registration_event_datetime=create_date_time(date=report_start, time="11:00:00"),
                        event_type=EventType.EHR_REQUESTS.value
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_error_code_06',
                        registration_event_datetime=create_date_time(date=report_start, time="11:01:00"),
                        event_type=EventType.ERRORS.value,
                        payload=create_error_payload(
                            errorCode="06",
                            errorDescription="Not at surgery",
                            failurePoint=EventType.EHR_REQUESTS.value
                        )

                    )),
                sourcetype="myevent")


            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_error_code_07',
                        registration_event_datetime=create_date_time(date=report_start, time="11:00:00"),
                        event_type=EventType.EHR_RESPONSES.value
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_error_code_07',
                        registration_event_datetime=create_date_time(date=report_start, time="11:01:00"),
                        event_type=EventType.ERRORS.value,
                        payload=create_error_payload(
                            errorCode="07",
                            errorDescription="GP2GP Messaging is not enabled on this system",
                            failurePoint=EventType.EHR_RESPONSES.value
                        )

                    )),
                sourcetype="myevent")


            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_error_code_09',
                        registration_event_datetime=create_date_time(date=report_start, time="11:00:00"),
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
                        conversation_id='test_error_code_09',
                        registration_event_datetime=create_date_time(date=report_start, time="11:01:00"),
                        event_type=EventType.ERRORS.value,
                        payload=create_error_payload(
                            errorCode="09",
                            errorDescription="EHR Extract received without corresponding request",
                            failurePoint=EventType.EHR_RESPONSES.value
                        )

                    )),
                sourcetype="myevent")

            # Act
            test_query = self.generate_splunk_query_from_report(
                "gp2gp_technical_failures_trending_report/gp2gp_technical_failures_trending_error_graph_count"
            )

            test_query = set_variables_on_query(
                test_query,
                {
                    "$index$": index_name,
                    "$start_time$": report_start.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    "$end_time$": report_end.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    "$cutoff$": cutoff,
                    "$time_period$": "month",
                },
            )

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service
            )
            self.LOG.info(f"telemetry: {telemetry}")

            # Assert
            time_period_month_str = datetime_utc_now().strftime("%Y-%m")
            expected_values = {
                "0": {"time_period": time_period_month_str,
                      "06": "1",
                      "07": "1",
                      "09": "1",
                      },
            }

            for idx in range(len(expected_values)):
                for key, value in expected_values[str(idx)].items():
                    self.LOG.info(
                        f'.[{idx}] | select( ."{key}"=="{value}")'
                    )
                    assert jq.first(
                        f'.[{idx}] | select( ."{key}"=="{value}")',
                        telemetry,
                    )

        finally:
            self.delete_index(index_name)

    def test_errors_graph_percentage(self):
        # reporting window
        report_start = datetime.today().date().replace(day=1)
        report_end = datetime.today().date().replace(day=28)
        cutoff = "0"

        num_errors = {'06': 2, '07': 3, '09': 5}

        try:
            # Arrange
            index_name, index = self.create_index()

            for idx in range(num_errors['06']):
                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id='test_error_code_06_'+str(idx),
                            registration_event_datetime=create_date_time(date=report_start, time="11:00:00"),
                            event_type=EventType.EHR_REQUESTS.value
                        )),
                    sourcetype="myevent")

                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id='test_error_code_06_'+str(idx),
                            registration_event_datetime=create_date_time(date=report_start, time="11:01:00"),
                            event_type=EventType.ERRORS.value,
                            payload=create_error_payload(
                                errorCode="06",
                                errorDescription="Not at surgery",
                                failurePoint=EventType.EHR_REQUESTS.value
                            )

                        )),
                    sourcetype="myevent")

            for idx in range(num_errors['07']):
                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id='test_error_code_07_'+str(idx),
                            registration_event_datetime=create_date_time(date=report_start, time="11:00:00"),
                            event_type=EventType.EHR_RESPONSES.value
                        )),
                    sourcetype="myevent")

                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id='test_error_code_07_'+str(idx),
                            registration_event_datetime=create_date_time(date=report_start, time="11:01:00"),
                            event_type=EventType.ERRORS.value,
                            payload=create_error_payload(
                                errorCode="07",
                                errorDescription="GP2GP Messaging is not enabled on this system",
                                failurePoint=EventType.EHR_RESPONSES.value
                            )

                        )),
                    sourcetype="myevent")

            for idx in range(num_errors['09']):
                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id='test_error_code_09_'+str(idx),
                            registration_event_datetime=create_date_time(date=report_start, time="11:00:00"),
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
                            conversation_id='test_error_code_09_'+str(idx),
                            registration_event_datetime=create_date_time(date=report_start, time="11:01:00"),
                            event_type=EventType.ERRORS.value,
                            payload=create_error_payload(
                                errorCode="09",
                                errorDescription="EHR Extract received without corresponding request",
                                failurePoint=EventType.EHR_RESPONSES.value
                            )

                        )),
                    sourcetype="myevent")

            # Act
            test_query = self.generate_splunk_query_from_report(
                "gp2gp_technical_failures_trending_report/"
                "gp2gp_technical_failures_trending_error_graph_percentage"
            )

            test_query = set_variables_on_query(
                test_query,
                {
                    "$index$": index_name,
                    "$start_time$": report_start.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    "$end_time$": report_end.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    "$cutoff$": cutoff,
                    "$time_period$": "month",
                },
            )

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service
            )
            self.LOG.info(f"telemetry: {telemetry}")

            # Assert
            time_period_month_str = datetime_utc_now().strftime("%Y-%m")
            expected_values = {
                "0": {"time_period": time_period_month_str,
                      "06": "20.00",
                      "07": "30.00",
                      "09": "50.00",
                      },
            }

            for idx in range(len(expected_values)):
                for key, value in expected_values[str(idx)].items():
                    self.LOG.info(
                        f'.[{idx}] | select( ."{key}"=="{value}")'
                    )
                    assert jq.first(
                        f'.[{idx}] | select( ."{key}"=="{value}")',
                        telemetry,
                    )

        finally:
            self.delete_index(index_name)

    def test_errors_graph_time_period_token_month(self):
        # reporting window
        report_start = datetime.today().date().replace(day=1) - timedelta(days=7)
        report_end = generate_report_end_date()
        cutoff = "0"

        try:
            # Arrange
            index_name, index = self.create_index()

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_error_code_06_month_1',
                        registration_event_datetime=create_date_time(date=report_start, time="11:00:00"),
                        event_type=EventType.EHR_REQUESTS.value
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_error_code_06_month_1',
                        registration_event_datetime=create_date_time(date=report_start, time="11:01:00"),
                        event_type=EventType.ERRORS.value,
                        payload=create_error_payload(
                            errorCode="06",
                            errorDescription="Not at surgery",
                            failurePoint=EventType.EHR_REQUESTS.value
                        )

                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_error_code_06_month_2_1',
                        registration_event_datetime=create_date_time(date=report_start + timedelta(days=9),
                                                                     time="11:00:00"),
                        event_type=EventType.EHR_REQUESTS.value
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_error_code_06_month_2_1',
                        registration_event_datetime=create_date_time(date=report_start + timedelta(days=9),
                                                                     time="11:01:00"),
                        event_type=EventType.ERRORS.value,
                        payload=create_error_payload(
                            errorCode="06",
                            errorDescription="Not at surgery",
                            failurePoint=EventType.EHR_REQUESTS.value
                        )

                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_error_code_06_month_2_2',
                        registration_event_datetime=create_date_time(date=report_start + timedelta(days=9),
                                                                     time="11:00:00"),
                        event_type=EventType.EHR_REQUESTS.value
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_error_code_06_month_2_2',
                        registration_event_datetime=create_date_time(date=report_start + timedelta(days=9),
                                                                     time="11:01:00"),
                        event_type=EventType.ERRORS.value,
                        payload=create_error_payload(
                            errorCode="06",
                            errorDescription="Not at surgery",
                            failurePoint=EventType.EHR_REQUESTS.value
                        )

                    )),
                sourcetype="myevent")

            # Act
            test_query = self.generate_splunk_query_from_report(
                "gp2gp_technical_failures_trending_report/"
                "gp2gp_technical_failures_trending_error_graph_count"
            )

            test_query = set_variables_on_query(
                test_query,
                {
                    "$index$": index_name,
                    "$start_time$": report_start.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    "$end_time$": report_end.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    "$cutoff$": cutoff,
                    "$time_period$": "month",
                },
            )

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service
            )
            self.LOG.info(f"telemetry: {telemetry}")

            # Assert
            time_period_month_1 = report_start.strftime("%Y-%m")
            time_period_month_2 = (report_start + timedelta(days=9)).strftime("%Y-%m")
            expected_values = {
                "0": {"time_period": time_period_month_1,
                      "06": "1",
                      },
                "1": {"time_period": time_period_month_2,
                      "06": "2",
                      },
            }

            for idx in range(len(expected_values)):
                for key, value in expected_values[str(idx)].items():
                    self.LOG.info(
                        f'.[{idx}] | select( ."{key}"=="{value}")'
                    )
                    assert jq.first(
                        f'.[{idx}] | select( ."{key}"=="{value}")',
                        telemetry,
                    )

        finally:
            self.delete_index(index_name)

    def test_errors_graph_time_period_token_week(self):
        # reporting window
        report_start = datetime.today().date().replace(day=1)
        report_end = report_start + timedelta(days=15)
        cutoff = "0"

        num_events = {"week_1": 2, "week_2": 4, "week_3": 3}
        try:
            # Arrange
            index_name, index = self.create_index()

            for idx in range(num_events["week_1"]):
                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id='test_error_code_06_week_1_'+str(idx),
                            registration_event_datetime=create_date_time(date=report_start, time="11:00:00"),
                            event_type=EventType.EHR_REQUESTS.value
                        )),
                    sourcetype="myevent")

                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id='test_error_code_06_week_1_'+str(idx),
                            registration_event_datetime=create_date_time(date=report_start, time="11:01:00"),
                            event_type=EventType.ERRORS.value,
                            payload=create_error_payload(
                                errorCode="06",
                                errorDescription="Not at surgery",
                                failurePoint=EventType.EHR_REQUESTS.value
                            )

                        )),
                    sourcetype="myevent")

            for idx in range(num_events["week_2"]):
                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id='test_error_code_06_week_2_'+str(idx),
                            registration_event_datetime=create_date_time(date=report_start + timedelta(days=7),
                                                                         time="11:00:00"),
                            event_type=EventType.EHR_REQUESTS.value
                        )),
                    sourcetype="myevent")

                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id='test_error_code_06_week_2_'+str(idx),
                            registration_event_datetime=create_date_time(date=report_start + timedelta(days=7),
                                                                         time="11:01:00"),
                            event_type=EventType.ERRORS.value,
                            payload=create_error_payload(
                                errorCode="06",
                                errorDescription="Not at surgery",
                                failurePoint=EventType.EHR_REQUESTS.value
                            )

                        )),
                    sourcetype="myevent")

            for idx in range(num_events["week_3"]):
                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id='test_error_code_06_week_3_'+str(idx),
                            registration_event_datetime=create_date_time(date=report_start + timedelta(days=14),
                                                                         time="11:00:00"),
                            event_type=EventType.EHR_REQUESTS.value
                        )),
                    sourcetype="myevent")

                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id='test_error_code_06_week_3_'+str(idx),
                            registration_event_datetime=create_date_time(date=report_start + timedelta(days=14),
                                                                         time="11:01:00"),
                            event_type=EventType.ERRORS.value,
                            payload=create_error_payload(
                                errorCode="06",
                                errorDescription="Not at surgery",
                                failurePoint=EventType.EHR_REQUESTS.value
                            )

                        )),
                    sourcetype="myevent")

            # Act
            test_query = self.generate_splunk_query_from_report(
                "gp2gp_technical_failures_trending_report/"
                "gp2gp_technical_failures_trending_error_graph_count"
            )

            test_query = set_variables_on_query(
                test_query,
                {
                    "$index$": index_name,
                    "$start_time$": report_start.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    "$end_time$": report_end.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    "$cutoff$": cutoff,
                    "$time_period$": "week",
                },
            )

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service
            )
            self.LOG.info(f"telemetry: {telemetry}")

            # Assert
            time_period_week_1 = report_start.strftime("%Y-Wk%W")
            time_period_week_2 = (report_start + timedelta(days=7)).strftime("%Y-Wk%W")
            time_period_week_3 = (report_start + timedelta(days=14)).strftime("%Y-Wk%W")
            expected_values = {
                "0": {"time_period": time_period_week_1,
                      "06": str(num_events["week_1"]),
                      },
                "1": {"time_period": time_period_week_2,
                      "06": str(num_events["week_2"]),
                      },
                "2": {"time_period": time_period_week_3,
                      "06": str(num_events["week_3"]),
                      },
            }

            for idx in range(len(expected_values)):
                for key, value in expected_values[str(idx)].items():
                    self.LOG.info(
                        f'.[{idx}] | select( ."{key}"=="{value}")'
                    )
                    assert jq.first(
                        f'.[{idx}] | select( ."{key}"=="{value}")',
                        telemetry,
                    )

        finally:
            self.delete_index(index_name)

    def test_errors_graph_time_period_token_day(self):
        # reporting window
        report_start = datetime.today().date() - timedelta(days=5)
        report_end = datetime.today().date()
        cutoff = "0"

        num_events = {"day_1": 2, "day_2": 4, "day_3": 3}
        try:
            # Arrange
            index_name, index = self.create_index()

            for idx in range(num_events["day_1"]):
                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id='test_error_code_06_day_1_'+str(idx),
                            registration_event_datetime=create_date_time(date=report_start, time="11:00:00"),
                            event_type=EventType.EHR_REQUESTS.value
                        )),
                    sourcetype="myevent")

                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id='test_error_code_06_day_1_'+str(idx),
                            registration_event_datetime=create_date_time(date=report_start, time="11:01:00"),
                            event_type=EventType.ERRORS.value,
                            payload=create_error_payload(
                                errorCode="06",
                                errorDescription="Not at surgery",
                                failurePoint=EventType.EHR_REQUESTS.value
                            )

                        )),
                    sourcetype="myevent")

            for idx in range(num_events["day_2"]):
                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id='test_error_code_06_day_2_'+str(idx),
                            registration_event_datetime=create_date_time(date=report_start + timedelta(days=1),
                                                                         time="11:00:00"),
                            event_type=EventType.EHR_REQUESTS.value
                        )),
                    sourcetype="myevent")

                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id='test_error_code_06_day_2_'+str(idx),
                            registration_event_datetime=create_date_time(date=report_start + timedelta(days=1),
                                                                         time="11:01:00"),
                            event_type=EventType.ERRORS.value,
                            payload=create_error_payload(
                                errorCode="06",
                                errorDescription="Not at surgery",
                                failurePoint=EventType.EHR_REQUESTS.value
                            )

                        )),
                    sourcetype="myevent")

            for idx in range(num_events["day_3"]):
                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id='test_error_code_06_day_3_'+str(idx),
                            registration_event_datetime=create_date_time(date=report_start + timedelta(days=2),
                                                                         time="11:00:00"),
                            event_type=EventType.EHR_REQUESTS.value
                        )),
                    sourcetype="myevent")

                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id='test_error_code_06_day_3_'+str(idx),
                            registration_event_datetime=create_date_time(date=report_start + timedelta(days=2),
                                                                         time="11:01:00"),
                            event_type=EventType.ERRORS.value,
                            payload=create_error_payload(
                                errorCode="06",
                                errorDescription="Not at surgery",
                                failurePoint=EventType.EHR_REQUESTS.value
                            )

                        )),
                    sourcetype="myevent")

            # Act
            test_query = self.generate_splunk_query_from_report(
                "gp2gp_technical_failures_trending_report/"
                "gp2gp_technical_failures_trending_error_graph_count"
            )

            test_query = set_variables_on_query(
                test_query,
                {
                    "$index$": index_name,
                    "$start_time$": report_start.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    "$end_time$": report_end.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    "$cutoff$": cutoff,
                    "$time_period$": "day",
                },
            )

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service
            )
            self.LOG.info(f"telemetry: {telemetry}")

            # Assert
            time_period_day_1 = report_start.strftime("%Y-%m-%d")
            time_period_day_2 = (report_start + timedelta(days=1)).strftime("%Y-%m-%d")
            time_period_day_3 = (report_start + timedelta(days=2)).strftime("%Y-%m-%d")
            expected_values = {
                "0": {"time_period": time_period_day_1,
                      "06": str(num_events["day_1"]),
                      },
                "1": {"time_period": time_period_day_2,
                      "06": str(num_events["day_2"]),
                      },
                "2": {"time_period": time_period_day_3,
                      "06": str(num_events["day_3"]),
                      },
            }

            for idx in range(len(expected_values)):
                for key, value in expected_values[str(idx)].items():
                    self.LOG.info(
                        f'.[{idx}] | select( ."{key}"=="{value}")'
                    )
                    assert jq.first(
                        f'.[{idx}] | select( ."{key}"=="{value}")',
                        telemetry,
                    )

        finally:
            self.delete_index(index_name)

    def test_failure_point_graph_count(self):
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
                        conversation_id='test_failure_point_ehr_request',
                        registration_event_datetime=create_date_time(date=report_start, time="11:00:00"),
                        event_type=EventType.EHR_REQUESTS.value
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_failure_point_ehr_request',
                        registration_event_datetime=create_date_time(date=report_start, time="11:01:00"),
                        event_type=EventType.ERRORS.value,
                        payload=create_error_payload(
                            errorCode="06",
                            errorDescription="Not at surgery",
                            failurePoint=EventType.EHR_REQUESTS.value
                        )

                    )),
                sourcetype="myevent")


            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_failure_point_ehr_response_1',
                        registration_event_datetime=create_date_time(date=report_start, time="11:00:00"),
                        event_type=EventType.EHR_RESPONSES.value
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_failure_point_ehr_response_1',
                        registration_event_datetime=create_date_time(date=report_start, time="11:01:00"),
                        event_type=EventType.ERRORS.value,
                        payload=create_error_payload(
                            errorCode="06",
                            errorDescription="GP2GP Messaging is not enabled on this system",
                            failurePoint=EventType.EHR_RESPONSES.value
                        )

                    )),
                sourcetype="myevent")


            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_failure_point_ehr_response_2',
                        registration_event_datetime=create_date_time(date=report_start, time="11:00:00"),
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
                        conversation_id='test_failure_point_ehr_response_2',
                        registration_event_datetime=create_date_time(date=report_start, time="11:01:00"),
                        event_type=EventType.ERRORS.value,
                        payload=create_error_payload(
                            errorCode="06",
                            errorDescription="EHR Extract received without corresponding request",
                            failurePoint=EventType.EHR_RESPONSES.value
                        )

                    )),
                sourcetype="myevent")

            # shouldn't show
            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_error_code_07',
                        registration_event_datetime=create_date_time(date=report_start, time="11:00:00"),
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
                        conversation_id='test_error_code_07',
                        registration_event_datetime=create_date_time(date=report_start, time="11:01:00"),
                        event_type=EventType.ERRORS.value,
                        payload=create_error_payload(
                            errorCode="07",
                            errorDescription="EHR Extract received without corresponding request",
                            failurePoint=EventType.EHR_RESPONSES.value
                        )

                    )),
                sourcetype="myevent")

            # Act
            test_query = self.generate_splunk_query_from_report(
                "gp2gp_technical_failures_trending_report/gp2gp_technical_failures_trending_failure_point_graph_count"
            )

            test_query = set_variables_on_query(
                test_query,
                {
                    "$index$": index_name,
                    "$start_time$": report_start.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    "$end_time$": report_end.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    "$cutoff$": cutoff,
                    "$time_period$": "month",
                    "$errorGraphColumn$": "06"
                },
            )

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service
            )
            self.LOG.info(f"telemetry: {telemetry}")

            # Assert
            time_period_month_str = datetime_utc_now().strftime("%Y-%m")
            expected_values = {
                "0": {"time_period": time_period_month_str,
                      "EHR_REQUESTS": "1",
                      "EHR_RESPONSES": "2",
                      },
            }

            for idx in range(len(expected_values)):
                for key, value in expected_values[str(idx)].items():
                    self.LOG.info(
                        f'.[{idx}] | select( ."{key}"=="{value}")'
                    )
                    assert jq.first(
                        f'.[{idx}] | select( ."{key}"=="{value}")',
                        telemetry,
                    )

        finally:
            self.delete_index(index_name)

    def test_failure_point_graph_percentage(self):
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
                        conversation_id='test_failure_point_ehr_request',
                        registration_event_datetime=create_date_time(date=report_start, time="11:00:00"),
                        event_type=EventType.EHR_REQUESTS.value
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_failure_point_ehr_request',
                        registration_event_datetime=create_date_time(date=report_start, time="11:01:00"),
                        event_type=EventType.ERRORS.value,
                        payload=create_error_payload(
                            errorCode="06",
                            errorDescription="Not at surgery",
                            failurePoint=EventType.EHR_REQUESTS.value
                        )

                    )),
                sourcetype="myevent")


            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_failure_point_ehr_response_1',
                        registration_event_datetime=create_date_time(date=report_start, time="11:00:00"),
                        event_type=EventType.EHR_RESPONSES.value
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_failure_point_ehr_response_1',
                        registration_event_datetime=create_date_time(date=report_start, time="11:01:00"),
                        event_type=EventType.ERRORS.value,
                        payload=create_error_payload(
                            errorCode="06",
                            errorDescription="GP2GP Messaging is not enabled on this system",
                            failurePoint=EventType.EHR_RESPONSES.value
                        )

                    )),
                sourcetype="myevent")


            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_failure_point_ehr_response_2',
                        registration_event_datetime=create_date_time(date=report_start, time="11:00:00"),
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
                        conversation_id='test_failure_point_ehr_response_2',
                        registration_event_datetime=create_date_time(date=report_start, time="11:01:00"),
                        event_type=EventType.ERRORS.value,
                        payload=create_error_payload(
                            errorCode="06",
                            errorDescription="EHR Extract received without corresponding request",
                            failurePoint=EventType.EHR_RESPONSES.value
                        )

                    )),
                sourcetype="myevent")

            # shouldn't show
            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_error_code_07',
                        registration_event_datetime=create_date_time(date=report_start, time="11:00:00"),
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
                        conversation_id='test_error_code_07',
                        registration_event_datetime=create_date_time(date=report_start, time="11:01:00"),
                        event_type=EventType.ERRORS.value,
                        payload=create_error_payload(
                            errorCode="07",
                            errorDescription="EHR Extract received without corresponding request",
                            failurePoint=EventType.EHR_RESPONSES.value
                        )

                    )),
                sourcetype="myevent")

            # Act
            test_query = self.generate_splunk_query_from_report(
                "gp2gp_technical_failures_trending_report/"
                "gp2gp_technical_failures_trending_failure_point_graph_percentage"
            )

            test_query = set_variables_on_query(
                test_query,
                {
                    "$index$": index_name,
                    "$start_time$": report_start.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    "$end_time$": report_end.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    "$cutoff$": cutoff,
                    "$time_period$": "month",
                    "$errorGraphColumn$": "06"
                },
            )

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service
            )
            self.LOG.info(f"telemetry: {telemetry}")

            # Assert
            time_period_month_str = datetime_utc_now().strftime("%Y-%m")
            expected_values = {
                "0": {"time_period": time_period_month_str,
                      "EHR_REQUESTS": "33.33",
                      "EHR_RESPONSES": "66.67",
                      },
            }

            for idx in range(len(expected_values)):
                for key, value in expected_values[str(idx)].items():
                    self.LOG.info(
                        f'.[{idx}] | select( ."{key}"=="{value}")'
                    )
                    assert jq.first(
                        f'.[{idx}] | select( ."{key}"=="{value}")',
                        telemetry,
                    )

        finally:
            self.delete_index(index_name)

    def test_failure_point_graph_time_period_token_month(self):
        # reporting window
        report_start = datetime.today().date().replace(day=1) - timedelta(days=7)
        report_end = generate_report_end_date()
        cutoff = "0"

        try:
            # Arrange
            index_name, index = self.create_index()

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_failure_point_ehr_requests_month_1',
                        registration_event_datetime=create_date_time(date=report_start, time="11:00:00"),
                        event_type=EventType.EHR_REQUESTS.value
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_failure_point_ehr_requests_month_1',
                        registration_event_datetime=create_date_time(date=report_start, time="11:01:00"),
                        event_type=EventType.ERRORS.value,
                        payload=create_error_payload(
                            errorCode="06",
                            errorDescription="Not at surgery",
                            failurePoint=EventType.EHR_REQUESTS.value
                        )

                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_failure_point_ehr_requests_month_2_1',
                        registration_event_datetime=create_date_time(date=report_start + timedelta(days=9),
                                                                     time="11:00:00"),
                        event_type=EventType.EHR_REQUESTS.value
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_failure_point_ehr_requests_month_2_1',
                        registration_event_datetime=create_date_time(date=report_start + timedelta(days=9),
                                                                     time="11:01:00"),
                        event_type=EventType.ERRORS.value,
                        payload=create_error_payload(
                            errorCode="06",
                            errorDescription="Not at surgery",
                            failurePoint=EventType.EHR_REQUESTS.value
                        )

                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_failure_point_ehr_requests_month_2_2',
                        registration_event_datetime=create_date_time(date=report_start + timedelta(days=9),
                                                                     time="11:00:00"),
                        event_type=EventType.EHR_REQUESTS.value
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_failure_point_ehr_requests_month_2_2',
                        registration_event_datetime=create_date_time(date=report_start + timedelta(days=9),
                                                                     time="11:01:00"),
                        event_type=EventType.ERRORS.value,
                        payload=create_error_payload(
                            errorCode="06",
                            errorDescription="Not at surgery",
                            failurePoint=EventType.EHR_REQUESTS.value
                        )

                    )),
                sourcetype="myevent")

            # Act
            test_query = self.generate_splunk_query_from_report(
                "gp2gp_technical_failures_trending_report/"
                "gp2gp_technical_failures_trending_failure_point_graph_count"
            )

            test_query = set_variables_on_query(
                test_query,
                {
                    "$index$": index_name,
                    "$start_time$": report_start.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    "$end_time$": report_end.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    "$cutoff$": cutoff,
                    "$time_period$": "month",
                    "$errorGraphColumn$": "06"
                },
            )

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service
            )
            self.LOG.info(f"telemetry: {telemetry}")

            # Assert
            time_period_month_1 = report_start.strftime("%Y-%m")
            time_period_month_2 = (report_start + timedelta(days=9)).strftime("%Y-%m")
            expected_values = {
                "0": {"time_period": time_period_month_1,
                      "EHR_REQUESTS": "1",
                      },
                "1": {"time_period": time_period_month_2,
                      "EHR_REQUESTS": "2",
                      },
            }

            for idx in range(len(expected_values)):
                for key, value in expected_values[str(idx)].items():
                    self.LOG.info(
                        f'.[{idx}] | select( ."{key}"=="{value}")'
                    )
                    assert jq.first(
                        f'.[{idx}] | select( ."{key}"=="{value}")',
                        telemetry,
                    )

        finally:
            self.delete_index(index_name)

    def test_failure_point_graph_time_period_token_week(self):
        # reporting window
        report_start = datetime.today().date().replace(day=1)
        report_end = report_start + timedelta(days=15)
        cutoff = "0"

        num_events = {"week_1": 2, "week_2": 4, "week_3": 3}
        try:
            # Arrange
            index_name, index = self.create_index()

            for idx in range(num_events["week_1"]):
                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id='test_failure_point_ehr_requests_week_1_'+str(idx),
                            registration_event_datetime=create_date_time(date=report_start, time="11:00:00"),
                            event_type=EventType.EHR_REQUESTS.value
                        )),
                    sourcetype="myevent")

                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id='test_failure_point_ehr_requests_week_1_'+str(idx),
                            registration_event_datetime=create_date_time(date=report_start, time="11:01:00"),
                            event_type=EventType.ERRORS.value,
                            payload=create_error_payload(
                                errorCode="06",
                                errorDescription="Not at surgery",
                                failurePoint=EventType.EHR_REQUESTS.value
                            )

                        )),
                    sourcetype="myevent")

            for idx in range(num_events["week_2"]):
                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id='test_failure_point_ehr_requests_week_2_'+str(idx),
                            registration_event_datetime=create_date_time(date=report_start + timedelta(days=7),
                                                                         time="11:00:00"),
                            event_type=EventType.EHR_REQUESTS.value
                        )),
                    sourcetype="myevent")

                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id='test_failure_point_ehr_requests_week_2_'+str(idx),
                            registration_event_datetime=create_date_time(date=report_start + timedelta(days=7),
                                                                         time="11:01:00"),
                            event_type=EventType.ERRORS.value,
                            payload=create_error_payload(
                                errorCode="06",
                                errorDescription="Not at surgery",
                                failurePoint=EventType.EHR_REQUESTS.value
                            )

                        )),
                    sourcetype="myevent")

            for idx in range(num_events["week_3"]):
                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id='test_failure_point_ehr_requests_week_3_'+str(idx),
                            registration_event_datetime=create_date_time(date=report_start + timedelta(days=14),
                                                                         time="11:00:00"),
                            event_type=EventType.EHR_REQUESTS.value
                        )),
                    sourcetype="myevent")

                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id='test_failure_point_ehr_requests_week_3_'+str(idx),
                            registration_event_datetime=create_date_time(date=report_start + timedelta(days=14),
                                                                         time="11:01:00"),
                            event_type=EventType.ERRORS.value,
                            payload=create_error_payload(
                                errorCode="06",
                                errorDescription="Not at surgery",
                                failurePoint=EventType.EHR_REQUESTS.value
                            )

                        )),
                    sourcetype="myevent")

            # Act
            test_query = self.generate_splunk_query_from_report(
                "gp2gp_technical_failures_trending_report/"
                "gp2gp_technical_failures_trending_failure_point_graph_count"
            )

            test_query = set_variables_on_query(
                test_query,
                {
                    "$index$": index_name,
                    "$start_time$": report_start.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    "$end_time$": report_end.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    "$cutoff$": cutoff,
                    "$time_period$": "week",
                    "$errorGraphColumn$": "06"
                },
            )

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service
            )
            self.LOG.info(f"telemetry: {telemetry}")

            # Assert
            time_period_week_1 = report_start.strftime("%Y-Wk%W")
            time_period_week_2 = (report_start + timedelta(days=7)).strftime("%Y-Wk%W")
            time_period_week_3 = (report_start + timedelta(days=14)).strftime("%Y-Wk%W")
            expected_values = {
                "0": {"time_period": time_period_week_1,
                      "EHR_REQUESTS": str(num_events["week_1"]),
                      },
                "1": {"time_period": time_period_week_2,
                      "EHR_REQUESTS": str(num_events["week_2"]),
                      },
                "2": {"time_period": time_period_week_3,
                      "EHR_REQUESTS": str(num_events["week_3"]),
                      },
            }

            for idx in range(len(expected_values)):
                for key, value in expected_values[str(idx)].items():
                    self.LOG.info(
                        f'.[{idx}] | select( ."{key}"=="{value}")'
                    )
                    assert jq.first(
                        f'.[{idx}] | select( ."{key}"=="{value}")',
                        telemetry,
                    )

        finally:
            self.delete_index(index_name)

    def test_failure_point_time_period_token_day(self):
        # reporting window
        report_start = datetime.today().date() - timedelta(days=5)
        report_end = datetime.today().date()
        cutoff = "0"

        num_events = {"day_1": 2, "day_2": 4, "day_3": 3}
        try:
            # Arrange
            index_name, index = self.create_index()

            for idx in range(num_events["day_1"]):
                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id='test_failure_point_ehr_requests_day_1_'+str(idx),
                            registration_event_datetime=create_date_time(date=report_start, time="11:00:00"),
                            event_type=EventType.EHR_REQUESTS.value
                        )),
                    sourcetype="myevent")

                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id='test_failure_point_ehr_requests_day_1_'+str(idx),
                            registration_event_datetime=create_date_time(date=report_start, time="11:01:00"),
                            event_type=EventType.ERRORS.value,
                            payload=create_error_payload(
                                errorCode="06",
                                errorDescription="Not at surgery",
                                failurePoint=EventType.EHR_REQUESTS.value
                            )

                        )),
                    sourcetype="myevent")

            for idx in range(num_events["day_2"]):
                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id='test_failure_point_ehr_requests_day_2_'+str(idx),
                            registration_event_datetime=create_date_time(date=report_start + timedelta(days=1),
                                                                         time="11:00:00"),
                            event_type=EventType.EHR_REQUESTS.value
                        )),
                    sourcetype="myevent")

                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id='test_failure_point_ehr_requests_day_2_'+str(idx),
                            registration_event_datetime=create_date_time(date=report_start + timedelta(days=1),
                                                                         time="11:01:00"),
                            event_type=EventType.ERRORS.value,
                            payload=create_error_payload(
                                errorCode="06",
                                errorDescription="Not at surgery",
                                failurePoint=EventType.EHR_REQUESTS.value
                            )

                        )),
                    sourcetype="myevent")

            for idx in range(num_events["day_3"]):
                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id='test_failure_point_ehr_requests_day_3_'+str(idx),
                            registration_event_datetime=create_date_time(date=report_start + timedelta(days=2),
                                                                         time="11:00:00"),
                            event_type=EventType.EHR_REQUESTS.value
                        )),
                    sourcetype="myevent")

                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id='test_failure_point_ehr_requests_day_3_'+str(idx),
                            registration_event_datetime=create_date_time(date=report_start + timedelta(days=2),
                                                                         time="11:01:00"),
                            event_type=EventType.ERRORS.value,
                            payload=create_error_payload(
                                errorCode="06",
                                errorDescription="Not at surgery",
                                failurePoint=EventType.EHR_REQUESTS.value
                            )

                        )),
                    sourcetype="myevent")

            # Act
            test_query = self.generate_splunk_query_from_report(
                "gp2gp_technical_failures_trending_report/"
                "gp2gp_technical_failures_trending_failure_point_graph_count"
            )

            test_query = set_variables_on_query(
                test_query,
                {
                    "$index$": index_name,
                    "$start_time$": report_start.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    "$end_time$": report_end.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    "$cutoff$": cutoff,
                    "$time_period$": "day",
                    "$errorGraphColumn$": "06"
                },
            )

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service
            )
            self.LOG.info(f"telemetry: {telemetry}")

            # Assert
            time_period_day_1 = report_start.strftime("%Y-%m-%d")
            time_period_day_2 = (report_start + timedelta(days=1)).strftime("%Y-%m-%d")
            time_period_day_3 = (report_start + timedelta(days=2)).strftime("%Y-%m-%d")
            expected_values = {
                "0": {"time_period": time_period_day_1,
                      "EHR_REQUESTS": str(num_events["day_1"]),
                      },
                "1": {"time_period": time_period_day_2,
                      "EHR_REQUESTS": str(num_events["day_2"]),
                      },
                "2": {"time_period": time_period_day_3,
                      "EHR_REQUESTS": str(num_events["day_3"]),
                      },
            }

            for idx in range(len(expected_values)):
                for key, value in expected_values[str(idx)].items():
                    self.LOG.info(
                        f'.[{idx}] | select( ."{key}"=="{value}")'
                    )
                    assert jq.first(
                        f'.[{idx}] | select( ."{key}"=="{value}")',
                        telemetry,
                    )

        finally:
            self.delete_index(index_name)
