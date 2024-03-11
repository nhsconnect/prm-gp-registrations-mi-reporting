import json
import uuid
from datetime import timedelta
from time import sleep
from splunklib import client
import jq
import pytest

from helpers.datetime_helper import (
    create_date_time,
    generate_report_start_date,
    generate_report_end_date,
)
from helpers.splunk import (
    get_telemetry_from_splunk,
    create_sample_event,
    set_variables_on_query,
    create_ehr_response_payload,
)
from tests.test_base import TestBase, EventType


class TestPlaceholderTrendingRawDataTable(TestBase):
    @pytest.mark.parametrize(
        "time_period, expected_column_format, expected_number_of_placeholders",
        [
            ("month", "%Y-%m", 4),
            ("week", "%Y-Wk%W", 3),
            ("day", "%Y-%m-%d", 2),
        ]
    )
    def test_gp2gp_placeholder_trending_report_raw_data_table_column_token(self, time_period, expected_column_format,
                                                                           expected_number_of_placeholders):

        """
        Tests aggregation when placeholders are the same.
        """

        # Arrange
        index_name, index = self.create_index()

        # reporting window
        report_start = generate_report_start_date()
        report_end = generate_report_end_date()
        cutoff = "0"

        line = "1-5 placeholders"

        event_datetime = report_start
        selected_column = event_datetime.strftime(expected_column_format)

        self.LOG.info(f"column: {selected_column}")

        if time_period == "day":
            other_event_datetime = event_datetime + timedelta(days=1, hours=8)
        elif time_period == "week":
            other_event_datetime = event_datetime + timedelta(weeks=1)
        elif time_period == "month":
            other_event_datetime = event_datetime.replace(month=11)

        self.LOG.info(f"current_event: {event_datetime.strftime('%Y-%m-%dT%H:%M:%S%z')}")
        self.LOG.info(f"other_event: {other_event_datetime.strftime('%Y-%m-%dT%H:%M:%S%z')}")

        placeholder = {
            "generatedBy": "SENDER",
            "clinicalType": "SCANNED_DOCUMENT",
            "reason": "FILE_NOT_FOUND",
            "originalMimeType": "application/pdf",
        }
        placeholders = [placeholder] * expected_number_of_placeholders
        payload = {
            "ehr": {
                "ehrStructuredSizeBytes": 4096,
                "placeholders": placeholders,
            }
        }

        try:

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id="test_no_placeholders_conv_1",
                        registration_event_datetime=create_date_time(date=event_datetime, time="05:00:00"),
                        event_type=EventType.EHR_RESPONSES.value,
                        payload=create_ehr_response_payload(number_of_placeholders=0)
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id="test_no_placeholders_conv_1",
                        registration_event_datetime=create_date_time(date=event_datetime, time="05:00:00"),
                        event_type=EventType.READY_TO_INTEGRATE_STATUSES.value,
                    )),
                sourcetype="myevent")

            placeholder_conversation_id = f"test_with_placeholders_{uuid.uuid4()}"

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=placeholder_conversation_id,
                        registration_event_datetime=create_date_time(date=event_datetime, time="05:00:00"),
                        event_type=EventType.EHR_RESPONSES.value,
                        payload=payload,
                    )
                ),
                sourcetype="myevent",
            )

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=placeholder_conversation_id,
                        registration_event_datetime=create_date_time(date=event_datetime, time="05:00:00"),
                        event_type=EventType.READY_TO_INTEGRATE_STATUSES.value,
                    )
                ),
                sourcetype="myevent",
            )

            other_event_conversation_id = f"test_other_events_with_placeholders_{uuid.uuid4()}"

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=other_event_conversation_id,
                        registration_event_datetime=create_date_time(date=other_event_datetime, time="05:00:00"),
                        event_type=EventType.EHR_RESPONSES.value,
                        payload=payload,
                    )
                ),
                sourcetype="myevent",
            )

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=other_event_conversation_id,
                        registration_event_datetime=create_date_time(date=other_event_datetime, time="05:00:00"),
                        event_type=EventType.READY_TO_INTEGRATE_STATUSES.value,
                    )
                ),
                sourcetype="myevent",
            )

            # Act
            test_query = self.generate_splunk_query_from_report(
                "gp2gp_placeholder_trending_report/"
                "gp2gp_placeholder_trending_report_raw_data_table"
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
                    "$line$": line
                },
            )

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service
            )
            self.LOG.info(f"telemetry: {telemetry}")

            # Assert
            assert len(telemetry) == 1

            assert jq.all(
                f".[0] "
                + f'| select( .conversation_id == "{placeholder_conversation_id}") '
                + f'| select( .total_number_of_placeholders == "{expected_number_of_placeholders}") '
                + f'| select( .clinical_type == "{placeholder["clinicalType"]}")'
                + f'| select( .reason == "{placeholder["reason"]}")'
                + f'| select( .count_of_placeholders_with_same_content == "{expected_number_of_placeholders}")'
                + f'| select( .generated_by == "{placeholder["generatedBy"]}")'
                + f'| select( .original_mime_type == "{placeholder["originalMimeType"]}")'
                + f'| select( .reporting_supplier_name == "TEST_SYSTEM_SUPPLIER")'
                + f'| select( .requesting_supplier_name == "TEST_SUPPLIER")'
                + f'| select( .sending_supplier_name == "TEST_SUPPLIER2")'
                + f'| select( .reporting_practice_ods_code == "A00029")'
                + f'| select( .requesting_practice_ods_code == "A00029")'
                + f'| select( .sending_practice_ods_code == "B00157")',
                telemetry,
            )

        finally:
            self.delete_index(index_name)

    @pytest.mark.parametrize(
        "time_period, expected_date_format, line, expected_total_number_of_placeholders",
        [
            ("month", "%Y-%m", "1-5 placeholders", 4),
            ("month", "%Y-%m", "6-10 placeholders", 8),
            ("week", "%Y-Wk%W", "11-15 placeholders", 14),
            ("week", "%Y-Wk%W", "16-20 placeholders", 18),
            ("day", "%Y-%m-%d", "21+ placeholders", 24),
        ]
    )
    def test_gp2gp_placeholder_trending_report_raw_data_table_line_token(self, time_period, expected_date_format,
                                                                         line, expected_total_number_of_placeholders):

        """
        Tests aggregation when placeholders are the different.
        """

        # Arrange
        index_name, index = self.create_index()

        # reporting window
        report_start = generate_report_start_date()
        report_end = generate_report_end_date()
        cutoff = "0"

        event_datetime = report_start
        selected_column = event_datetime.strftime(expected_date_format)

        self.LOG.info(f"column: {selected_column}")

        number_of_placeholders_with_same_content = expected_total_number_of_placeholders // 2

        placeholder_1 = {
            "generatedBy": "SENDER",
            "clinicalType": "SCANNED_DOCUMENT",
            "reason": "FILE_NOT_FOUND",
            "originalMimeType": "application/pdf",
        }

        placeholder_2 = {
            "generatedBy": "PRE_EXISTING",
            "clinicalType": "ORIGINAL_TEXT_DOCUMENT",
            "reason": "FILE_NOT_FOUND",
            "originalMimeType": "application/pdf",
        }

        placeholders = [placeholder_1] * number_of_placeholders_with_same_content
        placeholders += [placeholder_2] * number_of_placeholders_with_same_content

        payload = {
            "ehr": {
                "ehrStructuredSizeBytes": 4096,
                "placeholders": placeholders,
            }
        }

        try:

            random_conversation_id = f"test_placeholder_graph_{uuid.uuid4()}"

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=random_conversation_id,
                        registration_event_datetime=create_date_time(
                            date=event_datetime, time="05:00:00"
                        ),
                        event_type=EventType.EHR_RESPONSES.value,
                        payload=payload,
                    )
                ),
                sourcetype="myevent",
            )

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=random_conversation_id,
                        registration_event_datetime=create_date_time(
                            date=event_datetime, time="05:00:00"
                        ),
                        event_type=EventType.READY_TO_INTEGRATE_STATUSES.value,
                    )
                ),
                sourcetype="myevent",
            )

            # Act
            test_query = self.generate_splunk_query_from_report(
                "gp2gp_placeholder_trending_report/"
                "gp2gp_placeholder_trending_report_raw_data_table"
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
                    "$line$": line
                },
            )

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service
            )
            self.LOG.info(f"telemetry: {telemetry}")

            # Assert

            assert jq.all(
                f".[0] "
                + f'| select( .conversation_id == "{random_conversation_id}") '
                + f'| select( .total_number_of_placeholders == "{expected_total_number_of_placeholders}") '
                + f'| select( .clinical_type == "{placeholder_2["clinicalType"]}")'
                + f'| select( .reason == "{placeholder_2["reason"]}")'
                + f'| select( .count_of_placeholders_with_same_content == "{number_of_placeholders_with_same_content}")'
                + f'| select( .generated_by == "{placeholder_2["generatedBy"]}")'
                + f'| select( .original_mime_type == "{placeholder_2["originalMimeType"]}")'
                + f'| select( .reporting_supplier_name == "TEST_SYSTEM_SUPPLIER")'
                + f'| select( .requesting_supplier_name == "TEST_SUPPLIER")'
                + f'| select( .sending_supplier_name == "TEST_SUPPLIER2")'
                + f'| select( .reporting_practice_ods_code == "A00029")'
                + f'| select( .requesting_practice_ods_code == "A00029")'
                + f'| select( .sending_practice_ods_code == "B00157")',
                telemetry,
            )

            assert jq.all(
                f".[1] "
                + f'| select( .conversation_id == "{random_conversation_id}") '
                + f'| select( .total_number_of_placeholders == "{expected_total_number_of_placeholders}") '
                + f'| select( .clinical_type == "{placeholder_1["clinicalType"]}")'
                + f'| select( .reason == "{placeholder_1["reason"]}")'
                + f'| select( .count_of_placeholders_with_same_content == "{number_of_placeholders_with_same_content}")'
                + f'| select( .generated_by == "{placeholder_1["generatedBy"]}")'
                + f'| select( .original_mime_type == "{placeholder_1["originalMimeType"]}")'
                + f'| select( .reporting_supplier_name == "TEST_SYSTEM_SUPPLIER")'
                + f'| select( .requesting_supplier_name == "TEST_SUPPLIER")'
                + f'| select( .sending_supplier_name == "TEST_SUPPLIER2")'
                + f'| select( .reporting_practice_ods_code == "A00029")'
                + f'| select( .requesting_practice_ods_code == "A00029")'
                + f'| select( .sending_practice_ods_code == "B00157")',
                telemetry,
            )

        finally:
            self.delete_index(index_name)

    @pytest.mark.parametrize(
        "line, expected_number_of_conversations",
        [
            ("1-5 placeholders", 2),
            ("6-10 placeholders", 0),
            ("11-15 placeholders", 0),
            ("16-20 placeholders", 0),
            ("21+ placeholders", 0),
        ]
    )
    def test_gp2gp_placeholder_trending_report_raw_data_table_different_conversation(self, line,
                                                                                     expected_number_of_conversations):
        """
        Tests aggregation when conversation ids are different.
        """
        # Arrange
        index_name, index = self.create_index()

        # reporting window
        report_start = generate_report_start_date()
        report_end = generate_report_end_date()
        cutoff = "0"

        event_datetime = report_start

        try:

            placeholder_1 = {
                "generatedBy": "SENDER",
                "clinicalType": "SCANNED_DOCUMENT",
                "reason": "FILE_NOT_FOUND",
                "originalMimeType": "application/pdf",
            }

            placeholder_2 = {
                "generatedBy": "PRE_EXISTING",
                "clinicalType": "ORIGINAL_TEXT_DOCUMENT",
                "reason": "FILE_NOT_FOUND",
                "originalMimeType": "application/pdf",
            }

            placeholders_1 = [placeholder_1] * 3
            placeholders_2 = [placeholder_2] * 3

            payload_1 = {
                "ehr": {
                    "ehrStructuredSizeBytes": 4096,
                    "placeholders": placeholders_1,
                }
            }

            payload_2 = {
                "ehr": {
                    "ehrStructuredSizeBytes": 4096,
                    "placeholders": placeholders_2,
                }
            }

            conversation_id_1 = "conversation_id_1"
            conversation_id_2 = "conversation_id_2"

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversation_id_1,
                        registration_event_datetime=create_date_time(
                            date=event_datetime, time="05:00:00"
                        ),
                        event_type=EventType.EHR_RESPONSES.value,
                        payload=payload_1,
                    )
                ),
                sourcetype="myevent",
            )

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversation_id_1,
                        registration_event_datetime=create_date_time(
                            date=event_datetime, time="05:00:00"
                        ),
                        event_type=EventType.READY_TO_INTEGRATE_STATUSES.value,
                    )
                ),
                sourcetype="myevent",
            )

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversation_id_2,
                        registration_event_datetime=create_date_time(
                            date=event_datetime, time="05:01:00"
                        ),
                        event_type=EventType.EHR_RESPONSES.value,
                        payload=payload_2,
                    )
                ),
                sourcetype="myevent",
            )

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversation_id_2,
                        registration_event_datetime=create_date_time(
                            date=event_datetime, time="05:01:00"
                        ),
                        event_type=EventType.READY_TO_INTEGRATE_STATUSES.value,
                    )
                ),
                sourcetype="myevent",
            )

            # Act
            test_query = self.generate_splunk_query_from_report(
                "gp2gp_placeholder_trending_report/"
                "gp2gp_placeholder_trending_report_raw_data_table"
            )

            test_query = set_variables_on_query(
                test_query,
                {
                    "$index$": index_name,
                    "$start_time$": report_start.strftime("%Y-%m-%dT%H:%m:%s"),
                    "$end_time$": report_end.strftime("%Y-%m-%dT%H:%m:%s"),
                    "$cutoff$": cutoff,
                    "$time_period$": "month",
                    "$column$": event_datetime.strftime("%Y-%m"),
                    "$line$": line
                },
            )

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service
            )
            self.LOG.info(f"telemetry: {telemetry}")

            # Assert
            assert len(telemetry) == expected_number_of_conversations

            if len(telemetry) > 0:
                assert jq.all(
                    f".[0] "
                    + f'| select( .conversation_id == "{conversation_id_2}") '
                    + f'| select( .total_number_of_placeholders == "3") '
                    + f'| select( .clinical_type == "{placeholder_2["clinicalType"]}")'
                    + f'| select( .reason == "{placeholder_2["reason"]}")'
                    + f'| select( .count_of_placeholders_with_same_content == "3")'
                    + f'| select( .generated_by == "{placeholder_2["generatedBy"]}")'
                    + f'| select( .original_mime_type == "{placeholder_2["originalMimeType"]}")'
                    + f'| select( .requesting_supplier_name == "TEST_SUPPLIER")'
                    + f'| select( .sending_supplier_name == "TEST_SUPPLIER2")'
                    + f'| select( .requesting_practice_ods_code == "A00029")'
                    + f'| select( .sending_practice_ods_code == "B00157")',
                    telemetry,
                )

                assert jq.all(
                    f".[1] "
                    + f'| select( .conversation_id == "{conversation_id_1}") '
                    + f'| select( .total_number_of_placeholders == "3") '
                    + f'| select( .clinical_type == "{placeholder_1["clinicalType"]}")'
                    + f'| select( .reason == "{placeholder_1["reason"]}")'
                    + f'| select( .count_of_placeholders_with_same_content == "3")'
                    + f'| select( .generated_by == "{placeholder_1["generatedBy"]}")'
                    + f'| select( .original_mime_type == "{placeholder_1["originalMimeType"]}")'
                    + f'| select( .requesting_supplier_name == "TEST_SUPPLIER")'
                    + f'| select( .sending_supplier_name == "TEST_SUPPLIER2")'
                    + f'| select( .requesting_practice_ods_code == "A00029")'
                    + f'| select( .sending_practice_ods_code == "B00157")',
                    telemetry,
                )

        finally:
            self.delete_index(index_name)
