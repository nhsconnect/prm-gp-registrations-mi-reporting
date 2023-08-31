import json
from time import sleep
import jq

from helpers.datetime_helper import generate_report_start_date, generate_report_end_date, datetime_utc_now
from helpers.splunk import create_sample_event, create_transfer_compatibility_payload, set_variables_on_query, \
    get_telemetry_from_splunk, create_document_response_payload
from tests.test_base import EventType, TestBase


class TestSnapshotDocumentAttachmentsGraph(TestBase):
    def test_num_successfully_integrate_attachments(self):
        # Arrange
        index_name, index = self.create_index()

        # reporting window
        report_start = generate_report_start_date()
        report_end = generate_report_end_date()
        cutoff = "0"

        try:

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id="successful_document_response_1",
                        registration_event_datetime=(
                            datetime_utc_now()
                        ).strftime("%Y-%m-%dT%H:%M:%S%z"),
                        event_type=EventType.DOCUMENT_RESPONSES.value,
                        sendingSupplierName="EMIS",
                        requestingSupplierName="TPP",
                        payload=create_document_response_payload(
                            successful=True,
                        ),
                    )
                ),
                sourcetype="myevent",
            )

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id="successful_document_response_2",
                        registration_event_datetime=(
                            datetime_utc_now()
                        ).strftime("%Y-%m-%dT%H:%M:%S%z"),
                        event_type=EventType.DOCUMENT_RESPONSES.value,
                        sendingSupplierName="EMIS",
                        requestingSupplierName="TPP",
                        payload=create_document_response_payload(
                            successful=True,
                        ),
                    )
                ),
                sourcetype="myevent",
            )

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id="unsuccessful_document_response_1",
                        registration_event_datetime=(
                            datetime_utc_now()
                        ).strftime("%Y-%m-%dT%H:%M:%S%z"),
                        event_type=EventType.DOCUMENT_RESPONSES.value,
                        sendingSupplierName="EMIS",
                        requestingSupplierName="TPP",
                        payload=create_document_response_payload(
                            successful=False,
                        ),
                    )
                ),
                sourcetype="myevent",
            )


            # Act
            test_query = self.generate_splunk_query_from_report(
                "gp2gp_document_attachments_snapshot_report"
                "/gp2gp_document_attachments_snapshot_report_integrated_successfully_count"
            )

            test_query = set_variables_on_query(
                test_query,
                {
                    "$index$": index_name,
                    "$start_time$": report_start.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    "$end_time$": report_end.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    "$cutoff$": cutoff,
                },
            )

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service
            )
            self.LOG.info(f"telemetry: {telemetry}")

            # Assert

            assert jq.first(
                f'.[] | select( .count_of_successful_document_migrations=="2")',
                telemetry,
            )

        finally:
            self.delete_index(index_name)

    def test_num_unsuccessfully_integrate_attachments(self):
        # Arrange
        index_name, index = self.create_index()

        # reporting window
        report_start = generate_report_start_date()
        report_end = generate_report_end_date()
        cutoff = "0"

        try:

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id="successful_document_response_1",
                        registration_event_datetime=(
                            datetime_utc_now()
                        ).strftime("%Y-%m-%dT%H:%M:%S%z"),
                        event_type=EventType.DOCUMENT_RESPONSES.value,
                        sendingSupplierName="EMIS",
                        requestingSupplierName="TPP",
                        payload=create_document_response_payload(
                            successful=True,
                        ),
                    )
                ),
                sourcetype="myevent",
            )

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id="successful_document_response_2",
                        registration_event_datetime=(
                            datetime_utc_now()
                        ).strftime("%Y-%m-%dT%H:%M:%S%z"),
                        event_type=EventType.DOCUMENT_RESPONSES.value,
                        sendingSupplierName="EMIS",
                        requestingSupplierName="TPP",
                        payload=create_document_response_payload(
                            successful=True,
                        ),
                    )
                ),
                sourcetype="myevent",
            )

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id="unsuccessful_document_response_1",
                        registration_event_datetime=(
                            datetime_utc_now()
                        ).strftime("%Y-%m-%dT%H:%M:%S%z"),
                        event_type=EventType.DOCUMENT_RESPONSES.value,
                        sendingSupplierName="EMIS",
                        requestingSupplierName="TPP",
                        payload=create_document_response_payload(
                            successful=False,
                        ),
                    )
                ),
                sourcetype="myevent",
            )


            # Act
            test_query = self.generate_splunk_query_from_report(
                "gp2gp_document_attachments_snapshot_report"
                "/gp2gp_document_attachments_snapshot_report_integrated_unsuccessfully_count"
            )

            test_query = set_variables_on_query(
                test_query,
                {
                    "$index$": index_name,
                    "$start_time$": report_start.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    "$end_time$": report_end.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    "$cutoff$": cutoff,
                },
            )

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service
            )
            self.LOG.info(f"telemetry: {telemetry}")

            # Assert

            assert jq.first(
                f'.[] | select( .count_of_unsuccessful_document_migrations=="1")',
                telemetry,
            )

        finally:
            self.delete_index(index_name)