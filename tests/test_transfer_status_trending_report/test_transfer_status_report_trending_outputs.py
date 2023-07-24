import logging
import os
from enum import Enum
import pytest
import json
from time import sleep
from splunklib import client
import jq

from helpers.datetime_helper import datetime_utc_now
from helpers.splunk \
    import get_telemetry_from_splunk, get_or_create_index, create_sample_event, set_variables_on_query, \
    create_integration_payload,  create_error_payload, create_transfer_compatibility_payload
from datetime import datetime, timedelta
from jinja2 import Environment, FileSystemLoader
from tests.test_base import TestBase, EventType


class TestTransferStatusReportTrendingOutputs(TestBase):

    def test_gp2gp_transfer_status_report_trending_count_with_start_end_times_as_datetimes(self):

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
                'gp2gp_transfer_status_trending_report/gp2gp_transfer_status_trending_report_count')

            test_query = set_variables_on_query(test_query, {
                "$index$": index_name,
                "$start_time$": "2023-03-01T00:00:00.000+0000",
                "$end_time$": "2023-03-31T00:00:00.000+0000",
                "$cutoff$": "0",
                "$time_period$": "month"
            })

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service)
            self.LOG.info(f'telemetry: {telemetry}')

            # Assert
            expected_values = {"0": {"time_period": "23-03",
                                     "IN_PROGRESS": "2"}
                               }

            for row, row_values in expected_values.items():
                row_values_as_jq_str = ' '.join(
                    [f"| select(.{key}==\"{value}\") " for key, value in row_values.items()]
                )
                self.LOG.info(f'.[{row}] {row_values_as_jq_str} ')
                assert jq.first(
                    f'.[{row}] {row_values_as_jq_str} ', telemetry)

        finally:
            self.delete_index(index_name)

    def test_gp2gp_transfer_status_report_trending_count_with_start_end_times_as_relative_times(self):

        # Arrange
        index_name, index = self.create_index()

        now_minus_2_days = datetime_utc_now() - timedelta(days=2)

        try:

            index.submit(
                json.dumps(
                    create_sample_event(
                        'test_total_eligible_for_electronic_transfer_1',
                        registration_event_datetime=now_minus_2_days.strftime(
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
                        'test_total_eligible_for_electronic_transfer_2',
                        registration_event_datetime=now_minus_2_days.strftime(
                            "%Y-%m-%dT%H:%M:%S%z"),
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
                        registration_event_datetime=now_minus_2_days.strftime(
                            "%Y-%m-%dT%H:%M:%S%z"),
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
                'gp2gp_transfer_status_trending_report/gp2gp_transfer_status_trending_report_count')

            test_query = set_variables_on_query(test_query, {
                "$index$": index_name,
                "$start_time$": "-3d@d",
                "$end_time$": "now",
                "$cutoff$": "0",
                "$time_period$": "month"
            })

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service)
            self.LOG.info(f'telemetry: {telemetry}')

            # Assert
            expected_values = {"0": {"time_period": now_minus_2_days.strftime("%y-%m"),
                                     "IN_PROGRESS": "2"}
                               }

            for row, row_values in expected_values.items():
                row_values_as_jq_str = ' '.join(
                    [f"| select(.{key}==\"{value}\") " for key, value in row_values.items()]
                )
                self.LOG.info(f'.[{row}] {row_values_as_jq_str} ')
                assert jq.first(
                    f'.[{row}] {row_values_as_jq_str} ', telemetry)

        finally:
            self.delete_index(index_name)

    def test_gp2gp_transfer_status_report_trending_count_with_cutoff_1_day_fail(self):
        """This test ensures that new conversations are not included in the report when
        the registation_event_datetime is outside the reporting window, but inside the cutoff
        window."""

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
                        registration_event_datetime="2023-03-31T15:00:00.000+0000",
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

            # Act
            test_query = self.generate_splunk_query_from_report(
                'gp2gp_transfer_status_trending_report/gp2gp_transfer_status_trending_report_count')

            test_query = set_variables_on_query(test_query, {
                "$index$": index_name,
                "$start_time$": "2023-03-01T00:00:00.000+0000",
                "$end_time$": "2023-03-31T00:00:00.000+0000",
                "$cutoff$": "1",
                "$time_period$": "month"
            })

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service)
            self.LOG.info(f'telemetry: {telemetry}')

            # Assert
            expected_values = {"0": {"time_period": "23-03",
                                     "IN_PROGRESS": "1"}
                               }

            for row, row_values in expected_values.items():
                row_values_as_jq_str = ' '.join(
                    [f"| select(.{key}==\"{value}\") " for key, value in row_values.items()]
                )
                self.LOG.info(f'.[{row}] {row_values_as_jq_str} ')
                assert jq.first(
                    f'.[{row}] {row_values_as_jq_str} ', telemetry)

        finally:
            self.delete_index(index_name)

    def test_gp2gp_transfer_status_report_trending_count_with_cutoff_1_day_pass(self):
        """This test ensures that events that lie inside the cutoff window and belong to
        a conversation_id that started inside the reporting window are included in the report."""

        # Arrange
        index_name, index = self.create_index()
        conversation_id = 'test_total_eligible_for_electronic_transfer_1'

        try:

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversation_id,
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
                        conversation_id=conversation_id,
                        registration_event_datetime="2023-03-10T09:10:00+0000",
                        event_type=EventType.READY_TO_INTEGRATE_STATUSES.value
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversation_id,
                        registration_event_datetime="2023-03-12T08:10:00+0000",
                        event_type=EventType.EHR_INTEGRATIONS.value,
                        payload=create_integration_payload(
                            outcome="INTEGRATED_AND_SUPPRESSED")
                    )),
                sourcetype="myevent")

            # Act
            test_query = self.generate_splunk_query_from_report(
                'gp2gp_transfer_status_trending_report/gp2gp_transfer_status_trending_report_count')

            test_query = set_variables_on_query(test_query, {
                "$index$": index_name,
                "$start_time$": "2023-03-10T00:00:00.000+0000",
                "$end_time$": "2023-03-11T00:00:00.000+0000",
                "$cutoff$": "1",
                "$time_period$": "month"
            })

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service)
            self.LOG.info(f'telemetry: {telemetry}')

            # Assert
            expected_values = {"0": {"time_period": "23-03",
                                     "AWAITING_INTEGRATION": "1"}
                               }

            for row, row_values in expected_values.items():
                row_values_as_jq_str = ' '.join(
                    [f"| select(.{key}==\"{value}\") " for key, value in row_values.items()]
                )
                self.LOG.info(f'.[{row}] {row_values_as_jq_str} ')
                assert jq.first(
                    f'.[{row}] {row_values_as_jq_str} ', telemetry)

        finally:
            self.delete_index(index_name)

    def test_gp2gp_transfer_status_report_trending_count_with_time_period_month(self):

        # Arrange
        index_name, index = self.create_index()

        conversation_id_1 = 'test_total_eligible_for_electronic_transfer_1'
        conversation_id_2 = 'test_total_eligible_for_electronic_transfer_2'

        try:

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversation_id_1,
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
                        conversation_id=conversation_id_1,
                        registration_event_datetime="2023-03-10T09:10:00+0000",
                        event_type=EventType.READY_TO_INTEGRATE_STATUSES.value
                    )),
                sourcetype="myevent")


            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversation_id_2,
                        registration_event_datetime="2023-04-11T08:00:00+0000",
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
                        conversation_id=conversation_id_2,
                        registration_event_datetime="2023-04-11T09:10:00+0000",
                        event_type=EventType.READY_TO_INTEGRATE_STATUSES.value
                    )),
                sourcetype="myevent")



            # Act
            test_query = self.generate_splunk_query_from_report(
                'gp2gp_transfer_status_trending_report/gp2gp_transfer_status_trending_report_count')

            test_query = set_variables_on_query(test_query, {
                "$index$": index_name,
                "$start_time$": "2023-03-01T00:00:00.000+0000",
                "$end_time$": "2023-04-30T00:00:00.000+0000",
                "$cutoff$": "1",
                "$time_period$": "month"
            })

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service)
            self.LOG.info(f'telemetry: {telemetry}')

            # Assert
            expected_values = {"0": {"time_period": "23-03",
                                     "AWAITING_INTEGRATION": "1"},
                               "1": {"time_period": "23-04",
                                     "AWAITING_INTEGRATION": "1"},
                               }

            for row, row_values in expected_values.items():
                row_values_as_jq_str = ' '.join(
                    [f"| select(.{key}==\"{value}\") " for key, value in row_values.items()]
                )
                self.LOG.info(f'.[{row}] {row_values_as_jq_str} ')
                assert jq.first(
                    f'.[{row}] {row_values_as_jq_str} ', telemetry)

        finally:
            self.delete_index(index_name)

    def test_gp2gp_transfer_status_report_trending_count_with_time_period_week(self):

        # Arrange
        index_name, index = self.create_index()

        conversation_id_1 = 'test_total_eligible_for_electronic_transfer_1'
        conversation_id_2 = 'test_total_eligible_for_electronic_transfer_2'

        try:

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversation_id_1,
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
                        conversation_id=conversation_id_1,
                        registration_event_datetime="2023-03-10T09:10:00+0000",
                        event_type=EventType.READY_TO_INTEGRATE_STATUSES.value
                    )),
                sourcetype="myevent")


            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversation_id_2,
                        registration_event_datetime="2023-03-17T08:00:00+0000",
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
                        conversation_id=conversation_id_2,
                        registration_event_datetime="2023-03-17T09:10:00+0000",
                        event_type=EventType.READY_TO_INTEGRATE_STATUSES.value
                    )),
                sourcetype="myevent")



            # Act
            test_query = self.generate_splunk_query_from_report(
                'gp2gp_transfer_status_trending_report/gp2gp_transfer_status_trending_report_count')

            test_query = set_variables_on_query(test_query, {
                "$index$": index_name,
                "$start_time$": "2023-03-01T00:00:00.000+0000",
                "$end_time$": "2023-03-31T00:00:00.000+0000",
                "$cutoff$": "1",
                "$time_period$": "week"
            })

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service)
            self.LOG.info(f'telemetry: {telemetry}')

            # Assert
            expected_values = {"0": {"time_period": "23-03-10",
                                     "AWAITING_INTEGRATION": "1"},
                               "1": {"time_period": "23-03-11",
                                     "AWAITING_INTEGRATION": "1"},
                               }

            for row, row_values in expected_values.items():
                row_values_as_jq_str = ' '.join(
                    [f"| select(.{key}==\"{value}\") " for key, value in row_values.items()]
                )
                self.LOG.info(f'.[{row}] {row_values_as_jq_str} ')
                assert jq.first(
                    f'.[{row}] {row_values_as_jq_str} ', telemetry)

        finally:
            self.delete_index(index_name)

    def test_gp2gp_transfer_status_report_trending_percentage_with_start_end_times_as_datetimes(self):

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
                'gp2gp_transfer_status_trending_report/gp2gp_transfer_status_trending_report_percentage')

            test_query = set_variables_on_query(test_query, {
                "$index$": index_name,
                "$start_time$": "2023-03-01T00:00:00.000+0000",
                "$end_time$": "2023-03-31T00:00:00.000+0000",
                "$cutoff$": "0",
                "$time_period$": "month"
            })

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service)
            self.LOG.info(f'telemetry: {telemetry}')

            # Assert
            expected_values = {"0": {"time_period": "23-03",
                                     "IN_PROGRESS": "100.00"}
                               }

            for row, row_values in expected_values.items():
                row_values_as_jq_str = ' '.join(
                    [f"| select(.{key}==\"{value}\") " for key, value in row_values.items()]
                )
                self.LOG.info(f'.[{row}] {row_values_as_jq_str} ')
                assert jq.first(
                    f'.[{row}] {row_values_as_jq_str} ', telemetry)

        finally:
            self.delete_index(index_name)

    def test_gp2gp_transfer_status_report_trending_percentage_with_start_end_times_as_relative_times(self):

        # Arrange
        index_name, index = self.create_index()

        now_minus_2_days = datetime_utc_now() - timedelta(days=2)

        try:

            index.submit(
                json.dumps(
                    create_sample_event(
                        'test_total_eligible_for_electronic_transfer_1',
                        registration_event_datetime=now_minus_2_days.strftime(
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
                        'test_total_eligible_for_electronic_transfer_2',
                        registration_event_datetime=now_minus_2_days.strftime(
                            "%Y-%m-%dT%H:%M:%S%z"),
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
                        registration_event_datetime=now_minus_2_days.strftime(
                            "%Y-%m-%dT%H:%M:%S%z"),
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
                'gp2gp_transfer_status_trending_report/gp2gp_transfer_status_trending_report_percentage')

            test_query = set_variables_on_query(test_query, {
                "$index$": index_name,
                "$start_time$": "-3d@d",
                "$end_time$": "now",
                "$cutoff$": "0",
                "$time_period$": "month"
            })

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service)
            self.LOG.info(f'telemetry: {telemetry}')

            # Assert
            expected_values = {"0": {"time_period": now_minus_2_days.strftime("%y-%m"),
                                     "IN_PROGRESS": "100.00"}
                               }

            for row, row_values in expected_values.items():
                row_values_as_jq_str = ' '.join(
                    [f"| select(.{key}==\"{value}\") " for key, value in row_values.items()]
                )
                self.LOG.info(f'.[{row}] {row_values_as_jq_str} ')
                assert jq.first(
                    f'.[{row}] {row_values_as_jq_str} ', telemetry)

        finally:
            self.delete_index(index_name)

    def test_gp2gp_transfer_status_report_trending_percentage_with_cutoff_1_day_fail(self):
        """This test ensures that new conversations are not included in the report when
        the registation_event_datetime is outside the reporting window, but inside the cutoff
        window."""

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
                        registration_event_datetime="2023-03-31T15:00:00.000+0000",
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

            # Act
            test_query = self.generate_splunk_query_from_report(
                'gp2gp_transfer_status_trending_report/gp2gp_transfer_status_trending_report_percentage')

            test_query = set_variables_on_query(test_query, {
                "$index$": index_name,
                "$start_time$": "2023-03-01T00:00:00.000+0000",
                "$end_time$": "2023-03-31T00:00:00.000+0000",
                "$cutoff$": "1",
                "$time_period$": "month"
            })

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service)
            self.LOG.info(f'telemetry: {telemetry}')

            # Assert
            expected_values = {"0": {"time_period": "23-03",
                                     "IN_PROGRESS": "100.00"}
                               }

            for row, row_values in expected_values.items():
                row_values_as_jq_str = ' '.join(
                    [f"| select(.{key}==\"{value}\") " for key, value in row_values.items()]
                )
                self.LOG.info(f'.[{row}] {row_values_as_jq_str} ')
                assert jq.first(
                    f'.[{row}] {row_values_as_jq_str} ', telemetry)

        finally:
            self.delete_index(index_name)

    def test_gp2gp_transfer_status_report_trending_percentage_with_cutoff_1_day_pass(self):
        """This test ensures that events that lie inside the cutoff window and belong to
        a conversation_id that started inside the reporting window are included in the report."""

        # Arrange
        index_name, index = self.create_index()
        conversation_id = 'test_total_eligible_for_electronic_transfer_1'

        try:

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversation_id,
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
                        conversation_id=conversation_id,
                        registration_event_datetime="2023-03-10T09:10:00+0000",
                        event_type=EventType.READY_TO_INTEGRATE_STATUSES.value
                    )),
                sourcetype="myevent")

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversation_id,
                        registration_event_datetime="2023-03-12T08:10:00+0000",
                        event_type=EventType.EHR_INTEGRATIONS.value,
                        payload=create_integration_payload(
                            outcome="INTEGRATED_AND_SUPPRESSED")
                    )),
                sourcetype="myevent")

            # Act
            test_query = self.generate_splunk_query_from_report(
                'gp2gp_transfer_status_trending_report/gp2gp_transfer_status_trending_report_percentage')

            test_query = set_variables_on_query(test_query, {
                "$index$": index_name,
                "$start_time$": "2023-03-10T00:00:00.000+0000",
                "$end_time$": "2023-03-11T00:00:00.000+0000",
                "$cutoff$": "1",
                "$time_period$": "month"
            })

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service)
            self.LOG.info(f'telemetry: {telemetry}')

            # Assert
            expected_values = {"0": {"time_period": "23-03",
                                     "AWAITING_INTEGRATION": "100.00"}
                               }

            for row, row_values in expected_values.items():
                row_values_as_jq_str = ' '.join(
                    [f"| select(.{key}==\"{value}\") " for key, value in row_values.items()]
                )
                self.LOG.info(f'.[{row}] {row_values_as_jq_str} ')
                assert jq.first(
                    f'.[{row}] {row_values_as_jq_str} ', telemetry)

        finally:
            self.delete_index(index_name)

    def test_gp2gp_transfer_status_report_trending_percentage_with_time_period_month(self):

        # Arrange
        index_name, index = self.create_index()

        conversation_id_1 = 'test_total_eligible_for_electronic_transfer_1'
        conversation_id_2 = 'test_total_eligible_for_electronic_transfer_2'

        try:

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversation_id_1,
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
                        conversation_id=conversation_id_1,
                        registration_event_datetime="2023-03-10T09:10:00+0000",
                        event_type=EventType.READY_TO_INTEGRATE_STATUSES.value
                    )),
                sourcetype="myevent")


            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversation_id_2,
                        registration_event_datetime="2023-04-11T08:00:00+0000",
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
                        conversation_id=conversation_id_2,
                        registration_event_datetime="2023-04-11T09:10:00+0000",
                        event_type=EventType.READY_TO_INTEGRATE_STATUSES.value
                    )),
                sourcetype="myevent")



            # Act
            test_query = self.generate_splunk_query_from_report(
                'gp2gp_transfer_status_trending_report/gp2gp_transfer_status_trending_report_percentage')

            test_query = set_variables_on_query(test_query, {
                "$index$": index_name,
                "$start_time$": "2023-03-01T00:00:00.000+0000",
                "$end_time$": "2023-04-30T00:00:00.000+0000",
                "$cutoff$": "1",
                "$time_period$": "month"
            })

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service)
            self.LOG.info(f'telemetry: {telemetry}')

            # Assert
            expected_values = {"0": {"time_period": "23-03",
                                     "AWAITING_INTEGRATION": "100.00"},
                               "1": {"time_period": "23-04",
                                     "AWAITING_INTEGRATION": "100.00"},
                               }

            for row, row_values in expected_values.items():
                row_values_as_jq_str = ' '.join(
                    [f"| select(.{key}==\"{value}\") " for key, value in row_values.items()]
                )
                self.LOG.info(f'.[{row}] {row_values_as_jq_str} ')
                assert jq.first(
                    f'.[{row}] {row_values_as_jq_str} ', telemetry)

        finally:
            self.delete_index(index_name)

    def test_gp2gp_transfer_status_report_trending_percentage_with_time_period_week(self):

        # Arrange
        index_name, index = self.create_index()

        conversation_id_1 = 'test_total_eligible_for_electronic_transfer_1'
        conversation_id_2 = 'test_total_eligible_for_electronic_transfer_2'

        try:

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversation_id_1,
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
                        conversation_id=conversation_id_1,
                        registration_event_datetime="2023-03-10T09:10:00+0000",
                        event_type=EventType.READY_TO_INTEGRATE_STATUSES.value
                    )),
                sourcetype="myevent")


            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=conversation_id_2,
                        registration_event_datetime="2023-03-17T08:00:00+0000",
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
                        conversation_id=conversation_id_2,
                        registration_event_datetime="2023-03-17T09:10:00+0000",
                        event_type=EventType.READY_TO_INTEGRATE_STATUSES.value
                    )),
                sourcetype="myevent")



            # Act
            test_query = self.generate_splunk_query_from_report(
                'gp2gp_transfer_status_trending_report/gp2gp_transfer_status_trending_report_percentage')

            test_query = set_variables_on_query(test_query, {
                "$index$": index_name,
                "$start_time$": "2023-03-01T00:00:00.000+0000",
                "$end_time$": "2023-03-31T00:00:00.000+0000",
                "$cutoff$": "1",
                "$time_period$": "week"
            })

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service)
            self.LOG.info(f'telemetry: {telemetry}')

            # Assert
            expected_values = {"0": {"time_period": "23-03-10",
                                     "AWAITING_INTEGRATION": "100.00"},
                               "1": {"time_period": "23-03-11",
                                     "AWAITING_INTEGRATION": "100.00"},
                               }

            for row, row_values in expected_values.items():
                row_values_as_jq_str = ' '.join(
                    [f"| select(.{key}==\"{value}\") " for key, value in row_values.items()]
                )
                self.LOG.info(f'.[{row}] {row_values_as_jq_str} ')
                assert jq.first(
                    f'.[{row}] {row_values_as_jq_str} ', telemetry)

        finally:
            self.delete_index(index_name)


