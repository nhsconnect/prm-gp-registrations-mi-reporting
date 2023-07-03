import os
import json
import pytest
from time import sleep
from splunklib import client
import jq
from helpers.splunk \
    import get_telemetry_from_splunk,  create_sample_event, set_variables_on_query, \
    create_integration_payload, create_transfer_compatibility_payload
from tests.test_base import TestBase, EventType
from datetime import datetime, timedelta


class TestTransferStatusReportSnapshotOutputs(TestBase):

    def test_gp2gp_transfer_status_report_snapshot_counts(self):
        '''This test just tests the "counts output" is calling the base query correctly.'''

        # Arrange
        index_name, index = self.create_index()

        try:

            index.submit(
                json.dumps(
                    create_sample_event(
                        'test_total_eligible_for_electronic_transfer_1',
                        registration_event_datetime="2023-03-10T08:00:00+0000",
                        event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                        sendingPracticeSupplierName="EMIS",
                        requestingPracticeSupplierName="TPP",
                        payload=create_transfer_compatibility_payload(
                            internalTransfer=False,
                            transferCompatible=True,
                            reason="test1"
                        )

                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        'test_total_eligible_for_electronic_transfer_2',
                        registration_event_datetime="2023-03-10T09:00:00+0000",
                        event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                        sendingPracticeSupplierName="EMIS",
                        requestingPracticeSupplierName="TPP",
                        payload=create_transfer_compatibility_payload(
                            internalTransfer=False,
                            transferCompatible=True,
                            reason="test2"
                        )

                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        'test_total_eligible_for_electronic_transfer_3',
                        registration_event_datetime="2023-03-10T10:00:00+0000",
                        event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                        sendingPracticeSupplierName="EMIS",
                        requestingPracticeSupplierName="TPP",
                        payload=create_transfer_compatibility_payload(
                            internalTransfer=True,
                            transferCompatible=True,
                            reason="test1"
                        )

                    )),
                sourcetype="myevent")

            # Act
            test_query = self.generate_splunk_query_from_report(
                'gp2gp_transfer_status_snapshot_report/gp2gp_transfer_status_report_snapshot_counts')

            test_query = set_variables_on_query(test_query, {
                "$index$": index_name,
                "$report_start$": "2023-03-01",
                "$report_end$": "2023-03-31"
            })

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service)
            self.LOG.info(f'telemetry: {telemetry}')

            # Assert
            expected_values = {"Successfully Integrated": "0",
                               "Rejected": "0",
                               "Awaiting Integration": "0", 
                               "In-Progress": "0", 
                               "Technical Failure": "2"}

            for idx, (key, value) in enumerate(expected_values.items()):
                assert jq.first(
                    f'.[{idx}] | select( .label=="{key}") | select (.count=="{value}")', telemetry)

        finally:
            self.delete_index(index_name)

    def test_gp2gp_transfer_status_report_snapshot_percentages(self):
        '''This test just tests the "percentages output" is calling the base query correctly.'''

        # Arrange
        index_name, index = self.create_index()

        try:

            index.submit(
                json.dumps(
                    create_sample_event(
                        'test_total_eligible_for_electronic_transfer_1',
                        registration_event_datetime="2023-03-10T08:00:00+0000",
                        event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                        sendingPracticeSupplierName="EMIS",
                        requestingPracticeSupplierName="TPP",
                        payload=create_transfer_compatibility_payload(
                            internalTransfer=False,
                            transferCompatible=True,
                            reason="test1"
                        )

                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        'test_total_eligible_for_electronic_transfer_2',
                        registration_event_datetime="2023-03-10T09:00:00+0000",
                        event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                        sendingPracticeSupplierName="EMIS",
                        requestingPracticeSupplierName="TPP",
                        payload=create_transfer_compatibility_payload(
                            internalTransfer=False,
                            transferCompatible=True,
                            reason="test2"
                        )

                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        'test_total_eligible_for_electronic_transfer_3',
                        registration_event_datetime="2023-03-10T10:00:00+0000",
                        event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                        sendingPracticeSupplierName="EMIS",
                        requestingPracticeSupplierName="TPP",
                        payload=create_transfer_compatibility_payload(
                            internalTransfer=True,
                            transferCompatible=True,
                            reason="test1"
                        )

                    )),
                sourcetype="myevent")

            # Act
            test_query = self.generate_splunk_query_from_report(
                'gp2gp_transfer_status_snapshot_report/gp2gp_transfer_status_report_snapshot_percentages')

            test_query = set_variables_on_query(test_query, {
                "$index$": index_name,
                "$report_start$": "2023-03-01",
                "$report_end$": "2023-03-31"
            })

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service)
            self.LOG.info(f'telemetry: {telemetry}')

            # Assert
            expected_values = {"Successfully Integrated": "0.00",
                               "Rejected": "0.00",
                               "Awaiting Integration": "0.00", 
                               "In-Progress": "0.00", 
                               "Technical Failure": "100.00"}

            for idx, (key, value) in enumerate(expected_values.items()):
                assert jq.first(
                    f'.[{idx}] | select( .label=="{key}") | select (.count=="{value}")', telemetry)

        finally:
            self.delete_index(index_name)

    def test_gp2gp_transfer_status_report_snapshot_total_eligible_for_transfer(self):

            # Arrange
            index_name, index = self.create_index()

            try:

                index.submit(
                    json.dumps(
                        create_sample_event(
                            'test_total_eligible_for_electronic_transfer_1',
                            registration_event_datetime="2023-03-10T08:00:00+0000",
                            event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                            sendingPracticeSupplierName="EMIS",
                            requestingPracticeSupplierName="TPP",
                            payload=create_transfer_compatibility_payload(
                                internalTransfer=False,
                                transferCompatible=True,
                                reason="test1"
                            )

                        )),
                    sourcetype="myevent")

                index.submit(
                    json.dumps(
                        create_sample_event(
                            'test_total_eligible_for_electronic_transfer_2',
                            registration_event_datetime="2023-03-10T09:00:00+0000",
                            event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                            sendingPracticeSupplierName="EMIS",
                            requestingPracticeSupplierName="TPP",
                            payload=create_transfer_compatibility_payload(
                                internalTransfer=False,
                                transferCompatible=True,
                                reason="test2"
                            )

                        )),
                    sourcetype="myevent")

                index.submit(
                    json.dumps(
                        create_sample_event(
                            'test_total_eligible_for_electronic_transfer_3',
                            registration_event_datetime="2023-03-10T10:00:00+0000",
                            event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                            sendingPracticeSupplierName="EMIS",
                            requestingPracticeSupplierName="TPP",
                            payload=create_transfer_compatibility_payload(
                                internalTransfer=True,
                                transferCompatible=True,
                                reason="test1"
                            )

                        )),
                    sourcetype="myevent")

                # Act
                test_query = self.generate_splunk_query_from_report(
                    'gp2gp_transfer_status_snapshot_report/gp2gp_transfer_status_report_snapshot_total_eligible_for_transfer')

                test_query = set_variables_on_query(test_query, {
                    "$index$": index_name,
                    "$report_start$": "2023-03-01",
                    "$report_end$": "2023-03-31"
                })

                sleep(2)

                telemetry = get_telemetry_from_splunk(
                    self.savedsearch(test_query), self.splunk_service)
                self.LOG.info(f'telemetry: {telemetry}')


                # Assert                
                assert jq.first(
                    f'.[] | select( .total_eligible_for_electronic_transfer=="2")', telemetry)

            finally:
                self.delete_index(index_name)
