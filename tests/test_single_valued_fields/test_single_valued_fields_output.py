import logging
import os
from enum import Enum
import pytest
import json
from time import sleep
from splunklib import client
import jq

from helpers.datetime_helper import datetime_utc_now, create_date_time
from helpers.splunk \
    import get_telemetry_from_splunk, get_or_create_index, create_sample_event, set_variables_on_query, \
    create_integration_payload, create_error_payload, create_transfer_compatibility_payload
from datetime import datetime, timedelta
from jinja2 import Environment, FileSystemLoader
from tests.test_base import TestBase, EventType


class TestSingleValuedFieldOutputs(TestBase):

    def test_gp2gp_single_valued_field_total_number_of_registrations(self):

        # Arrange
        index_name, index = self.create_index()

        # reporting window
        report_start = datetime.today().date().replace(day=1)
        report_end = datetime.today().date().replace(day=2)
        cutoff = "0"

        try:

            index.submit(
                json.dumps(
                    create_sample_event(
                        'test_tot_num_reg_1',
                        registration_event_datetime=create_date_time(report_start, "08:00:00"),
                        event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                        sendingSupplierName="EMIS",
                        requestingSupplierName="TPP",
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
                        'test_tot_num_reg_2',
                        registration_event_datetime=create_date_time(report_start, "09:00:00"),
                        event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                        sendingSupplierName="EMIS",
                        requestingSupplierName="TPP",
                        payload=create_transfer_compatibility_payload(
                            internalTransfer=True,
                            transferCompatible=True,
                            reason="test2"
                        )

                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        'test_tot_num_reg_3',
                        registration_event_datetime=create_date_time(report_start, "10:00:00"),
                        event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                        sendingSupplierName="EMIS",
                        requestingSupplierName="TPP",
                        payload=create_transfer_compatibility_payload(
                            internalTransfer=False,
                            transferCompatible=True,
                            reason="test1"
                        )

                    )),
                sourcetype="myevent")

            # Act
            test_query = self.generate_splunk_query_from_report(
                'gp2gp_single_valued_fields/'
                'gp2gp_total_registration_count')

            test_query = set_variables_on_query(test_query, {
                "$index$": index_name,
                "$start_time$": report_start.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "$end_time$": report_end.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "$cutoff$": cutoff
            })

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service)
            self.LOG.info(f'telemetry: {telemetry}')

            # Assert
            assert jq.first(
                f'.[] | select( .total_number_of_registrations=="2")', telemetry)

        finally:
            self.delete_index(index_name)

    def test_gp2gp_single_valued_field_total_number_of_eligible_transfers(self):

        # Arrange
        index_name, index = self.create_index()

        # reporting window
        report_start = datetime.today().date().replace(day=1)
        report_end = datetime.today().date().replace(day=2)
        cutoff = "0"

        try:

            index.submit(
                json.dumps(
                    create_sample_event(
                        'test_tot_num_reg_1',
                        registration_event_datetime=create_date_time(report_start, "08:00:00"),
                        event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                        sendingSupplierName="EMIS",
                        requestingSupplierName="TPP",
                        payload=create_transfer_compatibility_payload(
                            internalTransfer=False,
                            transferCompatible=False,
                            reason="test1"
                        )

                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        'test_tot_num_reg_2',
                        registration_event_datetime=create_date_time(report_start, "08:00:00"),
                        event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                        sendingSupplierName="EMIS",
                        requestingSupplierName="TPP",
                        payload=create_transfer_compatibility_payload(
                            internalTransfer=False,
                            transferCompatible=False,
                            reason="test1"
                        )

                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        'test_tot_num_reg_3',
                        registration_event_datetime=create_date_time(report_start, "10:00:00"),
                        event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                        sendingSupplierName="EMIS",
                        requestingSupplierName="TPP",
                        payload=create_transfer_compatibility_payload(
                            internalTransfer=False,
                            transferCompatible=True,
                            reason="test1"
                        )

                    )),
                sourcetype="myevent")

            # Act
            test_query = self.generate_splunk_query_from_report(
                'gp2gp_single_valued_fields/'
                'gp2gp_total_eligible_transfers_count')

            test_query = set_variables_on_query(test_query, {
                "$index$": index_name,
                "$start_time$": report_start.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "$end_time$": report_end.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "$cutoff$": cutoff
            })

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service)
            self.LOG.info(f'telemetry: {telemetry}')

            # Assert
            assert jq.first(
                f'.[] | select( .total_number_of_eligible_transfers=="1")', telemetry)

        finally:
            self.delete_index(index_name)

    def test_gp2gp_single_valued_field_total_records_transferred(self):

        index_name, index = self.create_index()

        # reporting window
        report_start = datetime.today().date().replace(day=1)
        report_end = datetime.today().date().replace(day=28)
        cutoff = "0"

        try:
            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_total_transfers_#1',
                        registration_event_datetime=create_date_time(date=report_start, time="09:00:00"),
                        event_type=EventType.EHR_INTEGRATIONS.value,
                        payload=create_integration_payload(outcome="INTEGRATED")
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_total_transfers_#2',
                        registration_event_datetime=create_date_time(date=report_start, time="10:00:00"),
                        event_type=EventType.READY_TO_INTEGRATE_STATUSES.value
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_total_transfers_#3',
                        registration_event_datetime=create_date_time(date=report_start, time="11:00:00"),
                        event_type=EventType.ERRORS.value,
                        payload=create_error_payload(
                            errorCode="99",
                            errorDescription="Error with EHR Response",
                            failurePoint=EventType.EHR_RESPONSES.value
                        )

                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_total_transfers_#4',
                        registration_event_datetime=create_date_time(date=report_start, time="12:00:00"),
                        event_type=EventType.EHR_REQUESTS.value
                    )),
                sourcetype="myevent")

            # Act
            test_query = self.generate_splunk_query_from_report(
                'gp2gp_single_valued_fields/'
                'gp2gp_total_records_transferred')

            test_query = set_variables_on_query(test_query, {
                "$index$": index_name,
                "$start_time$": report_start.strftime("%Y-%m-%dT%H:%m:%s"),
                "$end_time$": report_end.strftime("%Y-%m-%dT%H:%m:%s"),
                "$cutoff$": cutoff
            })

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service)
            self.LOG.info(f'telemetry: {telemetry}')

            # Assert
            expected_values = {"total_records_transferred": "2"}

            for idx, (key, value) in enumerate(expected_values.items()):
                self.LOG.info(f'.[{idx}] | select( .label=="{key}") | select (.count=="{value}")')
                assert jq.first(
                    f'.[{idx}] | select( .{key}=="{value}")', telemetry)

        finally:
            self.delete_index(index_name)

    def test_gp2gp_single_valued_field_total_awaiting_integration(self):
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
                        conversation_id='test_awaiting_integration_#1',
                        registration_event_datetime=create_date_time(date=report_start, time="09:00:00"),
                        event_type=EventType.EHR_INTEGRATIONS.value,
                        payload=create_integration_payload(outcome="INTEGRATED")
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_awaiting_integration_#2',
                        registration_event_datetime=create_date_time(date=report_start, time="10:00:00"),
                        event_type=EventType.EHR_REQUESTS.value
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_awaiting_integration_#3',
                        registration_event_datetime=create_date_time(date=report_start, time="11:00:00"),
                        event_type=EventType.READY_TO_INTEGRATE_STATUSES.value
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_awaiting_integration_#4',
                        registration_event_datetime=create_date_time(date=report_start, time="12:00:00"),
                        event_type=EventType.ERRORS.value,
                        payload=create_error_payload(
                            errorCode="99",
                            errorDescription="Error with EHR Response",
                            failurePoint=EventType.EHR_RESPONSES.value
                        )

                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_awaiting_integration_#5',
                        registration_event_datetime=create_date_time(date=report_start, time="12:00:00"),
                        event_type=EventType.EHR_RESPONSES.value
                    )),
                sourcetype="myevent")

            # Act
            test_query = self.generate_splunk_query_from_report(
                'gp2gp_single_valued_fields/'
                'gp2gp_total_awaiting_integration_count')

            test_query = set_variables_on_query(test_query, {
                "$index$": index_name,
                "$start_time$": report_start.strftime("%Y-%m-%dT%H:%m:%s"),
                "$end_time$": report_end.strftime("%Y-%m-%dT%H:%m:%s"),
                "$cutoff$": cutoff
            })

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service)
            self.LOG.info(f'telemetry: {telemetry}')

            # Assert
            expected_values = {"total_awaiting_integration": "1"}

            for idx, (key, value) in enumerate(expected_values.items()):
                self.LOG.info(f'.[{idx}] | select( .label=="{key}") | select (.count=="{value}")')
                assert jq.first(
                    f'.[{idx}] | select( .{key}=="{value}")', telemetry)

        finally:
            self.delete_index(index_name)

    def test_gp2gp_single_valued_field_total_successful_integration(self):
        # Arrange
        index_name, index = self.create_index()

        # reporting window
        report_start = datetime.today().date().replace(day=1)
        report_end = datetime.today().date().replace(day=28)
        cutoff = "0"

        try:
            different_outcomes_list = [
                "INTEGRATED",
                "INTEGRATED_AND_SUPPRESSED",
                "SUPPRESSED_AND_REACTIVATED",
                "FILED_AS_ATTACHMENT",
                "INTERNAL_TRANSFER",
                "REJECTED",
                "FAILED_TO_INTEGRATE"
            ]

            for outcome in different_outcomes_list:
                index.submit(
                    json.dumps(
                        create_sample_event(
                            f'ehr_integrations_{outcome}',
                            registration_event_datetime=create_date_time(report_start, "08:00:00"),
                            event_type=EventType.EHR_INTEGRATIONS.value,
                            sendingSupplierName="EMIS",
                            requestingSupplierName="TPP",
                            payload=create_integration_payload(
                                outcome=outcome
                            )

                        )),
                    sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_awaiting_integration',
                        registration_event_datetime=create_date_time(date=report_start, time="11:00:00"),
                        event_type=EventType.READY_TO_INTEGRATE_STATUSES.value
                    )),
                sourcetype="myevent")

            # Act
            test_query = self.generate_splunk_query_from_report(
                'gp2gp_single_valued_fields/'
                'gp2gp_total_successful_integration_count')

            test_query = set_variables_on_query(test_query, {
                "$index$": index_name,
                "$start_time$": report_start.strftime("%Y-%m-%dT%H:%m:%s"),
                "$end_time$": report_end.strftime("%Y-%m-%dT%H:%m:%s"),
                "$cutoff$": cutoff
            })

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service)
            self.LOG.info(f'telemetry: {telemetry}')

            # Assert
            expected_values = {"total_successful_integration": "5"}

            for idx, (key, value) in enumerate(expected_values.items()):
                self.LOG.info(f'.[{idx}] | select( .label=="{key}") | select (.count=="{value}")')
                assert jq.first(
                    f'.[{idx}] | select( .{key}=="{value}")', telemetry)

        finally:
            self.delete_index(index_name)

    def test_gp2gp_single_valued_field_total_technical_failures(self):
        index_name, index = self.create_index()

        # reporting window
        report_start = datetime.today().date().replace(day=1)
        report_end = datetime.today().date().replace(day=28)
        cutoff = "0"

        try:
            # Arrange

            # technical_failure
            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_total_records_transferred_#1',
                        registration_event_datetime=create_date_time(date=report_start, time="09:00:00"),
                        event_type=EventType.EHR_INTEGRATIONS.value,
                        payload=create_integration_payload(outcome="FAILED_TO_INTEGRATE")
                    )),
                sourcetype="myevent")

            # awaiting_integration
            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_total_records_transferred_#2',
                        registration_event_datetime=create_date_time(date=report_start, time="10:00:00"),
                        event_type=EventType.READY_TO_INTEGRATE_STATUSES.value
                    )),
                sourcetype="myevent")

            # technical_failure
            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_total_records_transferred_#3',
                        registration_event_datetime=create_date_time(date=report_start, time="11:00:00"),
                        event_type=EventType.EHR_REQUESTS.value
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_total_records_transferred_#3',
                        registration_event_datetime=create_date_time(date=report_start, time="11:01:00"),
                        event_type=EventType.ERRORS.value,
                        payload=create_error_payload(
                            errorCode="99",
                            errorDescription="Error",
                            failurePoint=EventType.EHR_REQUESTS.value
                        )

                    )),
                sourcetype="myevent")

            # in_progress
            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_total_records_transferred_#4',
                        registration_event_datetime=create_date_time(date=report_start, time="11:10:00"),
                        event_type=EventType.EHR_REQUESTS.value
                    )),
                sourcetype="myevent")

            # technical_failure
            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_total_records_transferred_#5',
                        registration_event_datetime=create_date_time(date=report_start, time="11:00:00"),
                        event_type=EventType.EHR_RESPONSES.value
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_total_records_transferred_#5',
                        registration_event_datetime=create_date_time(date=report_start, time="11:01:00"),
                        event_type=EventType.ERRORS.value,
                        payload=create_error_payload(
                            errorCode="99",
                            errorDescription="Error",
                            failurePoint=EventType.EHR_RESPONSES.value
                        )

                    )),
                sourcetype="myevent")

            # in_progress
            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_total_records_transferred_#6',
                        registration_event_datetime=create_date_time(date=report_start, time="11:10:00"),
                        event_type=EventType.EHR_RESPONSES.value
                    )),
                sourcetype="myevent")

            # technical_failure
            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_total_records_transferred_#7',
                        registration_event_datetime=create_date_time(date=report_start, time="11:00:00"),
                        event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                        payload=create_transfer_compatibility_payload(
                            internalTransfer=False,
                            transferCompatible=True
                        )
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_total_records_transferred_#7',
                        registration_event_datetime=create_date_time(date=report_start, time="11:01:00"),
                        event_type=EventType.ERRORS.value,
                        payload=create_error_payload(
                            errorCode="99",
                            errorDescription="Error",
                            failurePoint=EventType.EHR_RESPONSES.value
                        )

                    )),
                sourcetype="myevent")

            # in_progress
            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id='test_total_records_transferred_#8',
                        registration_event_datetime=create_date_time(date=report_start, time="11:10:00"),
                        event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                        payload=create_transfer_compatibility_payload(
                            internalTransfer=False,
                            transferCompatible=True
                        )
                    )),
                sourcetype="myevent")

            # Act
            test_query = self.generate_splunk_query_from_report(
                'gp2gp_single_valued_fields/'
                'gp2gp_total_technical_failures')

            test_query = set_variables_on_query(test_query, {
                "$index$": index_name,
                "$start_time$": report_start.strftime("%Y-%m-%dT%H:%m:%s"),
                "$end_time$": report_end.strftime("%Y-%m-%dT%H:%m:%s"),
                "$cutoff$": cutoff
            })

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service)
            self.LOG.info(f'telemetry: {telemetry}')

            # Assert
            expected_values = {"total_number_of_technical_failures": "4"}

            for idx, (key, value) in enumerate(expected_values.items()):
                self.LOG.info(f'.[{idx}] | select( .label=="{key}") | select (.count=="{value}")')
                assert jq.first(
                    f'.[{idx}] | select( .{key}=="{value}")', telemetry)

        finally:
            self.delete_index(index_name)
