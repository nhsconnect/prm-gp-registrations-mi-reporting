import json
from datetime import timedelta, datetime
from time import sleep

import jq
import pytest

from helpers.splunk import create_sample_event, create_document_response_payload, set_variables_on_query, \
    get_telemetry_from_splunk
from tests.test_base import EventType, TestBase


class TestTrendingDocumentAttachmentsGraph(TestBase):
    @pytest.mark.parametrize(
        "report_type, time_period, expected_output",
        [
            ("count", "month", {"0": {"time_period": "2023-10", "Successful": "2", "Unsuccessful": "1"}}),
            ("count", "week", {"0": {"time_period": "2023-Wk39", "Successful": "1", "Unsuccessful": "1"},
                               "1": {"time_period": "2023-Wk40", "Successful": "1", "Unsuccessful": "0"}}),
            ("count", "day", {"0": {"time_period": "2023-10-01", "Successful": "1", "Unsuccessful": "1"},
                              "1": {"time_period": "2023-10-08", "Successful": "1", "Unsuccessful": "0"}}),
            ("percentage", "month", {"0": {"time_period": "2023-10", "Successful": "66.67", "Unsuccessful": "33.33"}}),
            ("percentage", "week", {"0": {"time_period": "2023-Wk39", "Successful": "50.00", "Unsuccessful": "50.00"},
                                    "1": {"time_period": "2023-Wk40", "Successful": "100.00", "Unsuccessful": "0.00"}}),
            ("percentage", "day", {"0": {"time_period": "2023-10-01", "Successful": "50.00", "Unsuccessful": "50.00"},
                                   "1": {"time_period": "2023-10-08", "Successful": "100.00", "Unsuccessful": "0.00"}})
        ]
    )
    def test_trending_document_attachment_migration_outcome_report(self, report_type, time_period, expected_output):
        # Arrange
        index_name, index = self.create_index()

        # Reporting window
        report_start = datetime(year=2023, month=10, day=1)
        report_end = datetime(year=2023, month=10, day=31)
        cutoff = "0"

        try:
            for idx in range(2):
                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id=f'successful_document_response_{idx}',
                            registration_event_datetime=(
                                    report_start + timedelta(weeks=idx)).strftime("%Y-%m-%dT%H:%M:%S%z"),
                            event_type=EventType.DOCUMENT_RESPONSES.value,
                            sendingSupplierName="EMIS",
                            requestingSupplierName="TPP",
                            payload=create_document_response_payload(
                                successful=True
                            )
                        )
                    ),
                    sourcetype="myevent"
                )

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id="unsuccessful_document_response_test",
                        registration_event_datetime=report_start.strftime("%Y-%m-%dT%H:%M:%S%z"),
                        event_type=EventType.DOCUMENT_RESPONSES.value,
                        sendingSupplierName="EMIS",
                        requestingSupplierName="TPP",
                        payload=create_document_response_payload(
                            successful=False
                        )
                    )
                )
            )

            # Act
            test_query = self.generate_splunk_query_from_report(
                f'gp2gp_document_attachments_trending_report'
                f'/gp2gp_document_attachments_trending_report_migration_outcome_{report_type}'
            )

            test_query = set_variables_on_query(test_query, {
                "$index$": index_name,
                "$start_time$": report_start.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "$end_time$": report_end.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "$cutoff$": cutoff,
                "$time_period$": time_period
            })

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service
            )

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
        "report_type, migration_outcome, time_period, expected_time_format",
        [
            ("count", "unsuccessful", "month", "2023-02"),
            ("count", "unsuccessful", "week", "2023-Wk05"),
            ("count", "unsuccessful", "day", "2023-02-04"),
            ("percentage", "unsuccessful", "month", "2023-02"),
            ("percentage", "unsuccessful", "week", "2023-Wk05"),
            ("percentage", "unsuccessful", "day", "2023-02-04"),
            ("count", "successful", "month", "2023-02"),
            ("count", "successful", "week", "2023-Wk05"),
            ("count", "successful", "day", "2023-02-04"),
            ("percentage", "successful", "month", "2023-02"),
            ("percentage", "successful", "week", "2023-Wk05"),
            ("percentage", "successful", "day", "2023-02-04")
        ]
    )
    def test_trending_document_attachment_clinical_type_report(self, report_type, migration_outcome, time_period,
                                                               expected_time_format):
        # Arrange
        index_name, index = self.create_index()

        # Reporting window
        report_start = datetime(year=2023, month=2, day=1)
        report_end = datetime(year=2023, month=2, day=28)
        cutoff = "0"

        event_datetime = datetime(year=2023, month=2, day=4)

        try:
            count_of_clinical_types = {
                "SCANNED_DOCUMENT": (1, 10),
                "ORIGINAL_TEXT_DOCUMENT": (2, 9),
                "OCR_TEXT_DOCUMENT": (3, 8),
                "IMAGE": (4, 7),
                "AUDIO_DICTATION": (5, 6),
                "OTHER_AUDIO": (6, 5),
                "OTHER_DIGITAL_SIGNAL": (7, 4),
                "EDI_MESSAGE": (8, 3),
                "NOT_AVAILABLE": (9, 2),
                "OTHER": (10, 1),
            }

            for clinical_type, (count_of_successful_integrations, count_of_unsuccessful_integrations) \
                    in count_of_clinical_types.items():
                for idx in range(count_of_unsuccessful_integrations):
                    index.submit(
                        json.dumps(
                            create_sample_event(
                                conversation_id=f'{clinical_type}_response_unsuccessful_{idx}',
                                registration_event_datetime=event_datetime.strftime("%Y-%m-%dT%H:%M:%S%z"),
                                event_type=EventType.DOCUMENT_RESPONSES.value,
                                sendingSupplierName="EMIS",
                                requestingSupplierName="TPP",
                                payload=create_document_response_payload(
                                    successful=False,
                                    clinical_type=clinical_type
                                )
                            )
                        ),
                        sourcetype="myevent"
                    )

                for idx in range(count_of_successful_integrations):
                    index.submit(
                        json.dumps(
                            create_sample_event(
                                conversation_id=f'{clinical_type}_response_successful_{idx}',
                                registration_event_datetime=event_datetime.strftime("%Y-%m-%dT%H:%M:%S%z"),
                                event_type=EventType.DOCUMENT_RESPONSES.value,
                                sendingSupplierName="EMIS",
                                requestingSupplierName="TPP",
                                payload=create_document_response_payload(
                                    successful=True,
                                    clinical_type=clinical_type
                                )
                            )
                        ),
                        sourcetype="myevent",
                    )

            # Act
            test_query = self.generate_splunk_query_from_report(
                f'gp2gp_document_attachments_trending_report'
                f'/gp2gp_document_attachments_trending_report_{migration_outcome}_clinical_report_{report_type}'
            )

            test_query = set_variables_on_query(test_query, {
                "$index$": index_name,
                "$start_time$": report_start.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "$end_time$": report_end.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "$cutoff$": cutoff,
                "$time_period$": time_period
            })

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service
            )

            self.LOG.info(f'telemetry: {telemetry}')

            # Assert
            expected_output = {}

            if report_type == "count":
                if migration_outcome == "unsuccessful":
                    expected_output = {
                        "0": {"time_period": f"{expected_time_format}", "AUDIO_DICTATION": "6", "EDI_MESSAGE": "3",
                              "IMAGE": "7", "NOT_AVAILABLE": "2", "OCR_TEXT_DOCUMENT": "8",
                              "ORIGINAL_TEXT_DOCUMENT": "9", "OTHER": "1", "OTHER_AUDIO": "5",
                              "OTHER_DIGITAL_SIGNAL": "4", "SCANNED_DOCUMENT": "10"}
                    }
                elif migration_outcome == "successful":
                    expected_output = {
                        "0": {"time_period": f"{expected_time_format}", "AUDIO_DICTATION": "5", "EDI_MESSAGE": "8",
                              "IMAGE": "4", "NOT_AVAILABLE": "9", "OCR_TEXT_DOCUMENT": "3",
                              "ORIGINAL_TEXT_DOCUMENT": "2", "OTHER": "10", "OTHER_AUDIO": "6",
                              "OTHER_DIGITAL_SIGNAL": "7", "SCANNED_DOCUMENT": "1"}
                    }
            elif report_type == "percentage":
                if migration_outcome == "unsuccessful":
                    expected_output = {
                        "0": {"time_period": f"{expected_time_format}", "AUDIO_DICTATION": "10.91",
                              "EDI_MESSAGE": "5.45", "IMAGE": "12.73", "NOT_AVAILABLE": "3.64",
                              "OCR_TEXT_DOCUMENT": "14.55", "ORIGINAL_TEXT_DOCUMENT": "16.36", "OTHER": "1.82",
                              "OTHER_AUDIO": "9.09", "OTHER_DIGITAL_SIGNAL": "7.27", "SCANNED_DOCUMENT": "18.18"}
                    }
                elif migration_outcome == "successful":
                    expected_output = {
                        "0": {"time_period": f"{expected_time_format}", "AUDIO_DICTATION": "9.09",
                              "EDI_MESSAGE": "14.55", "IMAGE": "7.27", "NOT_AVAILABLE": "16.36",
                              "OCR_TEXT_DOCUMENT": "5.45", "ORIGINAL_TEXT_DOCUMENT": "3.64", "OTHER": "18.18",
                              "OTHER_AUDIO": "10.91",  "OTHER_DIGITAL_SIGNAL": "12.73", "SCANNED_DOCUMENT": "1.82"}
                    }

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
