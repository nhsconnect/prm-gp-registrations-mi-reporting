import os
import json
import pytest
from time import sleep
from splunklib import client
import jq
from helpers.splunk \
    import create_ehr_response_payload, create_registration_payload, get_telemetry_from_splunk,  create_sample_event, set_variables_on_query, \
    create_integration_payload, create_transfer_compatibility_payload
from tests.test_base import TestBase, EventType
from datetime import timedelta, datetime
from helpers.datetime_helper import datetime_utc_now, create_date_time


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
                        'test_total_eligible_for_electronic_transfer_1',
                        registration_event_datetime=create_date_time(
                            date=report_start, time="08:00:00"),
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
                        registration_event_datetime=create_date_time(
                            date=report_start, time="09:00:00"),
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
                        registration_event_datetime=create_date_time(
                            date=report_start, time="10:00:00"),
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
                'gp2gp_transfer_status_snapshot_report/gp2gp_transfer_status_report_snapshot_base')
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
                '.[] | select( .total_eligible_for_electronic_transfer == "2" ) ', telemetry)

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
                        'test_successfully_integrated_1',
                        registration_event_datetime=create_date_time(
                            date=report_start, time="09:00:00"),
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
                        'test_successfully_integrated_1',
                        registration_event_datetime=create_date_time(
                            date=report_start, time="08:00:00"),
                        event_type=EventType.EHR_INTEGRATIONS.value,
                        payload=create_integration_payload(
                            outcome="INTEGRATED")
                    )),
                sourcetype="myevent")

            # successfully integrated - #2

            index.submit(
                json.dumps(
                    create_sample_event(
                        'test_successfully_integrated_2',
                        registration_event_datetime=create_date_time(
                            date=report_start, time="09:00:00"),
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
                        'test_successfully_integrated_2',
                        registration_event_datetime=create_date_time(
                            date=report_start, time="08:10:00"),
                        event_type=EventType.EHR_INTEGRATIONS.value,
                        payload=create_integration_payload(
                            outcome="INTEGRATED_AND_SUPPRESSED")
                    )),
                sourcetype="myevent")

            # successfully integrated - #3

            index.submit(
                json.dumps(
                    create_sample_event(
                        'test_successfully_integrated_3',
                        registration_event_datetime=create_date_time(
                            date=report_start, time="09:00:00"),
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
                        'test_successfully_integrated_3',
                        registration_event_datetime=create_date_time(
                            date=report_start, time="08:20:00"),
                        event_type=EventType.EHR_INTEGRATIONS.value,
                        payload=create_integration_payload(
                            outcome="SUPPRESSED_AND_REACTIVATED")
                    )),
                sourcetype="myevent")

            # rejected

            index.submit(
                json.dumps(
                    create_sample_event(
                        'test_successfully_integrated_rejected',
                        registration_event_datetime=create_date_time(
                            date=report_start, time="09:00:00"),
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
                        'test_successfully_integrated_rejected',
                        registration_event_datetime=create_date_time(
                            date=report_start, time="09:00:00"),
                        event_type=EventType.EHR_INTEGRATIONS.value,
                        payload=create_integration_payload(outcome="REJECTED")
                    )),
                sourcetype="myevent")

            # failed to integrate # 1

            index.submit(
                json.dumps(
                    create_sample_event(
                        'test_successfully_integrated_failed_to_integrate_#1',
                        registration_event_datetime=create_date_time(
                            date=report_start, time="09:00:00"),
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
                        'test_successfully_integrated_failed_to_integrate_#1',
                        registration_event_datetime=create_date_time(
                            date=report_start, time="09:10:00"),
                        event_type=EventType.EHR_INTEGRATIONS.value,
                        payload=create_integration_payload(
                            outcome="FAILED_TO_INTEGRATE")
                    )),
                sourcetype="myevent")

            # failed to integrate # 2

            index.submit(
                json.dumps(
                    create_sample_event(
                        'test_successfully_integrated_failed_to_integrate_#2',
                        registration_event_datetime=create_date_time(
                            date=report_start, time="09:00:00"),
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
                        'test_successfully_integrated_failed_to_integrate_#2',
                        registration_event_datetime=create_date_time(
                            date=report_start, time="09:10:00"),
                        event_type=EventType.EHR_INTEGRATIONS.value,
                        payload=create_integration_payload(
                            outcome="FAILED_TO_INTEGRATE")
                    )),
                sourcetype="myevent")

            # Act

            test_query = self.generate_splunk_query_from_report(
                'gp2gp_transfer_status_snapshot_report/gp2gp_transfer_status_report_snapshot_base')
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
                '.[] ' +
                '| select( .total_eligible_for_electronic_transfer=="6" )' +
                '| select( .count_successfully_integrated == "3")' +
                '| select( .percentage_successfully_integrated == "50.00")', telemetry)

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
                        'test_rejected_1',
                        registration_event_datetime=create_date_time(
                            date=report_start, time="09:00:00"),
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
                        'test_rejected_1',
                        registration_event_datetime=create_date_time(
                            date=report_start, time="08:00:00"),
                        event_type=EventType.EHR_INTEGRATIONS.value,
                        payload=create_integration_payload(
                            outcome="INTEGRATED")
                    )),
                sourcetype="myevent")

            # successfully integrated - #2

            index.submit(
                json.dumps(
                    create_sample_event(
                        'test_rejected_2',
                        registration_event_datetime=create_date_time(
                            date=report_start, time="09:00:00"),
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
                        'test_rejected_2',
                        registration_event_datetime=create_date_time(
                            date=report_start, time="08:10:00"),
                        event_type=EventType.EHR_INTEGRATIONS.value,
                        payload=create_integration_payload(
                            outcome="INTEGRATED_AND_SUPPRESSED")
                    )),
                sourcetype="myevent")

            # successfully integrated - #3

            index.submit(
                json.dumps(
                    create_sample_event(
                        'test_rejected_3',
                        registration_event_datetime=create_date_time(
                            date=report_start, time="09:00:00"),
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
                        'test_rejected_3',
                        registration_event_datetime=create_date_time(
                            date=report_start, time="08:20:00"),
                        event_type=EventType.EHR_INTEGRATIONS.value,
                        payload=create_integration_payload(
                            outcome="SUPPRESSED_AND_REACTIVATED")
                    )),
                sourcetype="myevent")

            # rejected

            index.submit(
                json.dumps(
                    create_sample_event(
                        'test_rejected_4',
                        registration_event_datetime=create_date_time(
                            date=report_start, time="09:00:00"),
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
                        'test_rejected_4',
                        registration_event_datetime=create_date_time(
                            date=report_start, time="09:00:00"),
                        event_type=EventType.EHR_INTEGRATIONS.value,
                        payload=create_integration_payload(outcome="REJECTED")
                    )),
                sourcetype="myevent")

            # Act

            test_query = self.generate_splunk_query_from_report(
                'gp2gp_transfer_status_snapshot_report/gp2gp_transfer_status_report_snapshot_base')
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
                '.[] ' +
                '| select( .total_eligible_for_electronic_transfer=="4" )' +
                '| select( .count_rejected == "1")' +
                '| select( .percentage_rejected == "25.00")', telemetry)

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
                        'awaiting_integration_1',
                        registration_event_datetime=create_date_time(
                            date=report_start, time="09:00:00"),
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
                        'awaiting_integration_1',
                        registration_event_datetime=create_date_time(
                            date=report_start, time="09:10:00"),
                        event_type=EventType.READY_TO_INTEGRATE_STATUSES.value
                    )),
                sourcetype="myevent")

            # awaiting_integration - #2

            index.submit(
                json.dumps(
                    create_sample_event(
                        'awaiting_integration_2',
                        registration_event_datetime=create_date_time(
                            date=report_start, time="09:20:00"),
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
                        'awaiting_integration_2',
                        registration_event_datetime=create_date_time(
                            date=report_start, time="09:30:00"),
                        event_type=EventType.READY_TO_INTEGRATE_STATUSES.value
                    )),
                sourcetype="myevent")

            # rejected

            index.submit(
                json.dumps(
                    create_sample_event(
                        'awaiting_integration_3',
                        registration_event_datetime=create_date_time(
                            date=report_start, time="09:00:00"),
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
                        'awaiting_integration_3',
                        registration_event_datetime=create_date_time(
                            date=report_start, time="09:00:00"),
                        event_type=EventType.EHR_INTEGRATIONS.value,
                        payload=create_integration_payload(outcome="REJECTED")
                    )),
                sourcetype="myevent")

            # Act

            test_query = self.generate_splunk_query_from_report(
                'gp2gp_transfer_status_snapshot_report/gp2gp_transfer_status_report_snapshot_base')

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
                '.[] ' +
                '| select( .total_eligible_for_electronic_transfer=="3" )' +
                '| select( .count_awaiting_integration == "2")' +
                '| select( .percentage_awaiting_integration == "66.67")' +
                '| select( .percentage_rejected == "33.33")', telemetry)

        finally:
            self.delete_index(index_name)

    def test_in_progress(self):

        # Arrange

        index_name, index = self.create_index()

         # reporting window
        report_start = datetime_utc_now().date().replace(day=1)
        report_end = datetime_utc_now().date().replace(day=28)
        cutoff = "0"

        try:
            # test requires a datetime less than 20mins
            now = datetime_utc_now()

            now_minus_18_mins = now - timedelta(hours=0, minutes=18)

            now_minus_25_mins = datetime_utc_now() - timedelta(hours=0, minutes=25)

            # test_#1 - compatible and within SLA
            conversationId = 'test_in_progress_within_sla'

            # create a transfer compatibility event less than 20mins from now()
            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversationId,
                        registration_event_datetime=datetime_utc_now().strftime("%Y-%m-%dT%H:%M:%S%z"),
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

            # in order to be within SLA, an EHR request event must be submitted within 20mins.

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversationId,
                        registration_event_datetime=now_minus_18_mins.strftime(
                            "%Y-%m-%dT%H:%M:%S%z"),
                        event_type=EventType.EHR_REQUESTS.value
                    )),
                sourcetype="myevent")

            # test_#2 - compatible and within SLA

            conversationId = 'test_in_progress_within_sla_2'

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversationId,
                        registration_event_datetime=now_minus_25_mins.strftime(
                            "%Y-%m-%dT%H:%M:%S%z"),
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
                        conversation_id=conversationId,
                        registration_event_datetime=now_minus_18_mins.strftime(
                            "%Y-%m-%dT%H:%M:%S%z"),
                        event_type=EventType.EHR_REQUESTS.value
                    )),
                sourcetype="myevent")

            # test_#3 - compatible but outside SLA

            conversationId = 'test_in_progress_outside_sla'

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversationId,
                        registration_event_datetime=datetime_utc_now().strftime("%Y-%m-%dT%H:%M:%S%z"),
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
                        conversation_id=conversationId,
                        registration_event_datetime=now_minus_25_mins.strftime(
                            "%Y-%m-%dT%H:%M:%S%z"),
                        event_type=EventType.EHR_REQUESTS.value
                    )),
                sourcetype="myevent")

            # Act

            test_query = self.generate_splunk_query_from_report(
                'gp2gp_transfer_status_snapshot_report/gp2gp_transfer_status_report_snapshot_base')

            test_query = set_variables_on_query(test_query, {
                "$index$": index_name,
                "$start_time$": report_start.strftime("%Y-%m-%dT%H:%M:%S"),
                "$end_time$": report_end.strftime("%Y-%m-%dT%H:%M:%S"),
                "$cutoff$": cutoff
            })

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service)
            self.LOG.info(f'telemetry: {telemetry}')

            # Assert
            assert jq.first(
                '.[] ' +
                '| select( .total_eligible_for_electronic_transfer=="3" )' +
                '| select( .count_in_progress == "2")' +
                '| select( .percentage_in_progress == "66.67")', telemetry)

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

            # test_#1 - compatible and within SLA
            conversationId = 'test_technical_failure_failed_to_integrate'

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversationId,
                        registration_event_datetime=create_date_time(
                            date=report_start, time="08:00:00"),
                        event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                        sendingPracticeSupplierName="EMIS",
                        requestingPracticeSupplierName="TPP",
                        payload=create_transfer_compatibility_payload(
                            internalTransfer=False,
                            transferCompatible=True
                        )

                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversationId,
                        registration_event_datetime=create_date_time(
                            date=report_start, time="08:10:00"),
                        event_type=EventType.EHR_INTEGRATIONS.value,
                        payload=create_integration_payload(
                            outcome="FAILED_TO_INTEGRATE")
                    )),
                sourcetype="myevent")

            # test_#2 - compatible and TOTAL TRANSFER TIME OUTSIDE SLA 24 HOURS = true

            # test requires a datetime greater than 24 hours
            now_minus_25_hours = datetime_utc_now() - timedelta(hours=25, minutes=0)
            self.LOG.info(f"now_minus_25_mins: {now_minus_25_hours}")

            conversationId = 'test_technical_failure_TOTAL_TRANSFER_TIME_OUTSIDE_SLA_24_HOURS'

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversationId,
                        registration_event_datetime=datetime_utc_now().strftime("%Y-%m-%dT%H:%M:%S%z"),
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
                        conversation_id=conversationId,
                        registration_event_datetime=now_minus_25_hours.strftime(
                            "%Y-%m-%dT%H:%M:%S%z"),
                        event_type=EventType.EHR_RESPONSES.value
                    )),
                sourcetype="myevent")

            # test_#3 - compatible but EHR SENDING OUTSIDE SLA = true

            conversationId = 'test_technical_failure_EHR_SENDING_OUTSIDE_SLA'

             # test requires a datetime less than 20mins
            now_over_20_mins = datetime_utc_now() - timedelta(hours=0, minutes=21)
            self.LOG.info(f"now_minus_18_mins: {now_over_20_mins}")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversationId,
                        registration_event_datetime=create_date_time(
                            date=report_start, time="08:00:00"),
                        event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                        sendingPracticeSupplierName="EMIS",
                        requestingPracticeSupplierName="TPP",
                        payload=create_transfer_compatibility_payload(
                            internalTransfer=False,
                            transferCompatible=True
                        )

                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversationId,
                        registration_event_datetime=now_over_20_mins.strftime(
                            "%Y-%m-%dT%H:%M:%S%z"),
                        event_type=EventType.EHR_REQUESTS.value
                    )),
                sourcetype="myevent")

            # test_#4 - eligible for transfer and EHR REQUESTING OUTSIDE SLA = true

            conversationId = 'test_technical_failure_EHR_REQUESTING_OUTSIDE_SLA'

             # test requires a datetime less than 20mins
            now_over_20_mins = datetime_utc_now() - timedelta(hours=0, minutes=21)
            self.LOG.info(f"now_minus_18_mins: {now_over_20_mins}")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversationId,
                        registration_event_datetime=now_over_20_mins.strftime(
                            "%Y-%m-%dT%H:%M:%S%z"),
                        event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                        sendingPracticeSupplierName="EMIS",
                        requestingPracticeSupplierName="TPP",
                        payload=create_transfer_compatibility_payload(
                            internalTransfer=False,
                            transferCompatible=True
                        )

                    )),
                sourcetype="myevent")

            # test_#5 - in-progress test to check technical failure count working correctly.

             # test requires a datetime greater than 24 hours
            now_minus_23_hours = datetime_utc_now() - timedelta(hours=23, minutes=0)
            self.LOG.info(f"now_minus_23_hours: {now_minus_23_hours}")

            conversationId = 'test_technical_failure_status_IN_PROGRESS'

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversationId,
                        registration_event_datetime=datetime_utc_now().strftime("%Y-%m-%dT%H:%M:%S%z"),
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
                        conversation_id=conversationId,
                        registration_event_datetime=now_minus_23_hours.strftime(
                            "%Y-%m-%dT%H:%M:%S%z"),
                        event_type=EventType.EHR_RESPONSES.value
                    )),
                sourcetype="myevent")

            # Act

            test_query = self.generate_splunk_query_from_report(
                'gp2gp_transfer_status_snapshot_report/gp2gp_transfer_status_report_snapshot_base')
            test_query = set_variables_on_query(test_query, {
                "$index$": index_name,
                "$start_time$": report_start.strftime("%Y-%m-%dT%H:%M:%S"),
                "$end_time$": report_end.strftime("%Y-%m-%dT%H:%M:%S"),
                "$cutoff$": cutoff
            })

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service)
            self.LOG.info(f'telemetry: {telemetry}')

            # Assert
            assert jq.first(
                '.[] ' +
                '| select( .total_eligible_for_electronic_transfer=="5" )' +
                '| select( .count_technical_failure == "4")' +
                '| select( .percentage_technical_failure == "80.00")', telemetry)

        finally:
            self.delete_index(index_name)

    @pytest.mark.parametrize("cutoff, registrationStatus",[(1,"REGISTRATION"),(7,"EHR_REQUESTED"),(11,"EHR_SENT"),(19,"READY_TO_INTEGRATE")])
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
                            registration_event_datetime=create_date_time(date=report_start.replace(day=1), time="08:00:00"),
                            event_type=EventType.REGISTRATIONS.value,
                            payload=create_registration_payload()
                        )),
                    sourcetype="myevent")

                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id=conversationId,
                            registration_event_datetime=create_date_time(date=report_start.replace(day=8), time="05:03:00"),
                            event_type=EventType.EHR_REQUESTS.value,
                        )),
                    sourcetype="myevent")

                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id=conversationId,
                            registration_event_datetime=create_date_time(date=report_start.replace(day=12), time="05:00:00"),
                            event_type=EventType.EHR_RESPONSES.value,
                            payload=create_ehr_response_payload(number_of_placeholders=2)
                        )),
                    sourcetype="myevent")

                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id=conversationId,
                            registration_event_datetime=create_date_time(date=report_start.replace(day=20), time="03:00:00"),
                            event_type=EventType.READY_TO_INTEGRATE_STATUSES.value,
                        )),
                    sourcetype="myevent")

                # Act
                test_query = self.generate_splunk_query_from_report(
                    'gp2gp_transfer_status_snapshot_report/gp2gp_transfer_status_report_snapshot_base')

                test_query = set_variables_on_query(test_query, {
                    "$index$": index_name,    
                    "$start_time$": report_start.strftime("%Y-%m-%dT%H:%m:%s"),
                    "$end_time$": report_end.strftime("%Y-%m-%dT%H:%m:%s"),          
                    "$cutoff$": str(cutoff)
                })

                sleep(2)

                telemetry = get_telemetry_from_splunk(
                    self.savedsearch(test_query), self.splunk_service)
                self.LOG.info(f'telemetry: {telemetry}')

                # Assert
                
                assert jq.first(
                f'.[] | select( .registrationStatus=="{registrationStatus}")', telemetry)

            finally:
                self.delete_index(index_name)