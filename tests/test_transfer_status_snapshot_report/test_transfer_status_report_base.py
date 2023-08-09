import os
import json
import pytest
from time import sleep
from splunklib import client
import jq
from helpers.splunk import (
    create_ehr_response_payload,
    create_registration_payload,
    get_telemetry_from_splunk,
    create_sample_event,
    set_variables_on_query,
    create_integration_payload,
    create_transfer_compatibility_payload,
)
from tests.test_base import TestBase, EventType
from datetime import timedelta, datetime
from helpers.datetime_helper import (
    datetime_utc_now,
    create_date_time,
    generate_report_start_date,
    generate_report_end_date,
)


class TestTransferStatusReportBase(TestBase):
    def test_total_eligible_for_electronic_transfer(self):
        # Arrange
        index_name, index = self.create_index()

        # reporting window
        report_start = datetime.today().date().replace(day=1)
        report_end = datetime.today().date().replace(day=28)
        cutoff = "0"

        try:
            index.submit(
                json.dumps(
                    create_sample_event(
                        "test_total_eligible_for_electronic_transfer_1",
                        registration_event_datetime=create_date_time(
                            date=report_start, time="08:00:00"
                        ),
                        event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                        sendingPracticeSupplierName="EMIS",
                        requestingPracticeSupplierName="TPP",
                        payload=create_transfer_compatibility_payload(
                            internalTransfer=False,
                            transferCompatible=True,
                            reason="test1",
                        ),
                    )
                ),
                sourcetype="myevent",
            )

            index.submit(
                json.dumps(
                    create_sample_event(
                        "test_total_eligible_for_electronic_transfer_2",
                        registration_event_datetime=create_date_time(
                            date=report_start, time="09:00:00"
                        ),
                        event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                        sendingPracticeSupplierName="EMIS",
                        requestingPracticeSupplierName="TPP",
                        payload=create_transfer_compatibility_payload(
                            internalTransfer=False,
                            transferCompatible=True,
                            reason="test2",
                        ),
                    )
                ),
                sourcetype="myevent",
            )

            index.submit(
                json.dumps(
                    create_sample_event(
                        "test_total_eligible_for_electronic_transfer_3",
                        registration_event_datetime=create_date_time(
                            date=report_start, time="10:00:00"
                        ),
                        event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                        sendingPracticeSupplierName="EMIS",
                        requestingPracticeSupplierName="TPP",
                        payload=create_transfer_compatibility_payload(
                            internalTransfer=True,
                            transferCompatible=True,
                            reason="test1",
                        ),
                    )
                ),
                sourcetype="myevent",
            )

            # Act

            test_query = self.generate_splunk_query_from_report(
                "gp2gp_transfer_status_snapshot_report/gp2gp_transfer_status_report_snapshot_base"
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
                '.[] | select( .total_eligible_for_electronic_transfer == "2" ) ',
                telemetry,
            )

        finally:
            self.delete_index(index_name)

    def test_successfully_integrated(self):
        # Arrange
        index_name, index = self.create_index()

        # reporting window
        report_start = datetime.today().date().replace(day=1)
        report_end = datetime.today().date().replace(day=28)
        cutoff = "0"

        try:
            # successfully integrated - #1

            index.submit(
                json.dumps(
                    create_sample_event(
                        "test_successfully_integrated_1",
                        registration_event_datetime=create_date_time(
                            date=report_start, time="09:00:00"
                        ),
                        event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                        sendingPracticeSupplierName="EMIS",
                        requestingPracticeSupplierName="TPP",
                        payload=create_transfer_compatibility_payload(
                            internalTransfer=False,
                            transferCompatible=True,
                            reason="test1",
                        ),
                    )
                ),
                sourcetype="myevent",
            )

            index.submit(
                json.dumps(
                    create_sample_event(
                        "test_successfully_integrated_1",
                        registration_event_datetime=create_date_time(
                            date=report_start, time="08:00:00"
                        ),
                        event_type=EventType.EHR_INTEGRATIONS.value,
                        payload=create_integration_payload(outcome="INTEGRATED"),
                    )
                ),
                sourcetype="myevent",
            )

            # successfully integrated - #2

            index.submit(
                json.dumps(
                    create_sample_event(
                        "test_successfully_integrated_2",
                        registration_event_datetime=create_date_time(
                            date=report_start, time="09:00:00"
                        ),
                        event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                        sendingPracticeSupplierName="EMIS",
                        requestingPracticeSupplierName="TPP",
                        payload=create_transfer_compatibility_payload(
                            internalTransfer=False,
                            transferCompatible=True,
                            reason="test1",
                        ),
                    )
                ),
                sourcetype="myevent",
            )

            index.submit(
                json.dumps(
                    create_sample_event(
                        "test_successfully_integrated_2",
                        registration_event_datetime=create_date_time(
                            date=report_start, time="08:10:00"
                        ),
                        event_type=EventType.EHR_INTEGRATIONS.value,
                        payload=create_integration_payload(
                            outcome="INTEGRATED_AND_SUPPRESSED"
                        ),
                    )
                ),
                sourcetype="myevent",
            )

            # successfully integrated - #3

            index.submit(
                json.dumps(
                    create_sample_event(
                        "test_successfully_integrated_3",
                        registration_event_datetime=create_date_time(
                            date=report_start, time="09:00:00"
                        ),
                        event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                        sendingPracticeSupplierName="EMIS",
                        requestingPracticeSupplierName="TPP",
                        payload=create_transfer_compatibility_payload(
                            internalTransfer=False,
                            transferCompatible=True,
                            reason="test1",
                        ),
                    )
                ),
                sourcetype="myevent",
            )

            index.submit(
                json.dumps(
                    create_sample_event(
                        "test_successfully_integrated_3",
                        registration_event_datetime=create_date_time(
                            date=report_start, time="08:20:00"
                        ),
                        event_type=EventType.EHR_INTEGRATIONS.value,
                        payload=create_integration_payload(
                            outcome="SUPPRESSED_AND_REACTIVATED"
                        ),
                    )
                ),
                sourcetype="myevent",
            )

            # rejected

            index.submit(
                json.dumps(
                    create_sample_event(
                        "test_successfully_integrated_rejected",
                        registration_event_datetime=create_date_time(
                            date=report_start, time="09:00:00"
                        ),
                        event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                        sendingPracticeSupplierName="EMIS",
                        requestingPracticeSupplierName="TPP",
                        payload=create_transfer_compatibility_payload(
                            internalTransfer=False,
                            transferCompatible=True,
                            reason="test1",
                        ),
                    )
                ),
                sourcetype="myevent",
            )

            index.submit(
                json.dumps(
                    create_sample_event(
                        "test_successfully_integrated_rejected",
                        registration_event_datetime=create_date_time(
                            date=report_start, time="09:00:00"
                        ),
                        event_type=EventType.EHR_INTEGRATIONS.value,
                        payload=create_integration_payload(outcome="REJECTED"),
                    )
                ),
                sourcetype="myevent",
            )

            # failed to integrate # 1

            index.submit(
                json.dumps(
                    create_sample_event(
                        "test_successfully_integrated_failed_to_integrate_#1",
                        registration_event_datetime=create_date_time(
                            date=report_start, time="09:00:00"
                        ),
                        event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                        sendingPracticeSupplierName="EMIS",
                        requestingPracticeSupplierName="TPP",
                        payload=create_transfer_compatibility_payload(
                            internalTransfer=False,
                            transferCompatible=True,
                            reason="test1",
                        ),
                    )
                ),
                sourcetype="myevent",
            )

            index.submit(
                json.dumps(
                    create_sample_event(
                        "test_successfully_integrated_failed_to_integrate_#1",
                        registration_event_datetime=create_date_time(
                            date=report_start, time="09:10:00"
                        ),
                        event_type=EventType.EHR_INTEGRATIONS.value,
                        payload=create_integration_payload(
                            outcome="FAILED_TO_INTEGRATE"
                        ),
                    )
                ),
                sourcetype="myevent",
            )

            # failed to integrate # 2

            index.submit(
                json.dumps(
                    create_sample_event(
                        "test_successfully_integrated_failed_to_integrate_#2",
                        registration_event_datetime=create_date_time(
                            date=report_start, time="09:00:00"
                        ),
                        event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                        sendingPracticeSupplierName="EMIS",
                        requestingPracticeSupplierName="TPP",
                        payload=create_transfer_compatibility_payload(
                            internalTransfer=False,
                            transferCompatible=True,
                            reason="test1",
                        ),
                    )
                ),
                sourcetype="myevent",
            )

            index.submit(
                json.dumps(
                    create_sample_event(
                        "test_successfully_integrated_failed_to_integrate_#2",
                        registration_event_datetime=create_date_time(
                            date=report_start, time="09:10:00"
                        ),
                        event_type=EventType.EHR_INTEGRATIONS.value,
                        payload=create_integration_payload(
                            outcome="FAILED_TO_INTEGRATE"
                        ),
                    )
                ),
                sourcetype="myevent",
            )

            # Act

            test_query = self.generate_splunk_query_from_report(
                "gp2gp_transfer_status_snapshot_report/gp2gp_transfer_status_report_snapshot_base"
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
                ".[] "
                + '| select( .total_eligible_for_electronic_transfer=="6" )'
                + '| select( .count_successfully_integrated == "3")'
                + '| select( .percentage_successfully_integrated == "50.00")',
                telemetry,
            )

        finally:
            self.delete_index(index_name)

    def test_rejected(self):
        # Arrange
        index_name, index = self.create_index()

        # reporting window
        report_start = datetime.today().date().replace(day=1)
        report_end = datetime.today().date().replace(day=28)
        cutoff = "0"

        try:
            # successfully integrated - #1

            index.submit(
                json.dumps(
                    create_sample_event(
                        "test_rejected_1",
                        registration_event_datetime=create_date_time(
                            date=report_start, time="09:00:00"
                        ),
                        event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                        sendingPracticeSupplierName="EMIS",
                        requestingPracticeSupplierName="TPP",
                        payload=create_transfer_compatibility_payload(
                            internalTransfer=False,
                            transferCompatible=True,
                            reason="test1",
                        ),
                    )
                ),
                sourcetype="myevent",
            )

            index.submit(
                json.dumps(
                    create_sample_event(
                        "test_rejected_1",
                        registration_event_datetime=create_date_time(
                            date=report_start, time="08:00:00"
                        ),
                        event_type=EventType.EHR_INTEGRATIONS.value,
                        payload=create_integration_payload(outcome="INTEGRATED"),
                    )
                ),
                sourcetype="myevent",
            )

            # successfully integrated - #2

            index.submit(
                json.dumps(
                    create_sample_event(
                        "test_rejected_2",
                        registration_event_datetime=create_date_time(
                            date=report_start, time="09:00:00"
                        ),
                        event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                        sendingPracticeSupplierName="EMIS",
                        requestingPracticeSupplierName="TPP",
                        payload=create_transfer_compatibility_payload(
                            internalTransfer=False,
                            transferCompatible=True,
                            reason="test1",
                        ),
                    )
                ),
                sourcetype="myevent",
            )

            index.submit(
                json.dumps(
                    create_sample_event(
                        "test_rejected_2",
                        registration_event_datetime=create_date_time(
                            date=report_start, time="08:10:00"
                        ),
                        event_type=EventType.EHR_INTEGRATIONS.value,
                        payload=create_integration_payload(
                            outcome="INTEGRATED_AND_SUPPRESSED"
                        ),
                    )
                ),
                sourcetype="myevent",
            )

            # successfully integrated - #3

            index.submit(
                json.dumps(
                    create_sample_event(
                        "test_rejected_3",
                        registration_event_datetime=create_date_time(
                            date=report_start, time="09:00:00"
                        ),
                        event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                        sendingPracticeSupplierName="EMIS",
                        requestingPracticeSupplierName="TPP",
                        payload=create_transfer_compatibility_payload(
                            internalTransfer=False,
                            transferCompatible=True,
                            reason="test1",
                        ),
                    )
                ),
                sourcetype="myevent",
            )

            index.submit(
                json.dumps(
                    create_sample_event(
                        "test_rejected_3",
                        registration_event_datetime=create_date_time(
                            date=report_start, time="08:20:00"
                        ),
                        event_type=EventType.EHR_INTEGRATIONS.value,
                        payload=create_integration_payload(
                            outcome="SUPPRESSED_AND_REACTIVATED"
                        ),
                    )
                ),
                sourcetype="myevent",
            )

            # rejected

            index.submit(
                json.dumps(
                    create_sample_event(
                        "test_rejected_4",
                        registration_event_datetime=create_date_time(
                            date=report_start, time="09:00:00"
                        ),
                        event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                        sendingPracticeSupplierName="EMIS",
                        requestingPracticeSupplierName="TPP",
                        payload=create_transfer_compatibility_payload(
                            internalTransfer=False,
                            transferCompatible=True,
                            reason="test1",
                        ),
                    )
                ),
                sourcetype="myevent",
            )

            index.submit(
                json.dumps(
                    create_sample_event(
                        "test_rejected_4",
                        registration_event_datetime=create_date_time(
                            date=report_start, time="09:00:00"
                        ),
                        event_type=EventType.EHR_INTEGRATIONS.value,
                        payload=create_integration_payload(outcome="REJECTED"),
                    )
                ),
                sourcetype="myevent",
            )

            # Act

            test_query = self.generate_splunk_query_from_report(
                "gp2gp_transfer_status_snapshot_report/gp2gp_transfer_status_report_snapshot_base"
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
                ".[] "
                + '| select( .total_eligible_for_electronic_transfer=="4" )'
                + '| select( .count_rejected == "1")'
                + '| select( .percentage_rejected == "25.00")',
                telemetry,
            )

        finally:
            self.delete_index(index_name)

    def test_awaiting_integration(self):
        # Arrange
        index_name, index = self.create_index()

        # reporting window
        report_start = datetime.today().date().replace(day=1)
        report_end = datetime.today().date().replace(day=28)
        cutoff = "0"

        try:
            # awaiting_integration - #1

            index.submit(
                json.dumps(
                    create_sample_event(
                        "awaiting_integration_1",
                        registration_event_datetime=create_date_time(
                            date=report_start, time="09:00:00"
                        ),
                        event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                        sendingPracticeSupplierName="EMIS",
                        requestingPracticeSupplierName="TPP",
                        payload=create_transfer_compatibility_payload(
                            internalTransfer=False,
                            transferCompatible=True,
                            reason="test1",
                        ),
                    )
                ),
                sourcetype="myevent",
            )

            index.submit(
                json.dumps(
                    create_sample_event(
                        "awaiting_integration_1",
                        registration_event_datetime=create_date_time(
                            date=report_start, time="09:10:00"
                        ),
                        event_type=EventType.READY_TO_INTEGRATE_STATUSES.value,
                    )
                ),
                sourcetype="myevent",
            )

            # awaiting_integration - #2

            index.submit(
                json.dumps(
                    create_sample_event(
                        "awaiting_integration_2",
                        registration_event_datetime=create_date_time(
                            date=report_start, time="09:20:00"
                        ),
                        event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                        sendingPracticeSupplierName="EMIS",
                        requestingPracticeSupplierName="TPP",
                        payload=create_transfer_compatibility_payload(
                            internalTransfer=False,
                            transferCompatible=True,
                            reason="test1",
                        ),
                    )
                ),
                sourcetype="myevent",
            )

            index.submit(
                json.dumps(
                    create_sample_event(
                        "awaiting_integration_2",
                        registration_event_datetime=create_date_time(
                            date=report_start, time="09:30:00"
                        ),
                        event_type=EventType.READY_TO_INTEGRATE_STATUSES.value,
                    )
                ),
                sourcetype="myevent",
            )

            # rejected

            index.submit(
                json.dumps(
                    create_sample_event(
                        "awaiting_integration_3",
                        registration_event_datetime=create_date_time(
                            date=report_start, time="09:00:00"
                        ),
                        event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                        sendingPracticeSupplierName="EMIS",
                        requestingPracticeSupplierName="TPP",
                        payload=create_transfer_compatibility_payload(
                            internalTransfer=False,
                            transferCompatible=True,
                            reason="test1",
                        ),
                    )
                ),
                sourcetype="myevent",
            )

            index.submit(
                json.dumps(
                    create_sample_event(
                        "awaiting_integration_3",
                        registration_event_datetime=create_date_time(
                            date=report_start, time="09:00:00"
                        ),
                        event_type=EventType.EHR_INTEGRATIONS.value,
                        payload=create_integration_payload(outcome="REJECTED"),
                    )
                ),
                sourcetype="myevent",
            )

            # Act

            test_query = self.generate_splunk_query_from_report(
                "gp2gp_transfer_status_snapshot_report/gp2gp_transfer_status_report_snapshot_base"
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
                ".[] "
                + '| select( .total_eligible_for_electronic_transfer=="3" )'
                + '| select( .count_awaiting_integration == "2")'
                + '| select( .percentage_awaiting_integration == "66.67")'
                + '| select( .percentage_rejected == "33.33")',
                telemetry,
            )

        finally:
            self.delete_index(index_name)

    def test_in_progress(self):
        # Arrange

        index_name, index = self.create_index()

        # reporting window
        report_start = generate_report_start_date()
        report_end = generate_report_end_date()
        cutoff = "0"

        try:
            # test_#1 - status EHR_SENT
            conversation_id_1 = "test_in_progress_EHR_SENT"

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversation_id_1,
                        registration_event_datetime=create_date_time(
                            report_start, "05:00:00"
                        ),
                        event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                        sendingPracticeSupplierName="EMIS",
                        requestingPracticeSupplierName="TPP",
                        payload=create_transfer_compatibility_payload(
                            internalTransfer=False,
                            transferCompatible=True,
                            reason="test1",
                        ),
                    )
                ),
                sourcetype="myevent",
            )

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversation_id_1,
                        registration_event_datetime=create_date_time(
                            report_start, "06:00:00"
                        ),
                        event_type=EventType.EHR_REQUESTS.value,
                    )
                ),
                sourcetype="myevent",
            )

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversation_id_1,
                        registration_event_datetime=create_date_time(
                            report_start, "07:00:00"
                        ),
                        event_type=EventType.EHR_RESPONSES.value,
                    )
                ),
                sourcetype="myevent",
            )

            # test_#2 - status EHR_REQUESTED
            conversation_id_2 = "test_in_progress_EHR_REQUESTED"

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversation_id_2,
                        registration_event_datetime=create_date_time(report_start,"05:00:00"),
                        event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                        sendingPracticeSupplierName="EMIS",
                        requestingPracticeSupplierName="TPP",
                        payload=create_transfer_compatibility_payload(
                            internalTransfer=False,
                            transferCompatible=True,
                            reason="test1",
                        ),
                    )
                ),
                sourcetype="myevent",
            )

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversation_id_2,
                        registration_event_datetime=create_date_time(report_start,"06:00:00"),
                        event_type=EventType.EHR_REQUESTS.value,
                    )
                ),
                sourcetype="myevent",
            )

            # test_#3 - status ELIGIBLE_FOR_TRANSFER

            conversation_id_3 = "test_in_progress_ELIGIBLE_FOR_TRANSFER"

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversation_id_3,
                        registration_event_datetime=create_date_time(report_start,"05:00:00"),
                        event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                        sendingPracticeSupplierName="EMIS",
                        requestingPracticeSupplierName="TPP",
                        payload=create_transfer_compatibility_payload(
                            internalTransfer=False,
                            transferCompatible=True,
                            reason="test1",
                        ),
                    )
                ),
                sourcetype="myevent",
            )

            # Act

            test_query = self.generate_splunk_query_from_report(
                "gp2gp_transfer_status_snapshot_report/gp2gp_transfer_status_report_snapshot_base"
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
                ".[] "
                + '| select( .total_eligible_for_electronic_transfer=="3" )'
                + '| select( .count_in_progress == "3")'
                + '| select( .percentage_in_progress == "100.00")',
                telemetry,
            )

        finally:
            self.delete_index(index_name)

    def test_transfer_status_report_technical_failure(self):
        # Arrange

        index_name, index = self.create_index()

        # reporting window
        report_start = datetime_utc_now().date().replace(day=1)
        report_end = datetime_utc_now().date().replace(day=28)
        cutoff = "0"

        try:
            conversationId = "test_technical_failure_failed_to_integrate"

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversationId,
                        registration_event_datetime=create_date_time(
                            date=report_start, time="08:00:00"
                        ),
                        event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                        sendingPracticeSupplierName="EMIS",
                        requestingPracticeSupplierName="TPP",
                        payload=create_transfer_compatibility_payload(
                            internalTransfer=False, transferCompatible=True
                        ),
                    )
                ),
                sourcetype="myevent",
            )

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversationId,
                        registration_event_datetime=create_date_time(
                            date=report_start, time="08:10:00"
                        ),
                        event_type=EventType.EHR_INTEGRATIONS.value,
                        payload=create_integration_payload(
                            outcome="FAILED_TO_INTEGRATE"
                        ),
                    )
                ),
                sourcetype="myevent",
            )

            # Act

            test_query = self.generate_splunk_query_from_report(
                "gp2gp_transfer_status_snapshot_report/gp2gp_transfer_status_report_snapshot_base"
            )
            test_query = set_variables_on_query(
                test_query,
                {
                    "$index$": index_name,
                    "$start_time$": report_start.strftime("%Y-%m-%dT%H:%M:%S"),
                    "$end_time$": report_end.strftime("%Y-%m-%dT%H:%M:%S"),
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
                ".[] "
                + '| select( .total_eligible_for_electronic_transfer=="1" )'
                + '| select( .count_technical_failure == "1")'
                + '| select( .percentage_technical_failure == "100.00")',
                telemetry,
            )

        finally:
            self.delete_index(index_name)

    @pytest.mark.parametrize(
        "cutoff, registrationStatus",
        [
            (1, "REGISTRATION"),
            (7, "EHR_REQUESTED"),
            (11, "EHR_SENT"),
            (19, "READY_TO_INTEGRATE"),
        ],
    )
    def test_cutoffs(self, cutoff, registrationStatus):
        """This test ensures that new conversations are at a different stage based on cutoff."""

        self.LOG.info(f"cutoff:{cutoff}, regstat:{registrationStatus}")

        # Arrange
        index_name, index = self.create_index()

        report_start = datetime.today().date().replace(day=1)
        report_end = datetime.today().date().replace(day=2)

        try:
            conversationId = "test_cutoffs"

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversationId,
                        registration_event_datetime=create_date_time(
                            date=report_start.replace(day=1), time="08:00:00"
                        ),
                        event_type=EventType.REGISTRATIONS.value,
                        payload=create_registration_payload(),
                    )
                ),
                sourcetype="myevent",
            )

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversationId,
                        registration_event_datetime=create_date_time(
                            date=report_start.replace(day=8), time="05:03:00"
                        ),
                        event_type=EventType.EHR_REQUESTS.value,
                    )
                ),
                sourcetype="myevent",
            )

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversationId,
                        registration_event_datetime=create_date_time(
                            date=report_start.replace(day=12), time="05:00:00"
                        ),
                        event_type=EventType.EHR_RESPONSES.value,
                        payload=create_ehr_response_payload(number_of_placeholders=2),
                    )
                ),
                sourcetype="myevent",
            )

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversationId,
                        registration_event_datetime=create_date_time(
                            date=report_start.replace(day=20), time="03:00:00"
                        ),
                        event_type=EventType.READY_TO_INTEGRATE_STATUSES.value,
                    )
                ),
                sourcetype="myevent",
            )

            # Act
            test_query = self.generate_splunk_query_from_report(
                "gp2gp_transfer_status_snapshot_report/gp2gp_transfer_status_report_snapshot_base"
            )

            test_query = set_variables_on_query(
                test_query,
                {
                    "$index$": index_name,
                    "$start_time$": report_start.strftime("%Y-%m-%dT%H:%m:%s"),
                    "$end_time$": report_end.strftime("%Y-%m-%dT%H:%m:%s"),
                    "$cutoff$": str(cutoff),
                },
            )

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service
            )
            self.LOG.info(f"telemetry: {telemetry}")

            # Assert

            assert jq.first(
                f'.[] | select( .registrationStatus=="{registrationStatus}")', telemetry
            )

        finally:
            self.delete_index(index_name)
