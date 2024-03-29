import logging
import os
from collections import OrderedDict
from enum import Enum
import pytest
import json
from time import sleep
from splunklib import client
import jq

from helpers.datetime_helper import datetime_utc_now, create_date_time
from helpers.splunk \
    import get_telemetry_from_splunk, get_or_create_index, create_sample_event, set_variables_on_query, \
    create_integration_payload, create_error_payload, create_transfer_compatibility_payload, create_registration_payload
from datetime import datetime, timedelta
from jinja2 import Environment, FileSystemLoader
from tests.test_base import TestBase, EventType


class TestErrorsSnapshotReportOutputs(TestBase):

    def test_gp2gp_errors_snapshot_report_error_graph_count(self):

        # reporting window
        report_start = datetime.today().date().replace(day=1)
        report_end = datetime.today().date().replace(day=28)
        cutoff = "0"

        try:
            # Arrange
            index_name, index = self.create_index()

            NUM_OF_ERROR_TYPES = {"registrations_error": (2, "06"),
                                  "transfer_compatibility_error": (3, "07"),
                                  "ehr_request_error": (1, "09"),
                                  "ehr_response_error": (4, "20"),
                                  "ready_to_integrate_error": (2, "21"),
                                  "integration_error": (2, "31"),
                                  }

            # registrations error
            for idx in range(NUM_OF_ERROR_TYPES["registrations_error"][0]):
                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id='test_registrations' + str(idx),
                            registration_event_datetime=create_date_time(date=report_start, time="11:00:00"),
                            event_type=EventType.REGISTRATIONS.value,
                            payload=create_registration_payload()
                        )),
                    sourcetype="myevent")

                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id='test_registrations' + str(idx),
                            registration_event_datetime=create_date_time(date=report_start, time="11:01:00"),
                            event_type=EventType.ERRORS.value,
                            payload=create_error_payload(
                                errorCode=NUM_OF_ERROR_TYPES["registrations_error"][1],
                                errorDescription="EHR Extract received without corresponding request",
                                failurePoint=EventType.REGISTRATIONS.value
                            )

                        )),
                    sourcetype="myevent")

            # trans compat error
            for idx in range(NUM_OF_ERROR_TYPES["transfer_compatibility_error"][0]):
                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id='test_transfer_compatibility' + str(idx),
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
                            conversation_id='test_transfer_compatibility' + str(idx),
                            registration_event_datetime=create_date_time(date=report_start, time="11:01:00"),
                            event_type=EventType.ERRORS.value,
                            payload=create_error_payload(
                                errorCode=NUM_OF_ERROR_TYPES["transfer_compatibility_error"][1],
                                errorDescription="EHR Extract received without corresponding request",
                                failurePoint=EventType.TRANSFER_COMPATIBILITY_STATUSES.value
                            )

                        )),
                    sourcetype="myevent")

            # EHR requests error
            for idx in range(NUM_OF_ERROR_TYPES["ehr_request_error"][0]):
                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id='test_ehr_requests' + str(idx),
                            registration_event_datetime=create_date_time(date=report_start, time="11:00:00"),
                            event_type=EventType.EHR_REQUESTS.value
                        )),
                    sourcetype="myevent")

                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id='test_ehr_requests' + str(idx),
                            registration_event_datetime=create_date_time(date=report_start, time="11:01:00"),
                            event_type=EventType.ERRORS.value,
                            payload=create_error_payload(
                                errorCode=NUM_OF_ERROR_TYPES["ehr_request_error"][1],
                                errorDescription="Not at surgery",
                                failurePoint=EventType.EHR_REQUESTS.value
                            )

                        )),
                    sourcetype="myevent")

            # EHR response error
            for idx in range(NUM_OF_ERROR_TYPES["ehr_response_error"][0]):
                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id='test_ehr_response' + str(idx),
                            registration_event_datetime=create_date_time(date=report_start, time="11:00:00"),
                            event_type=EventType.EHR_RESPONSES.value
                        )),
                    sourcetype="myevent")

                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id='test_ehr_response' + str(idx),
                            registration_event_datetime=create_date_time(date=report_start, time="11:01:00"),
                            event_type=EventType.ERRORS.value,
                            payload=create_error_payload(
                                errorCode=NUM_OF_ERROR_TYPES["ehr_response_error"][1],
                                errorDescription="GP2GP Messaging is not enabled on this system",
                                failurePoint=EventType.EHR_RESPONSES.value
                            )

                        )),
                    sourcetype="myevent")

            # ready to integrate error
            for idx in range(NUM_OF_ERROR_TYPES["ready_to_integrate_error"][0]):
                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id='test_ready_to_integrate' + str(idx),
                            registration_event_datetime=create_date_time(date=report_start, time="11:00:00"),
                            event_type=EventType.READY_TO_INTEGRATE_STATUSES.value
                        )),
                    sourcetype="myevent")

                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id='test_ready_to_integrate' + str(idx),
                            registration_event_datetime=create_date_time(date=report_start, time="11:01:00"),
                            event_type=EventType.ERRORS.value,
                            payload=create_error_payload(
                                errorCode=NUM_OF_ERROR_TYPES["ready_to_integrate_error"][1],
                                errorDescription="random error",
                                failurePoint=EventType.READY_TO_INTEGRATE_STATUSES.value
                            )

                        )),
                    sourcetype="myevent")

            # integration error
            for idx in range(NUM_OF_ERROR_TYPES["integration_error"][0]):
                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id='test_integration_error' + str(idx),
                            registration_event_datetime=create_date_time(date=report_start, time="11:00:00"),
                            event_type=EventType.EHR_INTEGRATIONS.value
                        )),
                    sourcetype="myevent")

                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id='test_integration_error' + str(idx),
                            registration_event_datetime=create_date_time(date=report_start, time="11:01:00"),
                            event_type=EventType.ERRORS.value,
                            payload=create_error_payload(
                                errorCode=NUM_OF_ERROR_TYPES["integration_error"][1],
                                errorDescription="random error",
                                failurePoint=EventType.EHR_INTEGRATIONS.value
                            )

                        )),
                    sourcetype="myevent")

            # Act
            test_query = self.generate_splunk_query_from_report(
                'gp2gp_errors_snapshot_report'
                '/gp2gp_errors_snapshot_error_graph_count')

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
            # has to be this order as "chart" command arranges columns in alphabetical order
            expected_values = {"0": {"errorCode": str(NUM_OF_ERROR_TYPES["registrations_error"][1]),
                                     "count": str(NUM_OF_ERROR_TYPES["registrations_error"][0])},
                               "1": {"errorCode": str(NUM_OF_ERROR_TYPES["transfer_compatibility_error"][1]),
                                     "count": str(NUM_OF_ERROR_TYPES["transfer_compatibility_error"][0])},
                               "2": {"errorCode": str(NUM_OF_ERROR_TYPES["ehr_request_error"][1]),
                                     "count": str(NUM_OF_ERROR_TYPES["ehr_request_error"][0])},
                               "3": {"errorCode": str(NUM_OF_ERROR_TYPES["ehr_response_error"][1]),
                                     "count": str(NUM_OF_ERROR_TYPES["ehr_response_error"][0])},
                               "4": {"errorCode": str(NUM_OF_ERROR_TYPES["ready_to_integrate_error"][1]),
                                     "count": str(NUM_OF_ERROR_TYPES["ready_to_integrate_error"][0])},
                               "5": {"errorCode": str(NUM_OF_ERROR_TYPES["integration_error"][1]),
                                     "count": str(NUM_OF_ERROR_TYPES["integration_error"][0])}
                               }

            for row, row_values in expected_values.items():
                row_values_as_jq_str = ' '.join(
                    [f"| select(.\"{key}\"==\"{value}\") " for key, value in row_values.items()]
                )
                self.LOG.info(f'.[{row}] {row_values_as_jq_str} ')
                assert jq.first(
                    f'.[{row}] {row_values_as_jq_str} ', telemetry)

        finally:
            self.delete_index(index_name)

    def test_gp2gp_errors_snapshot_report_error_graph_count_2_errors_1_conv(self):

        # reporting window
        report_start = datetime.today().date().replace(day=1)
        report_end = datetime.today().date().replace(day=28)
        cutoff = "0"

        try:
            # Arrange
            index_name, index = self.create_index()

            # technical_failure 1
            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_errors_1',
                        registration_event_datetime=create_date_time(date=report_start, time="11:00:00"),
                        event_type=EventType.EHR_REQUESTS.value
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_errors_1',
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
                        conversation_id='test_errors_1',
                        registration_event_datetime=create_date_time(date=report_start, time="11:02:00"),
                        event_type=EventType.EHR_RESPONSES.value
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_errors_1',
                        registration_event_datetime=create_date_time(date=report_start, time="11:03:00"),
                        event_type=EventType.ERRORS.value,
                        payload=create_error_payload(
                            errorCode="07",
                            errorDescription="fake error",
                            failurePoint=EventType.EHR_RESPONSES.value
                        )

                    )),
                sourcetype="myevent")

            # Act
            test_query = self.generate_splunk_query_from_report(
                'gp2gp_errors_snapshot_report'
                '/gp2gp_errors_snapshot_error_graph_count')

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
            # has to be this order as "chart" command arranges columns in alphabetical order
            expected_values = {"0": {"errorCode": "06",
                                     "count": "1"},
                               "1": {"errorCode": "07",
                                     "count": "1"},
                               }

            for row, row_values in expected_values.items():
                row_values_as_jq_str = ' '.join(
                    [f"| select(.\"{key}\"==\"{value}\") " for key, value in row_values.items()]
                )
                self.LOG.info(f'.[{row}] {row_values_as_jq_str} ')
                assert jq.first(
                    f'.[{row}] {row_values_as_jq_str} ', telemetry)

        finally:
            self.delete_index(index_name)

    def test_gp2gp_errors_snapshot_report_error_graph_percentage(self):

        # reporting window
        report_start = datetime.today().date().replace(day=1)
        report_end = datetime.today().date().replace(day=28)
        cutoff = "0"

        try:
            # Arrange
            index_name, index = self.create_index()

            NUM_OF_ERROR_TYPES = {"registrations_error": (2, "06"),
                                  "transfer_compatibility_error": (3, "07"),
                                  "ehr_request_error": (1, "09"),
                                  "ehr_response_error": (4, "20"),
                                  "ready_to_integrate_error": (2, "21"),
                                  "integration_error": (2, "31"),
                                  }
            total_num_errors = sum([i for (i, _) in NUM_OF_ERROR_TYPES.values()])

            # registrations error
            for idx in range(NUM_OF_ERROR_TYPES["registrations_error"][0]):
                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id='test_registrations' + str(idx),
                            registration_event_datetime=create_date_time(date=report_start, time="11:00:00"),
                            event_type=EventType.REGISTRATIONS.value,
                            payload=create_registration_payload()
                        )),
                    sourcetype="myevent")

                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id='test_registrations' + str(idx),
                            registration_event_datetime=create_date_time(date=report_start, time="11:01:00"),
                            event_type=EventType.ERRORS.value,
                            payload=create_error_payload(
                                errorCode=NUM_OF_ERROR_TYPES["registrations_error"][1],
                                errorDescription="EHR Extract received without corresponding request",
                                failurePoint=EventType.REGISTRATIONS.value
                            )

                        )),
                    sourcetype="myevent")

            # trans compat error
            for idx in range(NUM_OF_ERROR_TYPES["transfer_compatibility_error"][0]):
                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id='test_transfer_compatibility' + str(idx),
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
                            conversation_id='test_transfer_compatibility' + str(idx),
                            registration_event_datetime=create_date_time(date=report_start, time="11:01:00"),
                            event_type=EventType.ERRORS.value,
                            payload=create_error_payload(
                                errorCode=NUM_OF_ERROR_TYPES["transfer_compatibility_error"][1],
                                errorDescription="EHR Extract received without corresponding request",
                                failurePoint=EventType.TRANSFER_COMPATIBILITY_STATUSES.value
                            )

                        )),
                    sourcetype="myevent")

            # EHR requests error
            for idx in range(NUM_OF_ERROR_TYPES["ehr_request_error"][0]):
                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id='test_ehr_requests' + str(idx),
                            registration_event_datetime=create_date_time(date=report_start, time="11:00:00"),
                            event_type=EventType.EHR_REQUESTS.value
                        )),
                    sourcetype="myevent")

                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id='test_ehr_requests' + str(idx),
                            registration_event_datetime=create_date_time(date=report_start, time="11:01:00"),
                            event_type=EventType.ERRORS.value,
                            payload=create_error_payload(
                                errorCode=NUM_OF_ERROR_TYPES["ehr_request_error"][1],
                                errorDescription="Not at surgery",
                                failurePoint=EventType.EHR_REQUESTS.value
                            )

                        )),
                    sourcetype="myevent")

            # EHR response error
            for idx in range(NUM_OF_ERROR_TYPES["ehr_response_error"][0]):
                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id='test_ehr_response' + str(idx),
                            registration_event_datetime=create_date_time(date=report_start, time="11:00:00"),
                            event_type=EventType.EHR_RESPONSES.value
                        )),
                    sourcetype="myevent")

                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id='test_ehr_response' + str(idx),
                            registration_event_datetime=create_date_time(date=report_start, time="11:01:00"),
                            event_type=EventType.ERRORS.value,
                            payload=create_error_payload(
                                errorCode=NUM_OF_ERROR_TYPES["ehr_response_error"][1],
                                errorDescription="GP2GP Messaging is not enabled on this system",
                                failurePoint=EventType.EHR_RESPONSES.value
                            )

                        )),
                    sourcetype="myevent")

            # ready to integrate error
            for idx in range(NUM_OF_ERROR_TYPES["ready_to_integrate_error"][0]):
                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id='test_ready_to_integrate' + str(idx),
                            registration_event_datetime=create_date_time(date=report_start, time="11:00:00"),
                            event_type=EventType.READY_TO_INTEGRATE_STATUSES.value
                        )),
                    sourcetype="myevent")

                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id='test_ready_to_integrate' + str(idx),
                            registration_event_datetime=create_date_time(date=report_start, time="11:01:00"),
                            event_type=EventType.ERRORS.value,
                            payload=create_error_payload(
                                errorCode=NUM_OF_ERROR_TYPES["ready_to_integrate_error"][1],
                                errorDescription="random error",
                                failurePoint=EventType.READY_TO_INTEGRATE_STATUSES.value
                            )

                        )),
                    sourcetype="myevent")

            # integration error
            for idx in range(NUM_OF_ERROR_TYPES["integration_error"][0]):
                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id='test_integration_error' + str(idx),
                            registration_event_datetime=create_date_time(date=report_start, time="11:00:00"),
                            event_type=EventType.EHR_INTEGRATIONS.value
                        )),
                    sourcetype="myevent")

                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id='test_integration_error' + str(idx),
                            registration_event_datetime=create_date_time(date=report_start, time="11:01:00"),
                            event_type=EventType.ERRORS.value,
                            payload=create_error_payload(
                                errorCode=NUM_OF_ERROR_TYPES["integration_error"][1],
                                errorDescription="random error",
                                failurePoint=EventType.EHR_INTEGRATIONS.value
                            )

                        )),
                    sourcetype="myevent")

            # Act
            test_query = self.generate_splunk_query_from_report(
                'gp2gp_errors_snapshot_report/'
                'gp2gp_errors_snapshot_error_graph_percentage')

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
            # has to be this order as "chart" command arranges columns in alphabetical order
            expected_values = {"0": {"errorCode": str(NUM_OF_ERROR_TYPES["registrations_error"][1]),
                                     "percentage": str(
                                         round(NUM_OF_ERROR_TYPES["registrations_error"][0] * 100/total_num_errors, 2)
                                     )},
                               "1": {"errorCode": str(NUM_OF_ERROR_TYPES["transfer_compatibility_error"][1]),
                                     "percentage": str(
                                         round(NUM_OF_ERROR_TYPES["transfer_compatibility_error"][0]
                                               * 100/total_num_errors, 2)
                                               )},
                               "2": {"errorCode": str(NUM_OF_ERROR_TYPES["ehr_request_error"][1]),
                                     "percentage": str(
                                         round(NUM_OF_ERROR_TYPES["ehr_request_error"][0] * 100/total_num_errors, 2)
                                               )},
                               "3": {"errorCode": str(NUM_OF_ERROR_TYPES["ehr_response_error"][1]),
                                     "percentage": str(
                                         round(NUM_OF_ERROR_TYPES["ehr_response_error"][0] * 100/total_num_errors, 2)
                                               )},
                               "4": {"errorCode": str(NUM_OF_ERROR_TYPES["ready_to_integrate_error"][1]),
                                     "percentage": str(
                                         round(NUM_OF_ERROR_TYPES["ready_to_integrate_error"][0]
                                               * 100/total_num_errors, 2)
                                               )},
                               "5": {"errorCode": str(NUM_OF_ERROR_TYPES["integration_error"][1]),
                                     "percentage": str(
                                         round(NUM_OF_ERROR_TYPES["integration_error"][0] * 100/total_num_errors, 2)
                                               )}
                               }

            for row, row_values in expected_values.items():
                row_values_as_jq_str = ' '.join(
                    [f"| select(.\"{key}\"==\"{value}\") " for key, value in row_values.items()]
                )
                self.LOG.info(f'.[{row}] {row_values_as_jq_str} ')
                assert jq.first(
                    f'.[{row}] {row_values_as_jq_str} ', telemetry)

        finally:
            self.delete_index(index_name)

    def test_gp2gp_errors_snapshot_report_error_graph_percentage_2_errors_1_conv(self):

        # reporting window
        report_start = datetime.today().date().replace(day=1)
        report_end = datetime.today().date().replace(day=28)
        cutoff = "0"

        try:
            # Arrange
            index_name, index = self.create_index()

            # technical_failure 1
            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_error_1',
                        registration_event_datetime=create_date_time(date=report_start, time="11:00:00"),
                        event_type=EventType.EHR_REQUESTS.value
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_error_1',
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
                        conversation_id='test_error_1',
                        registration_event_datetime=create_date_time(date=report_start, time="11:02:00"),
                        event_type=EventType.EHR_RESPONSES.value
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_error_1',
                        registration_event_datetime=create_date_time(date=report_start, time="11:03:00"),
                        event_type=EventType.ERRORS.value,
                        payload=create_error_payload(
                            errorCode="07",
                            errorDescription="fake error",
                            failurePoint=EventType.EHR_RESPONSES.value
                        )

                    )),
                sourcetype="myevent")

            # Act
            test_query = self.generate_splunk_query_from_report(
                'gp2gp_errors_snapshot_report'
                '/gp2gp_errors_snapshot_error_graph_percentage')

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
            # has to be this order as "chart" command arranges columns in alphabetical order
            expected_values = {"0": {"errorCode": "06",
                                     "percentage": "50.00"},
                               "1": {"errorCode": "07",
                                     "percentage": "50.00"},
                               }

            for row, row_values in expected_values.items():
                row_values_as_jq_str = ' '.join(
                    [f"| select(.\"{key}\"==\"{value}\") " for key, value in row_values.items()]
                )
                self.LOG.info(f'.[{row}] {row_values_as_jq_str} ')
                assert jq.first(
                    f'.[{row}] {row_values_as_jq_str} ', telemetry)

        finally:
            self.delete_index(index_name)

    @pytest.mark.parametrize("clicked_column", ["06", "07", "09"])
    def test_gp2gp_errors_snapshot_report_failure_point_graph_count(self, clicked_column):

        # reporting window
        report_start = datetime.today().date().replace(day=1)
        report_end = datetime.today().date().replace(day=28)
        cutoff = "0"

        try:
            # Arrange
            index_name, index = self.create_index()

            # order needs to be alphabetical for test to pass as chart orders columns in this way
            failure_points_and_amounts = [
                ("EHR Ready to Integrate", 3),
                ("EHR Requested", 2),
                ("EHR Response", 1),
                ("Endpoint Lookup", 3),
                ("Other", 2),
                ("Patient General Update", 4),
                ("Patient Trace", 1)
            ]

            expected_vals = OrderedDict()

            for idx, (failure_point, amount) in enumerate(failure_points_and_amounts):
                # technical_failure
                for amount_idx in range(amount):
                    index.submit(
                        json.dumps(
                            create_sample_event(
                                conversation_id='test_failure_point_graph_'+clicked_column+str(amount_idx),
                                registration_event_datetime=create_date_time(date=report_start, time="11:00:00"),
                                event_type=EventType.EHR_REQUESTS.value
                            )),
                        sourcetype="myevent")

                    index.submit(
                        json.dumps(
                            create_sample_event(
                                conversation_id='test_failure_point_graph_'+clicked_column+str(amount_idx),
                                registration_event_datetime=create_date_time(date=report_start, time="11:01:00"),
                                event_type=EventType.ERRORS.value,
                                payload=create_error_payload(
                                    errorCode=clicked_column,
                                    errorDescription="Random desc",
                                    failurePoint=failure_point
                                )

                            )),
                        sourcetype="myevent")

                expected_vals[idx] = {"failure_point": failure_point, "count": amount}

            # awaiting_integration
            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_failure_point_graph_awaiting_integration_not_error',
                        registration_event_datetime=create_date_time(date=report_start, time="10:00:00"),
                        event_type=EventType.READY_TO_INTEGRATE_STATUSES.value
                    )),
                sourcetype="myevent")

            # Act
            test_query = self.generate_splunk_query_from_report(
                'gp2gp_errors_snapshot_report'
                '/gp2gp_errors_snapshot_failure_point_graph_count')

            test_query = set_variables_on_query(test_query, {
                "$index$": index_name,
                "$start_time$": report_start.strftime("%Y-%m-%dT%H:%m:%s"),
                "$end_time$": report_end.strftime("%Y-%m-%dT%H:%m:%s"),
                "$cutoff$": cutoff,
                "$errorGraphColumn$": clicked_column,
            })

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service)
            self.LOG.info(f'telemetry: {telemetry}')

            # Assert
            for row, row_values in expected_vals.items():
                row_values_as_jq_str = ' '.join(
                    [f"| select(.\"{key}\"==\"{value}\") " for key, value in row_values.items()]
                )
                self.LOG.info(f'.[{row}] {row_values_as_jq_str} ')
                assert jq.first(
                    f'.[{row}] {row_values_as_jq_str} ', telemetry)

        finally:
            self.delete_index(index_name)

    @pytest.mark.parametrize("clicked_column, expected_val",
                             [("06", {"failure_point": "EHR Response", "count": "1"}),
                              ("09", {"failure_point": "Other", "count": "1"})])
    def test_gp2gp_errors_snapshot_report_failure_point_graph_count_2_failure_points_1_conv(self,
                                                                                            clicked_column,
                                                                                            expected_val):

        # reporting window
        report_start = datetime.today().date().replace(day=1)
        report_end = datetime.today().date().replace(day=28)
        cutoff = "0"

        try:
            # Arrange
            index_name, index = self.create_index()

            # order needs to be alphabetical for test to pass as chart orders columns in this way
            failure_points_and_amounts = [
                ("EHR Ready to Integrate", 3),
                ("EHR Requested", 2),
                ("EHR Response", 1),
                ("Endpoint Lookup", 3),
                ("Other", 2),
                ("Patient General Update", 4),
                ("Patient Trace", 1)
            ]

            expected_vals = OrderedDict()

            # error code 06
            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_multiple_failure_points',
                        registration_event_datetime=create_date_time(date=report_start, time="11:00:00"),
                        event_type=EventType.EHR_REQUESTS.value
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_multiple_failure_points',
                        registration_event_datetime=create_date_time(date=report_start, time="11:01:00"),
                        event_type=EventType.ERRORS.value,
                        payload=create_error_payload(
                            errorCode="06",
                            errorDescription="Random desc",
                            failurePoint="EHR Response"
                        )

                    )),
                sourcetype="myevent")

            # FAILED_TO_INTEGRATE
            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_failure_point_graph_EHR_Integration_with_error',
                        registration_event_datetime=create_date_time(date=report_start, time="11:00:00"),
                        event_type=EventType.EHR_INTEGRATIONS.value,
                        payload=create_integration_payload(outcome="FAILED_TO_INTEGRATE")
                    )),
                sourcetype="myevent")

            sample_event = create_sample_event(
                conversation_id='test_failure_point_graph_EHR_Integration_with_error',
                registration_event_datetime=create_date_time(date=report_start, time="11:01:00"),
                event_type=EventType.ERRORS.value,
                payload=create_error_payload(
                    errorCode="31",
                    errorDescription="Random desc",
                    failurePoint="EHR_INTEGRATION"
                )
            )

            index.submit(
                json.dumps(
                    sample_event
                ),
                sourcetype="myevent")

            # error code 09
            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_multiple_failure_points',
                        registration_event_datetime=create_date_time(date=report_start, time="11:00:00"),
                        event_type=EventType.EHR_RESPONSES.value
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_multiple_failure_points',
                        registration_event_datetime=create_date_time(date=report_start, time="11:01:00"),
                        event_type=EventType.ERRORS.value,
                        payload=create_error_payload(
                            errorCode="09",
                            errorDescription="Random desc",
                            failurePoint="Other"
                        )

                    )),
                sourcetype="myevent")


            # Act
            test_query = self.generate_splunk_query_from_report(
                'gp2gp_errors_snapshot_report'
                '/gp2gp_errors_snapshot_failure_point_graph_count')

            test_query = set_variables_on_query(test_query, {
                "$index$": index_name,
                "$start_time$": report_start.strftime("%Y-%m-%dT%H:%m:%s"),
                "$end_time$": report_end.strftime("%Y-%m-%dT%H:%m:%s"),
                "$cutoff$": cutoff,
                "$errorGraphColumn$": clicked_column,
            })

            expected_vals["0"] = expected_val

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service)
            self.LOG.info(f'telemetry: {telemetry}')

            # Assert
            for row, row_values in expected_vals.items():
                row_values_as_jq_str = ' '.join(
                    [f"| select(.\"{key}\"==\"{value}\") " for key, value in row_values.items()]
                )
                self.LOG.info(f'.[{row}] {row_values_as_jq_str} ')
                assert jq.first(
                    f'.[{row}] {row_values_as_jq_str} ', telemetry)

        finally:
            self.delete_index(index_name)

    @pytest.mark.parametrize("clicked_column", ["06", "07", "09"])
    def test_gp2gp_errors_snapshot_report_failure_point_graph_percentage(self, clicked_column):

        # reporting window
        report_start = datetime.today().date().replace(day=1)
        report_end = datetime.today().date().replace(day=28)
        cutoff = "0"

        try:
            # Arrange
            index_name, index = self.create_index()

            expected_vals = OrderedDict()

            if clicked_column == "Integration failure":
                # technical_failure

                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id='test_failure_point_graph_EHR_Integration_with_error',
                            registration_event_datetime=create_date_time(date=report_start, time="09:00:00"),
                            event_type=EventType.EHR_INTEGRATIONS.value,
                            payload=create_integration_payload(outcome="FAILED_TO_INTEGRATE")
                        )),
                    sourcetype="myevent")

                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id='test_failure_point_graph_EHR_Integration_with_error',
                            registration_event_datetime=create_date_time(date=report_start, time="11:01:00"),
                            event_type=EventType.ERRORS.value,
                            payload=create_error_payload(
                                errorCode="31",
                                errorDescription="Random desc",
                                failurePoint="EHR_INTEGRATION"
                            )

                        )),
                    sourcetype="myevent")

                # should give failure point as EHR Integration
                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id='test_failure_point_graph_EHR_Integration_without_error',
                            registration_event_datetime=create_date_time(date=report_start, time="09:00:00"),
                            event_type=EventType.EHR_INTEGRATIONS.value,
                            payload=create_integration_payload(outcome="FAILED_TO_INTEGRATE")
                        )),
                    sourcetype="myevent")

                # need to be this order as chart organises columns by alphabetical order
                expected_vals["0"] = {"failure_point": "EHR_INTEGRATION", "percentage": "100.00"}

            elif clicked_column == "Unknown":

                # unknown failure point
                sample_event_without_failure_point = create_sample_event(
                    conversation_id='test_failure_point_graph_unknown',
                    registration_event_datetime=create_date_time(date=report_start, time="11:01:00"),
                    event_type=EventType.ERRORS.value,
                    payload=create_error_payload(
                        errorCode="06",
                        errorDescription="Random desc",
                        failurePoint="EHR Response"
                    )

                )
                del sample_event_without_failure_point["payload"]["error"]["failurePoint"]

                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id='test_failure_point_graph_unknown',
                            registration_event_datetime=create_date_time(date=report_start, time="11:00:00"),
                            event_type=EventType.EHR_REQUESTS.value
                        )),
                    sourcetype="myevent")

                index.submit(
                    json.dumps(
                        sample_event_without_failure_point
                    ),
                    sourcetype="myevent")

                expected_vals["0"] = {"failure_point": "UNKNOWN", "percentage": "100.00"}

            else:
                # order needs to be alphabetical for test to pass as chart orders columns in this way
                failure_points_and_amounts = [
                    ("EHR Ready to Integrate", 3),
                    ("EHR Requested", 2),
                    ("EHR Response", 1),
                    ("Endpoint Lookup", 3),
                    ("Other", 2),
                    ("Patient General Update", 4),
                    ("Patient Trace", 1)
                ]

                _, amounts = zip(*failure_points_and_amounts)
                total_events = sum(amounts)

                for idx, (failure_point, amount) in enumerate(failure_points_and_amounts):
                    # technical_failure
                    for amount_idx in range(amount):
                        index.submit(
                            json.dumps(
                                create_sample_event(
                                    conversation_id='test_failure_point_graph_'+clicked_column+str(amount_idx),
                                    registration_event_datetime=create_date_time(date=report_start, time="11:00:00"),
                                    event_type=EventType.EHR_REQUESTS.value
                                )),
                            sourcetype="myevent")

                        index.submit(
                            json.dumps(
                                create_sample_event(
                                    conversation_id='test_failure_point_graph_'+clicked_column+str(amount_idx),
                                    registration_event_datetime=create_date_time(date=report_start, time="11:01:00"),
                                    event_type=EventType.ERRORS.value,
                                    payload=create_error_payload(
                                        errorCode=clicked_column,
                                        errorDescription="Random desc",
                                        failurePoint=failure_point
                                    )

                                )),
                            sourcetype="myevent")

                    expected_vals[idx] = {"failure_point": failure_point,
                                          "percentage": f'{(amount / total_events) * 100:.2f}'}

            # awaiting_integration
            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_failure_point_graph_awaiting_integration_not_error',
                        registration_event_datetime=create_date_time(date=report_start, time="10:00:00"),
                        event_type=EventType.READY_TO_INTEGRATE_STATUSES.value
                    )),
                sourcetype="myevent")

            # Act
            test_query = self.generate_splunk_query_from_report(
                'gp2gp_errors_snapshot_report'
                '/gp2gp_errors_snapshot_failure_point_graph_percentage')

            test_query = set_variables_on_query(test_query, {
                "$index$": index_name,
                "$start_time$": report_start.strftime("%Y-%m-%dT%H:%m:%s"),
                "$end_time$": report_end.strftime("%Y-%m-%dT%H:%m:%s"),
                "$cutoff$": cutoff,
                "$errorGraphColumn$": clicked_column,
            })

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service)
            self.LOG.info(f'telemetry: {telemetry}')

            # Assert
            for row, row_values in expected_vals.items():
                row_values_as_jq_str = ' '.join(
                    [f"| select(.\"{key}\"==\"{value}\") " for key, value in row_values.items()]
                )
                self.LOG.info(f'.[{row}] {row_values_as_jq_str} ')
                assert jq.first(
                    f'.[{row}] {row_values_as_jq_str} ', telemetry)

        finally:
            self.delete_index(index_name)

    @pytest.mark.parametrize("clicked_column, expected_val",
                             [("06", {"failure_point": "EHR Response", "percentage": "100.00"}),
                              ("09", {"failure_point": "Other", "percentage": "100.00"})])
    def test_gp2gp_errors_snapshot_report_failure_point_graph_percentage_2_failure_points_1_conv(self,
                                                                                                 clicked_column,
                                                                                                 expected_val):

        # reporting window
        report_start = datetime.today().date().replace(day=1)
        report_end = datetime.today().date().replace(day=28)
        cutoff = "0"

        try:
            # Arrange
            index_name, index = self.create_index()

            # order needs to be alphabetical for test to pass as chart orders columns in this way
            failure_points_and_amounts = [
                ("EHR Ready to Integrate", 3),
                ("EHR Requested", 2),
                ("EHR Response", 1),
                ("Endpoint Lookup", 3),
                ("Other", 2),
                ("Patient General Update", 4),
                ("Patient Trace", 1)
            ]

            expected_vals = OrderedDict()

            # error code 06
            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_multiple_failure_points',
                        registration_event_datetime=create_date_time(date=report_start, time="11:00:00"),
                        event_type=EventType.EHR_REQUESTS.value
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_multiple_failure_points',
                        registration_event_datetime=create_date_time(date=report_start, time="11:01:00"),
                        event_type=EventType.ERRORS.value,
                        payload=create_error_payload(
                            errorCode="06",
                            errorDescription="Random desc",
                            failurePoint="EHR Response"
                        )

                    )),
                sourcetype="myevent")

            # FAILED_TO_INTEGRATE
            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_failure_point_graph_EHR_Integration_with_error',
                        registration_event_datetime=create_date_time(date=report_start, time="11:00:00"),
                        event_type=EventType.EHR_INTEGRATIONS.value,
                        payload=create_integration_payload(outcome="FAILED_TO_INTEGRATE")
                    )),
                sourcetype="myevent")

            sample_event = create_sample_event(
                conversation_id='test_failure_point_graph_EHR_Integration_with_error',
                registration_event_datetime=create_date_time(date=report_start, time="11:01:00"),
                event_type=EventType.ERRORS.value,
                payload=create_error_payload(
                    errorCode="31",
                    errorDescription="Random desc",
                    failurePoint="EHR_INTEGRATION"
                )
            )

            index.submit(
                json.dumps(
                    sample_event
                ),
                sourcetype="myevent")

            # error code 09
            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_multiple_failure_points',
                        registration_event_datetime=create_date_time(date=report_start, time="11:00:00"),
                        event_type=EventType.EHR_RESPONSES.value
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_multiple_failure_points',
                        registration_event_datetime=create_date_time(date=report_start, time="11:01:00"),
                        event_type=EventType.ERRORS.value,
                        payload=create_error_payload(
                            errorCode="09",
                            errorDescription="Random desc",
                            failurePoint="Other"
                        )

                    )),
                sourcetype="myevent")


            # Act
            test_query = self.generate_splunk_query_from_report(
                'gp2gp_errors_snapshot_report'
                '/gp2gp_errors_snapshot_failure_point_graph_percentage')

            test_query = set_variables_on_query(test_query, {
                "$index$": index_name,
                "$start_time$": report_start.strftime("%Y-%m-%dT%H:%m:%s"),
                "$end_time$": report_end.strftime("%Y-%m-%dT%H:%m:%s"),
                "$cutoff$": cutoff,
                "$errorGraphColumn$": clicked_column,
            })

            expected_vals["0"] = expected_val

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service)
            self.LOG.info(f'telemetry: {telemetry}')

            # Assert
            for row, row_values in expected_vals.items():
                row_values_as_jq_str = ' '.join(
                    [f"| select(.\"{key}\"==\"{value}\") " for key, value in row_values.items()]
                )
                self.LOG.info(f'.[{row}] {row_values_as_jq_str} ')
                assert jq.first(
                    f'.[{row}] {row_values_as_jq_str} ', telemetry)

        finally:
            self.delete_index(index_name)