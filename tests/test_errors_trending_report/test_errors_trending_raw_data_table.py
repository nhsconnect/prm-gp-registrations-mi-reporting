import json
from datetime import datetime, timedelta

import pytest
from time import sleep
import jq
from helpers.splunk \
    import get_telemetry_from_splunk, create_sample_event, set_variables_on_query, \
    create_integration_payload, create_error_payload
from tests.test_base import TestBase, EventType


class TestErrorsTrendingRawDataTable(TestBase):
    @pytest.mark.parametrize(
        "time_period, column_date_format, expected_number_of_events",
        [
            ("month", "%Y-%m", 4),
            ("week", "%Y-Wk%W", 3),
            ("day", "%Y-%m-%d", 2),
        ]
    )
    def test_errors_trending_raw_data_table_returns_results_for_the_specific_timeframe(self, time_period,
                                                                                       column_date_format,
                                                                                       expected_number_of_events):
        # Arrange
        index_name, index = self.create_index()

        # reporting window
        report_start = datetime(year=2023, month=7, day=1)
        report_end = datetime(year=2023, month=8, day=31)
        cutoff = "0"

        error_code = "99"
        failure_point = "Other"

        event_datetime = datetime(year=2023, month=7, day=15)
        selected_column = event_datetime.strftime(column_date_format)

        self.LOG.info(f"column: {selected_column}")

        if time_period == "day":
            other_event_datetime = event_datetime + timedelta(days=1, hours=8)
        elif time_period == "week":
            other_event_datetime = event_datetime + timedelta(weeks=1)
        elif time_period == "month":
            other_event_datetime = event_datetime.replace(month=8)

        self.LOG.info(f"current_event: {event_datetime.strftime('%Y-%m-%dT%H:%M:%S%z')}")
        self.LOG.info(f"other_event: {other_event_datetime.strftime('%Y-%m-%dT%H:%M:%S%z')}")

        try:
            for idx in range(expected_number_of_events):
                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id=f'test_selected_error_and_failure_reason_conv_{idx}',
                            registration_event_datetime=event_datetime.strftime("%Y-%m-%dT%H:%M:%S%z"),
                            event_type=EventType.EHR_INTEGRATIONS.value,
                            payload=create_integration_payload(outcome="FAILED_TO_INTEGRATE")
                        )),
                    sourcetype="myevent")

                # create error
                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id=f'test_selected_error_and_failure_reason_conv_{idx}',
                            registration_event_datetime=event_datetime.strftime("%Y-%m-%dT%H:%M:%S%z"),
                            event_type=EventType.ERRORS.value,
                            payload=create_error_payload(
                                errorCode=error_code,
                                errorDescription="random error",
                                failurePoint=failure_point
                            )

                        )),
                    sourcetype="myevent")

                # Other events for same error and failure point
                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id=f'conv_should_not_appear_id_{idx}',
                            registration_event_datetime=other_event_datetime.strftime("%Y-%m-%dT%H:%M:%S%z"),
                            event_type=EventType.EHR_INTEGRATIONS.value,
                            payload=create_integration_payload(outcome="FAILED_TO_INTEGRATE")
                        )),
                    sourcetype="myevent")

                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id=f'conv_should_not_appear_id_{idx}',
                            registration_event_datetime=other_event_datetime.strftime("%Y-%m-%dT%H:%M:%S%z"),
                            event_type=EventType.ERRORS.value,
                            payload=create_error_payload(
                                errorCode=error_code,
                                errorDescription="random error",
                                failurePoint=failure_point
                            )

                        )),
                    sourcetype="myevent")

            # Act
            test_query = self.generate_splunk_query_from_report(
                "gp2gp_errors_trending_report/gp2gp_errors_trending_raw_data_table"
            )

            test_query = set_variables_on_query(
                test_query,
                {
                    "$index$": index_name,
                    "$start_time$": report_start.strftime("%Y-%m-%dT%H:%m:%s"),
                    "$end_time$": report_end.strftime("%Y-%m-%dT%H:%m:%s"),
                    "$cutoff$": cutoff,
                    "$time_period$": time_period,
                    "$column$": selected_column,
                    "$errorGraphColumn$": error_code,
                    "$failurePointGraphColumn$": failure_point
                },
            )

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service
            )
            self.LOG.info(f"telemetry: {telemetry}")

            # Assert
            assert len(telemetry) == expected_number_of_events

            for idx in range(expected_number_of_events):
                assert jq.all(
                    f".[] "
                    + f'| select( .conversation_id == "test_selected_error_and_failure_reason_conv_{idx}") '
                    + f'| select( .reporting_supplier_name == "TEST_SYSTEM_SUPPLIER") '
                    + f'| select( .requesting_supplier_name == "TEST_SUPPLIER")'
                    + f'| select( .sending_supplier_name == "TEST_SUPPLIER2")'
                    + f'| select( .reporting_practice_ods_code == "A00029") '
                    + f'| select( .requesting_practice_ods_code == "A00029") '
                    + f'| select( .sending_practice_ods_code == "B00157") '
                    + f'| select( .error_code == "{error_code}")'
                    + f'| select( .failure_point == "{failure_point}")'
                    + f'| select( .other_failure_point == "N/A")'
                    + f'| select( .error_desc == "random error")'
                    , telemetry
                )

        finally:
            self.delete_index(index_name)

    @pytest.mark.parametrize(
        "time_period, column_date_format, selected_error, selected_failure_point, expected_num_of_conversations",
        [
            ("month", "%Y-%m", "06", "EHR Ready to Integrate", 1),
            ("week", "%Y-Wk%W", "11", "Other", 1),
            ("day", "%Y-%m-%d", "99", "EHR Response", 1),
            ("month", "%Y-%m", "06", "none", 2),
            ("week", "%Y-Wk%W", "11", "none", 1),
            ("day", "%Y-%m-%d", "99", "none", 1),
            ("month", "%Y-%m", "none", "EHR Ready to Integrate", 0),
            ("week", "%Y-Wk%W", "none", "Other", 0),
            ("day", "%Y-%m-%d", "none", "EHR Response", 0),
        ]
    )
    def test_errors_trending_raw_data_table_returns_results_based_on_provided_tokens(
            self, time_period, column_date_format, selected_error, selected_failure_point,
            expected_num_of_conversations):

        # Arrange
        index_name, index = self.create_index()

        # reporting window
        report_start = datetime(year=2023, month=7, day=1)
        report_end = datetime(year=2023, month=8, day=31)
        cutoff = "0"

        event_datetime = datetime(year=2023, month=7, day=15)
        selected_column = event_datetime.strftime(column_date_format)
        self.LOG.info(
            f"selected error {selected_error} with failure point {selected_failure_point} at {selected_column}")

        if time_period == "day":
            other_event_datetime = event_datetime + timedelta(days=1, hours=8)
        elif time_period == "week":
            other_event_datetime = event_datetime + timedelta(weeks=1)
        elif time_period == "month":
            other_event_datetime = event_datetime.replace(month=8)

        self.LOG.info(f"current_event: {event_datetime.strftime('%Y-%m-%dT%H:%M:%S%z')}")
        self.LOG.info(f"other_event: {other_event_datetime.strftime('%Y-%m-%dT%H:%M:%S%z')}")

        try:
            errors_dict = {
                "06": ["EHR Ready to Integrate", "Other"],
                "11": ["Other"],
                "99": ["EHR Response"]
            }

            for error_code, failure_points in errors_dict.items():
                for failure_point in failure_points:
                    test_conversation_id = f'test_trending_data_{error_code}_{failure_point.replace(" ", "_")}_id'

                    # Expected events
                    index.submit(
                        json.dumps(
                            create_sample_event(
                                conversation_id=test_conversation_id,
                                registration_event_datetime=event_datetime.strftime("%Y-%m-%dT%H:%M:%S%z"),
                                event_type=EventType.EHR_INTEGRATIONS.value,
                                payload=create_integration_payload(outcome="FAILED_TO_INTEGRATE")
                            )),
                        sourcetype="myevent")

                    # create error
                    index.submit(
                        json.dumps(
                            create_sample_event(
                                conversation_id=test_conversation_id,
                                registration_event_datetime=event_datetime.strftime("%Y-%m-%dT%H:%M:%S%z"),
                                event_type=EventType.ERRORS.value,
                                payload=create_error_payload(
                                    errorCode=error_code,
                                    errorDescription="random error",
                                    failurePoint=failure_point
                                )

                            )),
                        sourcetype="myevent")

                    # Other events
                    other_conversation_id = f'conv_should_not_appear_{error_code}_{failure_point.replace(" ", "_")}_id'

                    index.submit(
                        json.dumps(
                            create_sample_event(
                                conversation_id=other_conversation_id,
                                registration_event_datetime=other_event_datetime.strftime("%Y-%m-%dT%H:%M:%S%z"),
                                event_type=EventType.EHR_INTEGRATIONS.value,
                                payload=create_integration_payload(outcome="FAILED_TO_INTEGRATE")
                            )),
                        sourcetype="myevent")

                    index.submit(
                        json.dumps(
                            create_sample_event(
                                conversation_id=other_conversation_id,
                                registration_event_datetime=other_event_datetime.strftime("%Y-%m-%dT%H:%M:%S%z"),
                                event_type=EventType.ERRORS.value,
                                payload=create_error_payload(
                                    errorCode=error_code,
                                    errorDescription="random error",
                                    failurePoint=failure_point
                                )

                            )),
                        sourcetype="myevent")

            # Act
            test_query = self.generate_splunk_query_from_report(
                "gp2gp_errors_trending_report/gp2gp_errors_trending_raw_data_table"
            )

            test_query = set_variables_on_query(
                test_query,
                {
                    "$index$": index_name,
                    "$start_time$": report_start.strftime("%Y-%m-%dT%H:%m:%s"),
                    "$end_time$": report_end.strftime("%Y-%m-%dT%H:%m:%s"),
                    "$cutoff$": cutoff,
                    "$time_period$": time_period,
                    "$column$": selected_column,
                    "$errorGraphColumn$": selected_error,
                    "$failurePointGraphColumn$": selected_failure_point
                },
            )

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service
            )
            self.LOG.info(f"telemetry: {telemetry}")

            # Assert
            assert len(telemetry) == expected_num_of_conversations

            if len(telemetry) != 0:
                for idx in range(expected_num_of_conversations):
                    conversation_id = f'test_trending_data_{selected_error}_{errors_dict[selected_error][idx].replace(" ", "_")}_id'
                    assert jq.first(
                        f".[{idx}] "
                        + f'| select( .conversation_id == "{conversation_id}")'
                        + f'| select( .reporting_supplier_name == "TEST_SYSTEM_SUPPLIER") '
                        + f'| select( .requesting_supplier_name == "TEST_SUPPLIER")'
                        + f'| select( .sending_supplier_name == "TEST_SUPPLIER2")'
                        + f'| select( .reporting_practice_ods_code == "A00029") '
                        + f'| select( .requesting_practice_ods_code == "A00029") '
                        + f'| select( .sending_practice_ods_code == "B00157") '
                        + f'| select( .error_code == "{selected_error}")'
                        + f'| select( .failure_point == "{errors_dict[selected_error][idx]}")'
                        + f'| select( .other_failure_point == "N/A")'
                        + f'| select( .error_desc == "random error")'
                        , telemetry
                    )

        finally:
            self.delete_index(index_name)
