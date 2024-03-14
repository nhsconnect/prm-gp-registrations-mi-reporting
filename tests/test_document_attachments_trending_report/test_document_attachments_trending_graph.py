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
