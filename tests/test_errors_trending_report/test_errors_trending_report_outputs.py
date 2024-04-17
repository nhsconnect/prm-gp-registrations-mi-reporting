import json
from datetime import datetime, timedelta
from time import sleep

import jq
import pytest

from helpers.splunk import create_sample_event, create_registration_payload, create_error_payload, \
    create_transfer_compatibility_payload, set_variables_on_query, get_telemetry_from_splunk
from tests.test_base import TestBase, EventType


class TestErrorsTrendingReportOutputs(TestBase):
    @pytest.mark.parametrize(
        "report_type, time_period, expected_output", [
            ("count", "month", {"0": {"time_period": "2023-05", "06": "3", "07": "2", "31": "1"}}),
            ("count", "week", {"0": {"time_period": "2023-Wk18", "06": "1", "07": "1", "31": "1"},
                               "1": {"time_period": "2023-Wk19", "06": "1", "07": "1", "31": "0"},
                               "2": {"time_period": "2023-Wk20", "06": "1", "07": "0", "31": "0"}
                               }),
            ("count", "day", {"0": {"time_period": "2023-05-01", "06": "1", "07": "1", "31": "1"},
                              "1": {"time_period": "2023-05-08", "06": "1", "07": "1", "31": "0"},
                              "2": {"time_period": "2023-05-15", "06": "1", "07": "0", "31": "0"}
                              }),
            ("percentage", "month", {"0": {"time_period": "2023-05", "06": "50.00", "07": "33.33", "31": "16.67"}}),
            ("percentage", "week", {"0": {"time_period": "2023-Wk18", "06": "33.33", "07": "33.33", "31": "33.33"},
                                    "1": {"time_period": "2023-Wk19", "06": "50.00", "07": "50.00", "31": "0.00"},
                                    "2": {"time_period": "2023-Wk20", "06": "100.00", "07": "0.00", "31": "0.00"}
                                    }),
            ("percentage", "day", {"0": {"time_period": "2023-05-01", "06": "33.33", "07": "33.33", "31": "33.33"},
                                   "1": {"time_period": "2023-05-08", "06": "50.00", "07": "50.00", "31": "0.00"},
                                   "2": {"time_period": "2023-05-15", "06": "100.00", "07": "0.00", "31": "0.00"}
                                   }),
        ]
    )
    def test_errors_trending_report_output(self, report_type, time_period, expected_output):
        # Arrange
        index_name, index = self.create_index()

        # Reporting window
        report_start = datetime(year=2023, month=5, day=1)
        report_end = datetime(year=2023, month=5, day=31)
        cutoff = "0"

        sample_of_error_distribution = {"registrations_error": (3, "06"),
                                        "transfer_compatibility_error": (2, "07"),
                                        "integration_error": (1, "31")
                                        }

        try:
            # registrations error
            for idx in range(sample_of_error_distribution["registrations_error"][0]):
                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id=f'test_registrations_{idx}',
                            registration_event_datetime=(
                                    report_start + timedelta(weeks=idx, hours=11, minutes=0)).strftime(
                                "%Y-%m-%dT%H:%M:%S%z"),
                            event_type=EventType.REGISTRATIONS.value,
                            payload=create_registration_payload()
                        )),
                    sourcetype="myevent")

                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id=f'test_registrations_{idx}',
                            registration_event_datetime=(
                                    report_start + timedelta(weeks=idx, hours=11, minutes=1)).strftime(
                                "%Y-%m-%dT%H:%M:%S%z"),
                            event_type=EventType.ERRORS.value,
                            payload=create_error_payload(
                                errorCode=sample_of_error_distribution["registrations_error"][1],
                                errorDescription="EHR Extract received without corresponding request",
                                failurePoint=EventType.REGISTRATIONS.value
                            )

                        )),
                    sourcetype="myevent")

            # transfer compatibility error
            for idx in range(sample_of_error_distribution["transfer_compatibility_error"][0]):
                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id=f'test_transfer_compatibility_{idx}',
                            registration_event_datetime=(
                                    report_start + timedelta(weeks=idx, hours=11, minutes=0)).strftime(
                                "%Y-%m-%dT%H:%M:%S%z"),
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
                            conversation_id=f'test_transfer_compatibility_{idx}',
                            registration_event_datetime=(
                                    report_start + timedelta(weeks=idx, hours=11, minutes=1)).strftime(
                                "%Y-%m-%dT%H:%M:%S%z"),
                            event_type=EventType.ERRORS.value,
                            payload=create_error_payload(
                                errorCode=sample_of_error_distribution["transfer_compatibility_error"][1],
                                errorDescription="EHR Extract received without corresponding request",
                                failurePoint=EventType.TRANSFER_COMPATIBILITY_STATUSES.value
                            )

                        )),
                    sourcetype="myevent")

            # integration error
            for idx in range(sample_of_error_distribution["integration_error"][0]):
                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id=f'test_integration_error_{idx}',
                            registration_event_datetime=(
                                    report_start + timedelta(weeks=idx, hours=11, minutes=0)).strftime(
                                "%Y-%m-%dT%H:%M:%S%z"),
                            event_type=EventType.EHR_INTEGRATIONS.value
                        )),
                    sourcetype="myevent")

                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id=f'test_integration_error_{idx}',
                            registration_event_datetime=(
                                    report_start + timedelta(weeks=idx, hours=11, minutes=1)).strftime(
                                "%Y-%m-%dT%H:%M:%S%z"),
                            event_type=EventType.ERRORS.value,
                            payload=create_error_payload(
                                errorCode=sample_of_error_distribution["integration_error"][1],
                                errorDescription="random error",
                                failurePoint=EventType.EHR_INTEGRATIONS.value
                            )

                        )),
                    sourcetype="myevent")

            # Act
            test_query = self.generate_splunk_query_from_report(
                f'gp2gp_errors_trending_report/gp2gp_errors_trending_report_{report_type}')

            test_query = set_variables_on_query(test_query, {
                "$index$": index_name,
                "$start_time$": report_start.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "$end_time$": report_end.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "$cutoff$": cutoff,
                "$time_period$": time_period
            })

            sleep(2)

            telemetry = get_telemetry_from_splunk(self.savedsearch(test_query), self.splunk_service)
            self.LOG.info(f'telemetry: {telemetry}')

            # Assert
            for row, row_values in expected_output.items():
                row_values_as_jq_str = ' '.join(
                    [f"| select(.\"{key}\"==\"{value}\") " for key, value in row_values.items()]
                )

                self.LOG.info(f'.[{row}] {row_values_as_jq_str} ')
                assert jq.first(
                    f'.[{row}] {row_values_as_jq_str} ', telemetry
                )

        finally:
            self.delete_index(index_name)

    @pytest.mark.parametrize(
        "report_type, time_period, clicked_error, expected_output", [
            ("count", "month", "06", {"0": {"time_period": "2023-05", "EHR Ready to Integrate": "3",
                                            "EHR Requested": "2", "EHR Response": "1", "Endpoint Lookup": "3",
                                            "Other": "2", "Patient General Update": "2", "Patient Trace": "1"}}),
            ("count", "week", "06", {"0": {"time_period": "2023-Wk18", "EHR Ready to Integrate": "1",
                                           "EHR Requested": "1", "EHR Response": "1", "Endpoint Lookup": "1",
                                           "Other": "1", "Patient General Update": "1", "Patient Trace": "1"},
                                     "1": {"time_period": "2023-Wk19", "EHR Ready to Integrate": "1",
                                           "EHR Requested": "1", "EHR Response": "0", "Endpoint Lookup": "1",
                                           "Other": "1", "Patient General Update": "1", "Patient Trace": "0"},
                                     "2": {"time_period": "2023-Wk20", "EHR Ready to Integrate": "1",
                                           "EHR Requested": "0", "EHR Response": "0", "Endpoint Lookup": "1",
                                           "Other": "0", "Patient General Update": "0", "Patient Trace": "0"}}),
            ("count", "day", "06", {"0": {"time_period": "2023-05-01", "EHR Ready to Integrate": "1",
                                          "EHR Requested": "1", "EHR Response": "1", "Endpoint Lookup": "1",
                                          "Other": "1", "Patient General Update": "1", "Patient Trace": "1"},
                                    "1": {"time_period": "2023-05-08", "EHR Ready to Integrate": "1",
                                          "EHR Requested": "1", "EHR Response": "0", "Endpoint Lookup": "1",
                                          "Other": "1", "Patient General Update": "1", "Patient Trace": "0"},
                                    "2": {"time_period": "2023-05-15", "EHR Ready to Integrate": "1",
                                          "EHR Requested": "0", "EHR Response": "0", "Endpoint Lookup": "1",
                                          "Other": "0", "Patient General Update": "0", "Patient Trace": "0"}}),
            ("percentage", "month", "06", {"0": {"time_period": "2023-05", "EHR Ready to Integrate": "21.43",
                                                 "EHR Requested": "14.29", "EHR Response": "7.14",
                                                 "Endpoint Lookup": "21.43", "Other": "14.29",
                                                 "Patient General Update": "14.29", "Patient Trace": "7.14"}}),
            ("percentage", "week", "06", {"0": {"time_period": "2023-Wk18", "EHR Ready to Integrate": "14.29",
                                                "EHR Requested": "14.29", "EHR Response": "14.29",
                                                "Endpoint Lookup": "14.29", "Other": "14.29",
                                                "Patient General Update": "14.29", "Patient Trace": "14.29"},
                                          "1": {"time_period": "2023-Wk19", "EHR Ready to Integrate": "20.00",
                                                "EHR Requested": "20.00", "EHR Response": "0.00",
                                                "Endpoint Lookup": "20.00", "Other": "20.00",
                                                "Patient General Update": "20.00", "Patient Trace": "0.00"},
                                          "2": {"time_period": "2023-Wk20", "EHR Ready to Integrate": "50.00",
                                                "EHR Requested": "0.00", "EHR Response": "0.00",
                                                "Endpoint Lookup": "50.00", "Other": "0.00",
                                                "Patient General Update": "0.00", "Patient Trace": "0.00"}}),
            ("percentage", "day", "06", {"0": {"time_period": "2023-05-01", "EHR Ready to Integrate": "14.29",
                                               "EHR Requested": "14.29", "EHR Response": "14.29",
                                               "Endpoint Lookup": "14.29", "Other": "14.29",
                                               "Patient General Update": "14.29", "Patient Trace": "14.29"},
                                         "1": {"time_period": "2023-05-08", "EHR Ready to Integrate": "20.00",
                                               "EHR Requested": "20.00", "EHR Response": "0.00",
                                               "Endpoint Lookup": "20.00", "Other": "20.00",
                                               "Patient General Update": "20.00", "Patient Trace": "0.00"},
                                         "2": {"time_period": "2023-05-15", "EHR Ready to Integrate": "50.00",
                                               "EHR Requested": "0.00", "EHR Response": "0.00",
                                               "Endpoint Lookup": "50.00", "Other": "0.00",
                                               "Patient General Update": "0.00", "Patient Trace": "0.00"}}),
        ]
    )
    def test_errors_trending_failure_point_graph_output(self, report_type, time_period, clicked_error, expected_output):
        # Arrange
        index_name, index = self.create_index()

        # Reporting window
        report_start = datetime(year=2023, month=5, day=1)
        report_end = datetime(year=2023, month=5, day=31)
        cutoff = "0"

        failure_points_and_counts = [
            ("EHR Ready to Integrate", 3),
            ("EHR Requested", 2),
            ("EHR Response", 1),
            ("Endpoint Lookup", 3),
            ("Other", 2),
            ("Patient General Update", 2),
            ("Patient Trace", 1)
        ]

        try:
            for i, (failure_point, count) in enumerate(failure_points_and_counts):
                # technical_failure
                for idx in range(count):
                    failure_point_conversation_id = f'test_failure_point_trending_{clicked_error}_{idx}'

                    index.submit(
                        json.dumps(
                            create_sample_event(
                                conversation_id=failure_point_conversation_id,
                                registration_event_datetime=(
                                        report_start + timedelta(weeks=idx, hours=11, minutes=0)).strftime(
                                    "%Y-%m-%dT%H:%M:%S%z"),
                                event_type=EventType.EHR_REQUESTS.value
                            )),
                        sourcetype="myevent")

                    index.submit(
                        json.dumps(
                            create_sample_event(
                                conversation_id=failure_point_conversation_id,
                                registration_event_datetime=(
                                        report_start + timedelta(weeks=idx, hours=11, minutes=1)).strftime(
                                    "%Y-%m-%dT%H:%M:%S%z"),
                                event_type=EventType.ERRORS.value,
                                payload=create_error_payload(
                                    errorCode=clicked_error,
                                    errorDescription="Random desc",
                                    failurePoint=failure_point
                                )
                            )),
                        sourcetype="myevent")

                    # Non selected column
                    index.submit(
                        json.dumps(
                            create_sample_event(
                                conversation_id=f'test_failure_point_trending_different_error_code_{idx}',
                                registration_event_datetime=(
                                        report_start + timedelta(weeks=idx, hours=11, minutes=0)).strftime(
                                    "%Y-%m-%dT%H:%M:%S%z"),
                                event_type=EventType.EHR_REQUESTS.value
                            )),
                        sourcetype="myevent")

                    index.submit(
                        json.dumps(
                            create_sample_event(
                                conversation_id=f'test_failure_point_trending_different_error_code_{idx}',
                                registration_event_datetime=(
                                        report_start + timedelta(weeks=idx, hours=11, minutes=1)).strftime(
                                    "%Y-%m-%dT%H:%M:%S%z"),
                                event_type=EventType.ERRORS.value,
                                payload=create_error_payload(
                                    errorCode="different-error-code",
                                    errorDescription="Random desc",
                                    failurePoint=failure_point
                                )
                            )),
                        sourcetype="myevent")

            # Act
            test_query = self.generate_splunk_query_from_report(
                f'gp2gp_errors_trending_report/gp2gp_errors_trending_failure_point_graph_{report_type}')

            test_query = set_variables_on_query(test_query, {
                "$index$": index_name,
                "$start_time$": report_start.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "$end_time$": report_end.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "$cutoff$": cutoff,
                "$time_period$": time_period,
                "$errorGraphColumn$": clicked_error,
            })

            sleep(2)

            telemetry = get_telemetry_from_splunk(self.savedsearch(test_query), self.splunk_service)
            self.LOG.info(f'telemetry: {telemetry}')

            # Assert
            for row, row_values in expected_output.items():
                row_values_as_jq_str = ' '.join(
                    [f"| select(.\"{key}\"==\"{value}\") " for key, value in row_values.items()]
                )

                self.LOG.info(f'.[{row}] {row_values_as_jq_str} ')
                assert jq.first(
                    f'.[{row}] {row_values_as_jq_str} ', telemetry
                )

        finally:
            self.delete_index(index_name)
