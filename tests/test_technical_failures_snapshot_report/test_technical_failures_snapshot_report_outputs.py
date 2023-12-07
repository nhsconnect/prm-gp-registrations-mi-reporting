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
    import get_telemetry_from_splunk, get_or_create_index, create_sample_event, set_variables_on_query, \
    create_integration_payload, create_error_payload, create_transfer_compatibility_payload
from datetime import datetime, timedelta
from jinja2 import Environment, FileSystemLoader
from tests.test_base import TestBase, EventType


class TestTechnicalFailuresSnapshotReportOutputs(TestBase):

    def test_gp2gp_technical_failures_snapshot_report_count(self):

        # reporting window
        report_start = datetime.today().date().replace(day=1)
        report_end = datetime.today().date().replace(day=28)
        cutoff = "0"

        try:
            # Arrange
            index_name, index = self.create_index()

            NUM_OF_ERROR_TYPES = {"06": 2, "07": 3, "09": 1, "Integration failure": 4}
            conv_id_idx = 1
            # technical_failure
            for idx in range(NUM_OF_ERROR_TYPES["Integration failure"]):
                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id='test_total_records_transferred_'+str(conv_id_idx),
                            registration_event_datetime=create_date_time(date=report_start, time="09:00:00"),
                            event_type=EventType.EHR_INTEGRATIONS.value,
                            payload=create_integration_payload(outcome="FAILED_TO_INTEGRATE")
                        )),
                    sourcetype="myevent")

                conv_id_idx += 1

            # awaiting_integration
            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_total_records_transferred_'+str(conv_id_idx),
                        registration_event_datetime=create_date_time(date=report_start, time="10:00:00"),
                        event_type=EventType.READY_TO_INTEGRATE_STATUSES.value
                    )),
                sourcetype="myevent")

            conv_id_idx += 1

            # technical_failure
            for _ in range(NUM_OF_ERROR_TYPES["06"]):
                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id='test_total_records_transferred_'+str(conv_id_idx),
                            registration_event_datetime=create_date_time(date=report_start, time="11:00:00"),
                            event_type=EventType.EHR_REQUESTS.value
                        )),
                    sourcetype="myevent")

                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id='test_total_records_transferred_'+str(conv_id_idx),
                            registration_event_datetime=create_date_time(date=report_start, time="11:01:00"),
                            event_type=EventType.ERRORS.value,
                            payload=create_error_payload(
                                errorCode="06",
                                errorDescription="Not at surgery",
                                failurePoint=EventType.EHR_REQUESTS.value
                            )

                        )),
                    sourcetype="myevent")

                conv_id_idx += 1

            # in_progress
            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_total_records_transferred_'+str(conv_id_idx),
                        registration_event_datetime=create_date_time(date=report_start, time="11:10:00"),
                        event_type=EventType.EHR_REQUESTS.value
                    )),
                sourcetype="myevent")

            conv_id_idx += 1

            # technical_failure
            for _ in range(NUM_OF_ERROR_TYPES["07"]):
                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id='test_total_records_transferred_'+str(conv_id_idx),
                            registration_event_datetime=create_date_time(date=report_start, time="11:00:00"),
                            event_type=EventType.EHR_RESPONSES.value
                        )),
                    sourcetype="myevent")

                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id='test_total_records_transferred_'+str(conv_id_idx),
                            registration_event_datetime=create_date_time(date=report_start, time="11:01:00"),
                            event_type=EventType.ERRORS.value,
                            payload=create_error_payload(
                                errorCode="07",
                                errorDescription="GP2GP Messaging is not enabled on this system",
                                failurePoint=EventType.EHR_RESPONSES.value
                            )

                        )),
                    sourcetype="myevent")

                conv_id_idx += 1

            # in_progress
            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_total_records_transferred_'+str(conv_id_idx),
                        registration_event_datetime=create_date_time(date=report_start, time="11:10:00"),
                        event_type=EventType.EHR_RESPONSES.value
                    )),
                sourcetype="myevent")

            conv_id_idx += 1

            # technical_failure
            for _ in range(NUM_OF_ERROR_TYPES["09"]):
                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id='test_total_records_transferred_'+str(conv_id_idx),
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
                            conversation_id='test_total_records_transferred_'+str(conv_id_idx),
                            registration_event_datetime=create_date_time(date=report_start, time="11:01:00"),
                            event_type=EventType.ERRORS.value,
                            payload=create_error_payload(
                                errorCode="09",
                                errorDescription="EHR Extract received without corresponding request",
                                failurePoint=EventType.EHR_RESPONSES.value
                            )

                        )),
                    sourcetype="myevent")

                conv_id_idx += 1

            # in_progress
            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_total_records_transferred_'+str(conv_id_idx),
                        registration_event_datetime=create_date_time(date=report_start, time="11:10:00"),
                        event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                        payload=create_transfer_compatibility_payload(
                            internalTransfer=False,
                            transferCompatible=True
                        )
                    )),
                sourcetype="myevent")

            conv_id_idx += 1

            # Act
            test_query = self.generate_splunk_query_from_report(
                'gp2gp_technical_failures_snapshot_report'
                '/gp2gp_technical_failures_snapshot_error_graph_count')

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
            expected_values = {"0": {"technical_failure_reason": "06",
                                     "count": str(NUM_OF_ERROR_TYPES["06"])},
                               "1": {"technical_failure_reason": "07",
                                     "count": str(NUM_OF_ERROR_TYPES["07"])},
                               "2": {"technical_failure_reason": "09",
                                     "count": str(NUM_OF_ERROR_TYPES["09"])},
                               "3": {"technical_failure_reason": "Integration failure",
                                     "count": str(NUM_OF_ERROR_TYPES["Integration failure"])},
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


    def test_gp2gp_technical_failures_snapshot_report_percentage(self):

        # reporting window
        report_start = datetime.today().date().replace(day=1)
        report_end = datetime.today().date().replace(day=28)
        cutoff = "0"

        try:
            # Arrange
            index_name, index = self.create_index()

            NUM_OF_ERROR_TYPES = {"06": 2, "07": 3, "09": 1, "Integration failure": 4}
            conv_id_idx = 1
            # technical_failure
            for idx in range(NUM_OF_ERROR_TYPES["Integration failure"]):
                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id='test_total_records_transferred_'+str(conv_id_idx),
                            registration_event_datetime=create_date_time(date=report_start, time="09:00:00"),
                            event_type=EventType.EHR_INTEGRATIONS.value,
                            payload=create_integration_payload(outcome="FAILED_TO_INTEGRATE")
                        )),
                    sourcetype="myevent")

                conv_id_idx += 1

            # awaiting_integration
            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_total_records_transferred_'+str(conv_id_idx),
                        registration_event_datetime=create_date_time(date=report_start, time="10:00:00"),
                        event_type=EventType.READY_TO_INTEGRATE_STATUSES.value
                    )),
                sourcetype="myevent")

            conv_id_idx += 1

            # technical_failure
            for _ in range(NUM_OF_ERROR_TYPES["06"]):
                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id='test_total_records_transferred_'+str(conv_id_idx),
                            registration_event_datetime=create_date_time(date=report_start, time="11:00:00"),
                            event_type=EventType.EHR_REQUESTS.value
                        )),
                    sourcetype="myevent")

                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id='test_total_records_transferred_'+str(conv_id_idx),
                            registration_event_datetime=create_date_time(date=report_start, time="11:01:00"),
                            event_type=EventType.ERRORS.value,
                            payload=create_error_payload(
                                errorCode="06",
                                errorDescription="Not at surgery",
                                failurePoint=EventType.EHR_REQUESTS.value
                            )

                        )),
                    sourcetype="myevent")

                conv_id_idx += 1

            # in_progress
            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_total_records_transferred_'+str(conv_id_idx),
                        registration_event_datetime=create_date_time(date=report_start, time="11:10:00"),
                        event_type=EventType.EHR_REQUESTS.value
                    )),
                sourcetype="myevent")

            conv_id_idx += 1

            # technical_failure
            for _ in range(NUM_OF_ERROR_TYPES["07"]):
                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id='test_total_records_transferred_'+str(conv_id_idx),
                            registration_event_datetime=create_date_time(date=report_start, time="11:00:00"),
                            event_type=EventType.EHR_RESPONSES.value
                        )),
                    sourcetype="myevent")

                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id='test_total_records_transferred_'+str(conv_id_idx),
                            registration_event_datetime=create_date_time(date=report_start, time="11:01:00"),
                            event_type=EventType.ERRORS.value,
                            payload=create_error_payload(
                                errorCode="07",
                                errorDescription="GP2GP Messaging is not enabled on this system",
                                failurePoint=EventType.EHR_RESPONSES.value
                            )

                        )),
                    sourcetype="myevent")

                conv_id_idx += 1

            # in_progress
            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_total_records_transferred_'+str(conv_id_idx),
                        registration_event_datetime=create_date_time(date=report_start, time="11:10:00"),
                        event_type=EventType.EHR_RESPONSES.value
                    )),
                sourcetype="myevent")

            conv_id_idx += 1

            # technical_failure
            for _ in range(NUM_OF_ERROR_TYPES["09"]):
                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id='test_total_records_transferred_'+str(conv_id_idx),
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
                            conversation_id='test_total_records_transferred_'+str(conv_id_idx),
                            registration_event_datetime=create_date_time(date=report_start, time="11:01:00"),
                            event_type=EventType.ERRORS.value,
                            payload=create_error_payload(
                                errorCode="09",
                                errorDescription="EHR Extract received without corresponding request",
                                failurePoint=EventType.EHR_RESPONSES.value
                            )

                        )),
                    sourcetype="myevent")

                conv_id_idx += 1

            # in_progress
            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_total_records_transferred_'+str(conv_id_idx),
                        registration_event_datetime=create_date_time(date=report_start, time="11:10:00"),
                        event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                        payload=create_transfer_compatibility_payload(
                            internalTransfer=False,
                            transferCompatible=True
                        )
                    )),
                sourcetype="myevent")

            conv_id_idx += 1

            # Act
            test_query = self.generate_splunk_query_from_report(
                'gp2gp_technical_failures_snapshot_report'
                '/gp2gp_technical_failures_snapshot_error_graph_percentage')

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
            expected_values = {"0": {"technical_failure_reason": "06",
                                     "count": "20.00"},
                               "1": {"technical_failure_reason": "07",
                                     "count": "30.00"},
                               "2": {"technical_failure_reason": "09",
                                     "count": "10.00"},
                               "3": {"technical_failure_reason": "Integration failure",
                                     "count": "40.00"},
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
