import json
import random
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

    def test_count_clinical_type_scanned_documents(self):
        # Arrange
        index_name, index = self.create_index()

        # reporting window
        report_start = generate_report_start_date()
        report_end = generate_report_end_date()
        cutoff = "0"

        try:
            # links the clinical type to 2 random ints that will determine the num
            # successful and unsuccessful events produced.
            clinical_type_count_dict = {
                "SCANNED_DOCUMENT": (random.randint(1, 10), random.randint(1, 10)),
                "ORIGINAL_TEXT_DOCUMENT": (random.randint(1, 10), random.randint(1, 10)),
                "OCR_TEXT_DOCUMENT": (random.randint(1, 10), random.randint(1, 10)),
                "IMAGE": (random.randint(1, 10), random.randint(1, 10)),
                "AUDIO_DICTATION": (random.randint(1, 10), random.randint(1, 10)),
                "OTHER_AUDIO": (random.randint(1, 10), random.randint(1, 10)),
                "OTHER_DIGITAL_SIGNAL": (random.randint(1, 10), random.randint(1, 10)),
                "EDI_MESSAGE": (random.randint(1, 10), random.randint(1, 10)),
                "NOT_AVAILABLE": (random.randint(1, 10), random.randint(1, 10)),
                "OTHER": (random.randint(1, 10), random.randint(1, 10)),
            }

            # testing successful=False records not counted

            for clinical_type, (num_successful_records, num_unsuccessful_records) in clinical_type_count_dict.items():
                for idx in range(num_successful_records):
                    index.submit(
                        json.dumps(
                            create_sample_event(
                                conversation_id=f"{clinical_type}_response_success_{idx}",
                                registration_event_datetime=(
                                    datetime_utc_now()
                                ).strftime("%Y-%m-%dT%H:%M:%S%z"),
                                event_type=EventType.DOCUMENT_RESPONSES.value,
                                sendingSupplierName="EMIS",
                                requestingSupplierName="TPP",
                                payload=create_document_response_payload(
                                    successful=True,
                                    clinical_type=clinical_type
                                ),
                            )
                        ),
                        sourcetype="myevent",
                    )

                for idx in range(num_unsuccessful_records):
                    index.submit(
                        json.dumps(
                            create_sample_event(
                                conversation_id=f"{clinical_type}_response_fail_{idx}",
                                registration_event_datetime=(
                                    datetime_utc_now()
                                ).strftime("%Y-%m-%dT%H:%M:%S%z"),
                                event_type=EventType.DOCUMENT_RESPONSES.value,
                                sendingSupplierName="EMIS",
                                requestingSupplierName="TPP",
                                payload=create_document_response_payload(
                                    successful=False,
                                    clinical_type=clinical_type
                                ),
                            )
                        ),
                        sourcetype="myevent",
                    )

            # Act
            test_query = self.generate_splunk_query_from_report(
                "gp2gp_document_attachments_snapshot_report"
                "/gp2gp_document_attachments_snapshot_report_count"
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

            expected_values = {"0": {"Clinical Type": "AUDIO_DICTATION",
                                     "Success": clinical_type_count_dict["AUDIO_DICTATION"][0],
                                     "Fail": clinical_type_count_dict["AUDIO_DICTATION"][1],
                                     },
                               "1": {"Clinical Type": "EDI_MESSAGE",
                                     "Success": clinical_type_count_dict["EDI_MESSAGE"][0],
                                     "Fail": clinical_type_count_dict["EDI_MESSAGE"][1],
                                     },
                               "2": {"Clinical Type": "IMAGE",
                                     "Success": clinical_type_count_dict["IMAGE"][0],
                                     "Fail": clinical_type_count_dict["IMAGE"][1],
                                     },
                               "3": {"Clinical Type": "NOT_AVAILABLE",
                                     "Success": clinical_type_count_dict["NOT_AVAILABLE"][0],
                                     "Fail": clinical_type_count_dict["NOT_AVAILABLE"][1],
                                     },
                               "4": {"Clinical Type": "OCR_TEXT_DOCUMENT",
                                     "Success": clinical_type_count_dict["OCR_TEXT_DOCUMENT"][0],
                                     "Fail": clinical_type_count_dict["OCR_TEXT_DOCUMENT"][1],
                                     },
                               "5": {"Clinical Type": "ORIGINAL_TEXT_DOCUMENT",
                                     "Success": clinical_type_count_dict["ORIGINAL_TEXT_DOCUMENT"][0],
                                     "Fail": clinical_type_count_dict["ORIGINAL_TEXT_DOCUMENT"][1],
                                     },
                               "6": {"Clinical Type": "OTHER",
                                     "Success": clinical_type_count_dict["OTHER"][0],
                                     "Fail": clinical_type_count_dict["OTHER"][1],
                                     },
                               "7": {"Clinical Type": "OTHER_AUDIO",
                                     "Success": clinical_type_count_dict["OTHER_AUDIO"][0],
                                     "Fail": clinical_type_count_dict["OTHER_AUDIO"][1],
                                     },
                               "8": {"Clinical Type": "OTHER_DIGITAL_SIGNAL",
                                     "Success": clinical_type_count_dict["OTHER_DIGITAL_SIGNAL"][0],
                                     "Fail": clinical_type_count_dict["OTHER_DIGITAL_SIGNAL"][1],
                                     },
                               "9": {"Clinical Type": "SCANNED_DOCUMENT",
                                     "Success": clinical_type_count_dict["SCANNED_DOCUMENT"][0],
                                     "Fail": clinical_type_count_dict["SCANNED_DOCUMENT"][1],
                                     },
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


    def test_percentage_clinical_type_scanned_documents(self):
        # Arrange
        index_name, index = self.create_index()

        # reporting window
        report_start = generate_report_start_date()
        report_end = generate_report_end_date()
        cutoff = "0"

        try:
            # links the clinical type to 2 random ints that will determine the num
            # successful and unsuccessful events produced.
            clinical_type_count_dict = {
                "SCANNED_DOCUMENT": (random.randint(1, 10), random.randint(1, 10)),
                "ORIGINAL_TEXT_DOCUMENT": (random.randint(1, 10), random.randint(1, 10)),
                "OCR_TEXT_DOCUMENT": (random.randint(1, 10), random.randint(1, 10)),
                "IMAGE": (random.randint(1, 10), random.randint(1, 10)),
                "AUDIO_DICTATION": (random.randint(1, 10), random.randint(1, 10)),
                "OTHER_AUDIO": (random.randint(1, 10), random.randint(1, 10)),
                "OTHER_DIGITAL_SIGNAL": (random.randint(1, 10), random.randint(1, 10)),
                "EDI_MESSAGE": (random.randint(1, 10), random.randint(1, 10)),
                "NOT_AVAILABLE": (random.randint(1, 10), random.randint(1, 10)),
                "OTHER": (random.randint(1, 10), random.randint(1, 10)),
            }
            total_num_document_migrations = sum([int1+int2 for int1, int2 in clinical_type_count_dict.values()])

            # testing successful=False records not counted

            for clinical_type, (num_successful_records, num_unsuccessful_records) in clinical_type_count_dict.items():
                for idx in range(num_successful_records):
                    index.submit(
                        json.dumps(
                            create_sample_event(
                                conversation_id=f"{clinical_type}_response_success_{idx}",
                                registration_event_datetime=(
                                    datetime_utc_now()
                                ).strftime("%Y-%m-%dT%H:%M:%S%z"),
                                event_type=EventType.DOCUMENT_RESPONSES.value,
                                sendingSupplierName="EMIS",
                                requestingSupplierName="TPP",
                                payload=create_document_response_payload(
                                    successful=True,
                                    clinical_type=clinical_type
                                ),
                            )
                        ),
                        sourcetype="myevent",
                    )

                for idx in range(num_unsuccessful_records):
                    index.submit(
                        json.dumps(
                            create_sample_event(
                                conversation_id=f"{clinical_type}_response_fail_{idx}",
                                registration_event_datetime=(
                                    datetime_utc_now()
                                ).strftime("%Y-%m-%dT%H:%M:%S%z"),
                                event_type=EventType.DOCUMENT_RESPONSES.value,
                                sendingSupplierName="EMIS",
                                requestingSupplierName="TPP",
                                payload=create_document_response_payload(
                                    successful=False,
                                    clinical_type=clinical_type
                                ),
                            )
                        ),
                        sourcetype="myevent",
                    )

            # Act
            test_query = self.generate_splunk_query_from_report(
                "gp2gp_document_attachments_snapshot_report"
                "/gp2gp_document_attachments_snapshot_report_percentage"
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

            expected_values = {"0": {"Clinical Type": "AUDIO_DICTATION",
                                     "Success": clinical_type_count_dict["AUDIO_DICTATION"][0],
                                     "Fail": clinical_type_count_dict["AUDIO_DICTATION"][1],
                                     },
                               "1": {"Clinical Type": "EDI_MESSAGE",
                                     "Success": clinical_type_count_dict["EDI_MESSAGE"][0],
                                     "Fail": clinical_type_count_dict["EDI_MESSAGE"][1],
                                     },
                               "2": {"Clinical Type": "IMAGE",
                                     "Success": clinical_type_count_dict["IMAGE"][0],
                                     "Fail": clinical_type_count_dict["IMAGE"][1],
                                     },
                               "3": {"Clinical Type": "NOT_AVAILABLE",
                                     "Success": clinical_type_count_dict["NOT_AVAILABLE"][0],
                                     "Fail": clinical_type_count_dict["NOT_AVAILABLE"][1],
                                     },
                               "4": {"Clinical Type": "OCR_TEXT_DOCUMENT",
                                     "Success": clinical_type_count_dict["OCR_TEXT_DOCUMENT"][0],
                                     "Fail": clinical_type_count_dict["OCR_TEXT_DOCUMENT"][1],
                                     },
                               "5": {"Clinical Type": "ORIGINAL_TEXT_DOCUMENT",
                                     "Success": clinical_type_count_dict["ORIGINAL_TEXT_DOCUMENT"][0],
                                     "Fail": clinical_type_count_dict["ORIGINAL_TEXT_DOCUMENT"][1],
                                     },
                               "6": {"Clinical Type": "OTHER",
                                     "Success": clinical_type_count_dict["OTHER"][0],
                                     "Fail": clinical_type_count_dict["OTHER"][1],
                                     },
                               "7": {"Clinical Type": "OTHER_AUDIO",
                                     "Success": clinical_type_count_dict["OTHER_AUDIO"][0],
                                     "Fail": clinical_type_count_dict["OTHER_AUDIO"][1],
                                     },
                               "8": {"Clinical Type": "OTHER_DIGITAL_SIGNAL",
                                     "Success": clinical_type_count_dict["OTHER_DIGITAL_SIGNAL"][0],
                                     "Fail": clinical_type_count_dict["OTHER_DIGITAL_SIGNAL"][1],
                                     },
                               "9": {"Clinical Type": "SCANNED_DOCUMENT",
                                     "Success": clinical_type_count_dict["SCANNED_DOCUMENT"][0],
                                     "Fail": clinical_type_count_dict["SCANNED_DOCUMENT"][1],
                                     },
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
