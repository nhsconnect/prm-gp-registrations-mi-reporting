import datetime
import json
import pytest
from time import sleep
import jq
from helpers.splunk \
    import get_telemetry_from_splunk, create_sample_event, set_variables_on_query, \
    create_integration_payload, create_error_payload, create_transfer_compatibility_payload, create_ehr_response_payload
from tests.test_base import TestBase, EventType
from helpers.datetime_helper import create_date_time, generate_report_start_date, \
    generate_report_end_date


class TestTechnicalFailuresTrendingRawDataTableOutputs(TestBase):

    @pytest.mark.parametrize("error_code_line, failure_point_line, error_codes, failure_points",
                             [("None", "None", [], []),
                              ("Integration failure", "None", ["20"], ["EHR_INTEGRATION"]),
                              ("06", "None", ["06", "06"], ["EHR_RESPONSE", "OTHER"]),
                              ("06", "OTHER", ["06"], ["OTHER"])
                              ])
    def test_gp2gp_technical_failures_trending_raw_data_table_error_code_line_and_failure_point_line_tokens(
            self,
            error_code_line,
            failure_point_line,
            error_codes,
            failure_points
    ):

        # reporting window
        report_start = generate_report_start_date()
        report_end = generate_report_end_date()
        cutoff = "0"

        try:
            # Arrange
            index_name, index = self.create_index()

            # create event
            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id="test_error_code_06_failure_point_OTHER",
                        registration_event_datetime=create_date_time(date=report_start, time="09:00:00"),
                        event_type=EventType.EHR_INTEGRATIONS.value,
                        payload=create_integration_payload(outcome="FAILED_TO_INTEGRATE")
                    )),
                sourcetype="myevent")

            # create error
            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id="test_error_code_06_failure_point_OTHER",
                        registration_event_datetime=create_date_time(date=report_start, time="09:00:00"),
                        event_type=EventType.ERRORS.value,
                        payload=create_error_payload(
                            errorCode="06",
                            errorDescription="random error",
                            failurePoint="OTHER"
                        )

                    )),
                sourcetype="myevent")

            # create event
            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id="test_error_code_06_failure_point_EHR_RESPONSE",
                        registration_event_datetime=create_date_time(date=report_start, time="09:01:00"),
                        event_type=EventType.EHR_RESPONSES.value,
                        payload=create_ehr_response_payload()
                    )),
                sourcetype="myevent")

            # create error
            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id="test_error_code_06_failure_point_EHR_RESPONSE",
                        registration_event_datetime=create_date_time(date=report_start, time="09:01:00"),
                        event_type=EventType.ERRORS.value,
                        payload=create_error_payload(
                            errorCode="06",
                            errorDescription="random error",
                            failurePoint="EHR_RESPONSE"
                        )

                    )),
                sourcetype="myevent")

            # create event
            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id="test_error_code_20_failure_point_EHR_RESPONSE",
                        registration_event_datetime=create_date_time(date=report_start, time="09:02:00"),
                        event_type=EventType.EHR_RESPONSES.value,
                        payload=create_ehr_response_payload()
                    )),
                sourcetype="myevent")

            # create error
            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id="test_error_code_20_failure_point_EHR_RESPONSE",
                        registration_event_datetime=create_date_time(date=report_start, time="09:02:00"),
                        event_type=EventType.ERRORS.value,
                        payload=create_error_payload(
                            errorCode="20",
                            errorDescription="random error",
                            failurePoint="EHR_RESPONSE"
                        )

                    )),
                sourcetype="myevent")

            # create event
            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id="test_error_code_20_failure_point_EHR_INTEGRATION",
                        registration_event_datetime=create_date_time(date=report_start, time="09:00:00"),
                        event_type=EventType.EHR_INTEGRATIONS.value,
                        payload=create_integration_payload(outcome="FAILED_TO_INTEGRATE")
                    )),
                sourcetype="myevent")

            # create error
            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id="test_error_code_20_failure_point_EHR_INTEGRATION",
                        registration_event_datetime=create_date_time(date=report_start, time="09:00:00"),
                        event_type=EventType.ERRORS.value,
                        payload=create_error_payload(
                            errorCode="20",
                            errorDescription="random error",
                            failurePoint="EHR_INTEGRATION"
                        )

                    )),
                sourcetype="myevent")

            # Act
            test_query = self.generate_splunk_query_from_report(
                "gp2gp_technical_failures_trending_report"
                "/gp2gp_technical_failures_trending_raw_data_table")

            test_query = set_variables_on_query(test_query, {
                "$index$": index_name,
                "$start_time$": report_start.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "$end_time$": report_end.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "$cutoff$": cutoff,
                "$time_period$": "month",
                "$column$": report_start.strftime("%Y-%m"),
                "$error_code_line$": error_code_line,
                "$failure_point_line$": failure_point_line,
            })

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service)
            self.LOG.info(f'telemetry: {telemetry}')

            # Assert

            if error_code_line == "None" and failure_point_line == "None":
                assert len(telemetry) == 0
            elif error_code_line == "06" and failure_point_line == "None":
                assert len(telemetry) == 2
            else:
                assert len(telemetry) == 1

            for idx in range(len(error_codes)):
                assert jq.first(
                    f".[{idx}] "
                    + f'| select( .reporting_supplier_name == "TEST_SYSTEM_SUPPLIER")'
                    + f'| select( .requesting_supplier_name == "TEST_SUPPLIER")'
                    + f'| select( .sending_supplier_name == "TEST_SUPPLIER2")'
                    + f'| select( .reporting_practice_ods_code == "A00029")'
                    + f'| select( .requesting_practice_ods_code == "A00029")'
                    + f'| select( .sending_practice_ods_code == "B00157")'
                    + f'| select( .error_code == "{error_codes[idx]}")'
                    + f'| select( .failure_point == "{failure_points[idx]}")'
                    + f'| select( .other_failure_point == "N/A")'
                    + f'| select( .error_desc == "random error")'
                    + f'| select( .broken_24h_sla == "0" or .broken_24h_sla == "1")'
                    + f'| select( .broken_ehr_sending_sla == "0" or .broken_ehr_sending_sla == "1")'
                    + f'| select( .broken_ehr_requesting_sla == "0" or .broken_ehr_requesting_sla == "1")'
                    , telemetry
                )

        finally:
            self.delete_index(index_name)

    @pytest.mark.parametrize(
        "time_period, expected_column_format, expected_number_of_events",
        [
            ("month", "%Y-%m", 4),
            ("week", "%Y-Wk%W", 3),
            ("day", "%Y-%m-%d", 2),
        ]
    )
    def test_gp2gp_technical_failures_trending_raw_data_table_column_token(self, time_period,
                                                                           expected_column_format,
                                                                           expected_number_of_events):

        # Arrange
        index_name, index = self.create_index()

        # reporting window
        report_start = datetime.datetime(year=2023, month=10, day=1)
        report_end = datetime.datetime(year=2023, month=10, day=31)
        cutoff = "0"

        error_code_line = "06"
        failure_point_line = "OTHER"

        event_datetime = report_start
        selected_column = event_datetime.strftime(expected_column_format)

        if time_period == "day":
            other_event_datetime = event_datetime + datetime.timedelta(days=1, hours=8)
        elif time_period == "week":
            other_event_datetime = event_datetime + datetime.timedelta(weeks=1)
        elif time_period == "month":
            other_event_datetime = event_datetime.replace(month=11)
        else:
            raise ValueError("time_period must be on of the following options: 'day', 'week', 'month'.")

        trending_total_number_of_technical_failures = 5
        total_outside_selection = trending_total_number_of_technical_failures - expected_number_of_events

        try:
            # Arrange
            index_name, index = self.create_index()

            for idx in range(expected_number_of_events):
                # create event
                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id=f"test_expected_technical_failures_{idx}",
                            registration_event_datetime=event_datetime.strftime("%Y-%m-%dT%H:%M:%S%z"),
                            event_type=EventType.EHR_INTEGRATIONS.value,
                            payload=create_integration_payload(outcome="FAILED_TO_INTEGRATE")
                        )),
                    sourcetype="myevent")

                # create error
                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id=f"test_expected_technical_failures_{idx}",
                            registration_event_datetime=event_datetime.strftime("%Y-%m-%dT%H:%M:%S%z"),
                            event_type=EventType.ERRORS.value,
                            payload=create_error_payload(
                                errorCode="06",
                                errorDescription="random error",
                                failurePoint="OTHER"
                            )

                        )),
                    sourcetype="myevent")

            for idx in range(total_outside_selection):
                # create event
                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id=f"test_other_technical_failures_{idx}",
                            registration_event_datetime=other_event_datetime.strftime("%Y-%m-%dT%H:%M:%S%z"),
                            event_type=EventType.EHR_INTEGRATIONS.value,
                            payload=create_integration_payload(outcome="FAILED_TO_INTEGRATE")
                        )),
                    sourcetype="myevent")

                # create error
                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id=f"test_other_technical_failures_{idx}",
                            registration_event_datetime=other_event_datetime.strftime("%Y-%m-%dT%H:%M:%S%z"),
                            event_type=EventType.ERRORS.value,
                            payload=create_error_payload(
                                errorCode="06",
                                errorDescription="random error",
                                failurePoint="OTHER"
                            )

                        )),
                    sourcetype="myevent")

            # Act
            test_query = self.generate_splunk_query_from_report(
                "gp2gp_technical_failures_trending_report"
                "/gp2gp_technical_failures_trending_raw_data_table")

            test_query = set_variables_on_query(test_query, {
                "$index$": index_name,
                "$start_time$": report_start.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "$end_time$": report_end.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "$cutoff$": cutoff,
                "$time_period$": time_period,
                "$column$": selected_column,
                "$error_code_line$": error_code_line,
                "$failure_point_line$": failure_point_line,
            })

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service)
            self.LOG.info(f'telemetry: {telemetry}')

            # Assert

            assert len(telemetry) == expected_number_of_events

            for idx in range(expected_number_of_events):
                assert jq.all(
                    f".[] "
                    + f'| select( .conversation_id == "test_expected_technical_failures_{idx}")'
                    + f'| select( .reporting_supplier_name == "TEST_SYSTEM_SUPPLIER")'
                    + f'| select( .requesting_supplier_name == "TEST_SUPPLIER")'
                    + f'| select( .sending_supplier_name == "TEST_SUPPLIER2")'
                    + f'| select( .reporting_practice_ods_code == "A00029")'
                    + f'| select( .requesting_practice_ods_code == "A00029")'
                    + f'| select( .sending_practice_ods_code == "B00157")'
                    + f'| select( .error_code == "06")'
                    + f'| select( .failure_point == "OTHER")'
                    + f'| select( .other_failure_point == "N/A")'
                    + f'| select( .error_desc == "random error")'
                    + f'| select( .broken_24h_sla == "0" or .broken_24h_sla == "1")'
                    + f'| select( .broken_ehr_sending_sla == "0" or .broken_ehr_sending_sla == "1")'
                    + f'| select( .broken_ehr_requesting_sla == "0" or .broken_ehr_requesting_sla == "1")'
                    , telemetry
                )

        finally:
            self.delete_index(index_name)
