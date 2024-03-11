import pytest
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
                            set_variables_on_query, create_error_payload, create_ehr_response_payload)
from tests.test_base import EventType, TestBase


class TestInProgressSlaTrendingRawDataTable(TestBase):

    @pytest.mark.parametrize("column_indicator", ["yesterday", "two_days_ago"])
    def test_in_progress_sla_trending_raw_data_table_select_column_token(self, column_indicator):
        # Arrange
        index_name, index = self.create_index()

        if column_indicator == "yesterday":
            td_hours = 25
            num_events = 1
        elif column_indicator == "two_days_ago":
            td_hours = 49
            num_events = 2
        else:
            raise ValueError('column value should be "yesterday" or "two_days_ago"')

        # reporting window
        report_start = datetime_utc_now() - timedelta(hours=72)
        report_end = generate_report_end_date()
        cutoff = "0"

        try:
            column = (datetime_utc_now() - timedelta(hours=td_hours)).strftime("%Y-%m-%d")
            self.LOG.info(f"column: {column}")

            # Broken 24h sla
            for idx in range(num_events):
                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id="broken_24h_sla_conv"+str(idx),
                            registration_event_datetime=(
                                    datetime_utc_now() - timedelta(hours=td_hours)
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
                            conversation_id="broken_24h_sla_conv"+str(idx),
                            registration_event_datetime=(
                                    datetime_utc_now() - timedelta(hours=td_hours)
                            ).strftime("%Y-%m-%dT%H:%M:%S%z"),
                            event_type=EventType.EHR_REQUESTS.value,
                            sendingSupplierName="EMIS",
                            requestingSupplierName="TPP",
                        )
                    ),
                    sourcetype="myevent",
                )

                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id="broken_24h_sla_conv"+str(idx),
                            registration_event_datetime=(
                                    datetime_utc_now() - timedelta(hours=td_hours)
                            ).strftime("%Y-%m-%dT%H:%M:%S%z"),
                            event_type=EventType.EHR_RESPONSES.value,
                            sendingSupplierName="EMIS",
                            requestingSupplierName="TPP",
                        )
                    ),
                    sourcetype="myevent",
                )

            # Act
            test_query = self.generate_splunk_query_from_report(
                "gp2gp_in_progress_sla_trending_report/gp2gp_in_progress_sla_trending_report_raw_data_table"
            )

            test_query = set_variables_on_query(
                test_query,
                {
                    "$index$": index_name,
                    "$start_time$": report_start.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    "$end_time$": report_end.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    "$cutoff$": cutoff,
                    "$time_period$": "day",
                    "$line$": "B24",
                    "$column$": column

                },
            )

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service
            )
            self.LOG.info(f"telemetry: {telemetry}")

            # Assert
            assert len(telemetry) == num_events

            for idx in range(num_events):
                assert jq.all(
                    f".[{idx}] "
                    + f'| select( .conversation_id == "broken_24h_sla_conv{str(idx)}") '
                    + f'| select( .reporting_supplier_name == "TEST_SYSTEM_SUPPLIER") '
                    + f'| select( .requesting_supplier_name == "TPP") '
                    + f'| select( .sending_supplier_name == "EMIS") '
                    + f'| select( .reporting_practice_ods_code == "A00029") '
                    + f'| select( .requesting_practice_ods_code == "A00029") '
                    + f'| select( .sending_practice_ods_code == "B00157") '
                    , telemetry
                )

        finally:
            self.delete_index(index_name)

    @pytest.mark.parametrize('line', ['BEhrS', 'BEhrR'])
    def test_in_progress_sla_trending_raw_data_table_select_line_token(self, line):
        # Arrange
        index_name, index = self.create_index()

        if line == "BEhrS":
            num_events = 2
            ehr_request_td_mins = 21
            ehr_response_td_mins = 0
        elif line == "BEhrR":
            num_events = 1
            ehr_request_td_mins = 0
            ehr_response_td_mins = 0
        else:
            raise ValueError('line value should be "B24" or "IF"')

        # reporting window
        report_start = generate_report_start_date()
        report_end = generate_report_end_date()
        cutoff = "0"

        try:

            for idx in range(num_events):
                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id="broken_24h_sla_conv"+str(idx),
                            registration_event_datetime=(
                                    datetime_utc_now() - timedelta(minutes=21
                                                                   )
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
                            conversation_id="broken_24h_sla_conv"+str(idx),
                            registration_event_datetime=(
                                    datetime_utc_now() - timedelta(minutes=ehr_request_td_mins)
                            ).strftime("%Y-%m-%dT%H:%M:%S%z"),
                            event_type=EventType.EHR_REQUESTS.value,
                            sendingSupplierName="EMIS",
                            requestingSupplierName="TPP",
                        )
                    ),
                    sourcetype="myevent",
                )

                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id="broken_24h_sla_conv"+str(idx),
                            registration_event_datetime=(
                                    datetime_utc_now() - timedelta(minutes=ehr_response_td_mins)
                            ).strftime("%Y-%m-%dT%H:%M:%S%z"),
                            event_type=EventType.EHR_RESPONSES.value,
                            sendingSupplierName="EMIS",
                            requestingSupplierName="TPP",
                        )
                    ),
                    sourcetype="myevent",
                )

                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id="broken_24h_sla_conv"+str(idx),
                            registration_event_datetime=(
                                    datetime_utc_now()
                            ).strftime("%Y-%m-%dT%H:%M:%S%z"),
                            event_type=EventType.READY_TO_INTEGRATE_STATUSES.value,
                            sendingSupplierName="EMIS",
                            requestingSupplierName="TPP",
                        )
                    ),
                    sourcetype="myevent",
                )

            column = (datetime_utc_now() - timedelta(minutes=2)).strftime("%Y-%m-%d")
            self.LOG.info(f"column: {column}")

            # Act
            test_query = self.generate_splunk_query_from_report(
                "gp2gp_in_progress_sla_trending_report/gp2gp_in_progress_sla_trending_report_raw_data_table"
            )

            test_query = set_variables_on_query(
                test_query,
                {
                    "$index$": index_name,
                    "$start_time$": report_start.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    "$end_time$": report_end.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    "$cutoff$": cutoff,
                    "$time_period$": "day",
                    "$line$": line,
                    "$column$": column

                },
            )

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service
            )
            self.LOG.info(f"telemetry: {telemetry}")

            # Assert
            assert len(telemetry) == num_events

            for idx in range(num_events):
                assert jq.all(
                    f".[{idx}] "
                    + f'| select( .conversation_id == "broken_24h_sla_conv{str(idx)}") '
                    + f'| select( .reporting_supplier_name == "TEST_SYSTEM_SUPPLIER") '
                    + f'| select( .requesting_supplier_name == "TPP") '
                    + f'| select( .sending_supplier_name == "EMIS") '
                    + f'| select( .reporting_practice_ods_code == "A00029") '
                    + f'| select( .requesting_practice_ods_code == "A00029") '
                    + f'| select( .sending_practice_ods_code == "B00157") '
                    , telemetry
                )

        finally:
            self.delete_index(index_name)
