import json
import uuid
from datetime import timedelta
from time import sleep

import jq

from helpers.datetime_helper import (datetime_utc_now,
                                     generate_report_end_date,
                                     generate_report_start_date)
from helpers.splunk import (create_sample_event,
                            create_transfer_compatibility_payload,
                            get_telemetry_from_splunk,
                            set_variables_on_query, create_document_response_payload)
from tests.test_base import EventType, TestBase


class TestDocumentAttachmentsRawDatatable(TestBase):

    def test_document_attachments_raw_data_table_output(self):
        """
        Tests the output as requested for the document attachments raw data table
        """

        index_name, index = self.create_index()

        # reporting window
        report_start = generate_report_start_date()
        report_end = generate_report_end_date()
        cutoff = "0"

        try:

            # Arrange
            random_conversation_id = f"test_document_attachments_raw_data_table_{uuid.uuid4()}"

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id="conv_id_should_not_appear",
                        registration_event_datetime=(
                                datetime_utc_now() - timedelta(minutes=6)
                        ).strftime("%Y-%m-%dT%H:%M:%S%z"),
                        event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                        sendingSupplierName="EMIS",
                        requestingSupplierName="TPP",
                        payload=create_transfer_compatibility_payload(
                            internalTransfer=False,
                            transferCompatible=True,
                            reason="test",
                        ),
                    )
                ),
                sourcetype="myevent",
            )

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=random_conversation_id,
                        registration_event_datetime=(
                                datetime_utc_now()
                        ).strftime("%Y-%m-%dT%H:%M:%S%z"),
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
                "gp2gp_document_attachments_snapshot_report"
                "/gp2gp_document_attachments_snapshot_report_raw_data_table"
            )

            test_query = set_variables_on_query(
                test_query,
                {
                    "$index$": index_name,
                    "$start_time$": report_start.strftime("%Y-%m-%dT%H:%m:%s"),
                    "$end_time$": report_end.strftime("%Y-%m-%dT%H:%m:%s"),
                    "$cutoff$": cutoff,
                    "$column$": "SCANNED_DOCUMENT",
                    "$legend$": "Fail",
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
