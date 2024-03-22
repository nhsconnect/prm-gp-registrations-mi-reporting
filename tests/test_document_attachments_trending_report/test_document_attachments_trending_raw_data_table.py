import json
from datetime import timedelta, datetime
from time import sleep

import jq
import pytest

from helpers.splunk import (create_sample_event,
                            get_telemetry_from_splunk,
                            set_variables_on_query, create_document_response_payload)
from tests.test_base import EventType, TestBase


class TestDocumentAttachmentsTrendingRawDataTable(TestBase):
    @pytest.mark.parametrize(
        "time_period, expected_column_format, expected_number_of_events",
        [
            ("month", "%Y-%m", 4),
            ("week", "%Y-Wk%W", 3),
            ("day", "%Y-%m-%d", 2),
        ]
    )
    def test_document_attachments_trending_raw_data_table_column_token(self, time_period, expected_column_format,
                                                                       expected_number_of_events):
        # Arrange
        index_name, index = self.create_index()

        # reporting window
        report_start = datetime(year=2023, month=10, day=1)
        report_end = datetime(year=2023, month=10, day=31)
        cutoff = "0"

        line = "Unsuccessful"

        event_datetime = datetime(year=2023, month=10, day=15)
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

        try:
            for idx in range(expected_number_of_events):
                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id=f'document_attachment_conv_{idx}',
                            registration_event_datetime=event_datetime.strftime("%Y-%m-%dT%H:%M:%S%z"),
                            event_type=EventType.DOCUMENT_RESPONSES.value,
                            sendingSupplierName="EMIS",
                            requestingSupplierName="TPP",
                            payload=create_document_response_payload(
                                successful=False,
                                clinical_type="SCANNED_DOCUMENT",
                                reason="test reason",
                                size_bytes=4096,
                                mime_type="application/pdf"
                            ),
                        )
                    ),
                    sourcetype="myevent",
                )

                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id=f'conv_should_not_appear_id_{idx}',
                            registration_event_datetime=other_event_datetime.strftime("%Y-%m-%dT%H:%M:%S%z"),
                            event_type=EventType.DOCUMENT_RESPONSES.value,
                            sendingSupplierName="EMIS",
                            requestingSupplierName="TPP",
                            payload=create_document_response_payload(
                                successful=False,
                                clinical_type="SCANNED_DOCUMENT",
                                reason="test reason",
                                size_bytes=4096,
                                mime_type="application/pdf"
                            ),
                        )
                    ),
                    sourcetype="myevent",
                )

            # Act
            test_query = self.generate_splunk_query_from_report(
                "gp2gp_document_attachments_trending_report/gp2gp_document_attachments_trending_report_raw_data_table"
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
                    "$line$": line,
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
                    + f'| select( .conversation_id == "document_attachment_conv_{idx}") '
                    + f'| select( .reporting_supplier_name == "TEST_SYSTEM_SUPPLIER") '
                    + f'| select( .requesting_supplier_name == "TPP") '
                    + f'| select( .sending_supplier_name == "EMIS") '
                    + f'| select( .reporting_practice_ods_code == "A00029") '
                    + f'| select( .requesting_practice_ods_code == "A00029") '
                    + f'| select( .sending_practice_ods_code == "B00157") '
                    + f'| select( .attachment_type == "SCANNED_DOCUMENT") '
                    + f'| select( .integrated_successfully == "false") '
                    + f'| select( .failed_to_integrate_reason == "test reason") '
                    + f'| select( .size_greater_than_100mb == "false") '
                    + f'| select( .mime_type == "application/pdf") '
                    , telemetry
                )

        finally:
            self.delete_index(index_name)

    @pytest.mark.parametrize(
        "time_period, expected_date_format, line",
        [
            ("month", "%Y-%m", "SCANNED_DOCUMENT"),
            ("month", "%Y-%m", "ORIGINAL_TEXT_DOCUMENT"),
            ("week", "%Y-Wk%W", "OCR_TEXT_DOCUMENT"),
            ("week", "%Y-Wk%W", "IMAGE"),
            ("day", "%Y-%m-%d", "AUDIO_DICTATION"),
            ("day", "%Y-%m-%d", "OTHER_AUDIO"),
            ("week", "%Y-Wk%W", "OTHER_DIGITAL_SIGNAL"),
            ("week", "%Y-Wk%W", "EDI_MESSAGE"),
            ("day", "%Y-%m-%d", "NOT_AVAILABLE"),
            ("day", "%Y-%m-%d", "OTHER"),
        ]
    )
    def test_document_attachments_trending_raw_data_table_line_token(self, time_period, expected_date_format, line):
        # Arrange
        index_name, index = self.create_index()

        # reporting window
        report_start = datetime(year=2023, month=10, day=1)
        report_end = datetime(year=2023, month=10, day=31)
        cutoff = "0"

        event_datetime = datetime(year=2023, month=10, day=15)
        selected_column = event_datetime.strftime(expected_date_format)
        self.LOG.info(f"selected column for {line} data: {selected_column}")

        migration_outcomes = {"successfully": True, "unsuccessfully": False}

        if time_period == "day":
            other_event_datetime = event_datetime + timedelta(days=1, hours=8)
        elif time_period == "week":
            other_event_datetime = event_datetime + timedelta(weeks=1)
        elif time_period == "month":
            other_event_datetime = event_datetime.replace(month=11)

        self.LOG.info(f"current_event: {event_datetime.strftime('%Y-%m-%dT%H:%M:%S%z')}")
        self.LOG.info(f"other_event: {other_event_datetime.strftime('%Y-%m-%dT%H:%M:%S%z')}")

        try:
            for outcome in migration_outcomes:
                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id=f'document_attachment_conv_integrated_{outcome}',
                            registration_event_datetime=event_datetime.strftime("%Y-%m-%dT%H:%M:%S%z"),
                            event_type=EventType.DOCUMENT_RESPONSES.value,
                            sendingSupplierName="EMIS",
                            requestingSupplierName="TPP",
                            payload=create_document_response_payload(
                                successful=migration_outcomes[outcome],
                                clinical_type=line,
                                reason="test reason",
                                size_bytes=4096,
                                mime_type="application/pdf"
                            ),
                        )
                    ),
                    sourcetype="myevent",
                )

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=f'conv_should_not_appear_id',
                        registration_event_datetime=other_event_datetime.strftime("%Y-%m-%dT%H:%M:%S%z"),
                        event_type=EventType.DOCUMENT_RESPONSES.value,
                        sendingSupplierName="EMIS",
                        requestingSupplierName="TPP",
                        payload=create_document_response_payload(
                            successful=False,
                            clinical_type=line,
                            reason="test reason",
                            size_bytes=4096,
                            mime_type="application/pdf"
                        ),
                    )
                ),
                sourcetype="myevent",
            )

            # Act
            test_query = self.generate_splunk_query_from_report(
                "gp2gp_document_attachments_trending_report/gp2gp_document_attachments_trending_report_raw_data_table"
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
                    "$line$": line,
                },
            )

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service
            )
            self.LOG.info(f"telemetry: {telemetry}")

            # Assert
            assert len(telemetry) == 2

            for outcome in migration_outcomes:
                assert jq.all(
                    f".[] "
                    + f'| select( .conversation_id == "document_attachment_conv_integrated_{outcome}") '
                    + f'| select( .reporting_supplier_name == "TEST_SYSTEM_SUPPLIER") '
                    + f'| select( .requesting_supplier_name == "TPP") '
                    + f'| select( .sending_supplier_name == "EMIS") '
                    + f'| select( .reporting_practice_ods_code == "A00029") '
                    + f'| select( .requesting_practice_ods_code == "A00029") '
                    + f'| select( .sending_practice_ods_code == "B00157") '
                    + f'| select( .attachment_type == "{line}") '
                    + f'| select( .integrated_successfully == "{str(migration_outcomes[outcome]).lower()}") '
                    + f'| select( .failed_to_integrate_reason == "test reason") '
                    + f'| select( .size_greater_than_100mb == "false") '
                    + f'| select( .mime_type == "application/pdf") '
                    , telemetry
                )

        finally:
            self.delete_index(index_name)