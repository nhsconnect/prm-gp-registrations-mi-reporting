import logging
import os
from enum import Enum
import pytest
import json
from time import sleep
from splunklib import client
import jq
from helpers.splunk import (
    get_telemetry_from_splunk,
    get_or_create_index,
    create_sample_event,
    set_variables_on_query,
    create_integration_payload,
    create_error_payload,
    create_transfer_compatibility_payload,
    create_ehr_response_payload,
)
from datetime import datetime, timedelta
from jinja2 import Environment, FileSystemLoader
from tests.test_base import TestBase, EventType
from helpers.datetime_helper import (
    create_date_time,
    generate_report_start_date,
    generate_report_end_date,
)
import uuid


class TestPlaceholderRawDataTable(TestBase):
    def test_raw_data_table_output(self):
        # reporting window
        report_start = generate_report_start_date()
        report_end = generate_report_end_date()
        cutoff = "0"

        placeholder = {
            "generatedBy": "SENDER",
            "clinicalType": "SCANNED_DOCUMENT",
            "reason": "FILE_NOT_FOUND",
            "originalMimeType": "application/pdf",
        }
        placeholders = [placeholder] * 6
        payload = {
            "ehr": {
                "ehrStructuredSizeBytes": 4096,
                "placeholders": placeholders,
            }
        }

        try:
            # Arrange
            index_name, index = self.create_index()

            random_conversation_id = f"test_placeholder_graph_{uuid.uuid4()}"

            # payload = create_ehr_response_payload(number_of_placeholders=6)

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=random_conversation_id,
                        registration_event_datetime=create_date_time(
                            date=report_start, time="05:00:00"
                        ),
                        event_type=EventType.EHR_RESPONSES.value,
                        payload=payload,
                    )
                ),
                sourcetype="myevent",
            )

            # Act
            test_query = self.generate_splunk_query_from_report(
                "gp2gp_placeholder_snapshot_report/"
                "gp2gp_placeholder_snapshot_report_raw_data_table"
            )

            test_query = set_variables_on_query(
                test_query,
                {
                    "$index$": index_name,
                    "$start_time$": report_start.strftime("%Y-%m-%dT%H:%m:%s"),
                    "$end_time$": report_end.strftime("%Y-%m-%dT%H:%m:%s"),
                    "$cutoff$": cutoff,
                },
            )

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service
            )
            self.LOG.info(f"telemetry: {telemetry}")

            # Assert
            # clinical_type_field = payload["ehr"]["placeholders"][:]["clinicalType"]
            # generated_by_field = payload["ehr"]["placeholders"][:]["generatedBy"]
            # original_mime_type_field = payload["ehr"]["placeholders"][:]["originalMimeType"]
            # reason_field = payload["ehr"]["placeholders"][:]["reason"]
            # list_zipped_fields = list(zip(clinical_type_field,generated_by_field,original_mime_type_field,reason_field))
            # count_field_combos = {field_combo: list_zipped_fields.count(field_combo)
            #                       for field_combo in list_zipped_fields}

            assert jq.all(
                f".[0] "
                + f'| select( .conversation_id == "{random_conversation_id}") '
                # + f'| select( .total_number_of_placeholders == "6") '
                # + f'| select( .clinical_type == "{placeholder["clinicalType"]}")'
                # + f'| select( .reason == "{placeholder["reason"]}")'
                # + f'| select( .count_of_clinical_type_and_reason == "6")'
                # + f'| select( .generated_by == "{placeholder["generatedBy"]}")'
                # + f'| select( .original_mime_type == "{placeholder["originalMimeType"]}")'
                # + f'| select( .reporting_system_supplier == "TEST_SYSTEM_SUPPLIER")'
                # + f'| select( .requesting_supplier_name == "TEST_SUPPLIER")'
                # + f'| select( .sending_supplier_name == "TEST_SUPPLIER2")'
                # + f'| select( .requesting_practice_ods_code == "A00029")'
                # + f'| select( .sending_practice_ods_code == "B00157")'
                ,telemetry
            ) 
    

        finally:
            self.delete_index(index_name)
