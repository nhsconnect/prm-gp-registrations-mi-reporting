import datetime
import json
from datetime import timedelta
from time import sleep

import jq
import pytest

from helpers.datetime_helper import generate_report_start_date, generate_report_end_date, \
    datetime_utc_now
from helpers.splunk \
    import get_telemetry_from_splunk, create_sample_event, set_variables_on_query, \
    create_integration_payload
from tests.test_base import TestBase, EventType


class TestSuccessfullyIntegratedTrendingRawDataTable(TestBase):
    @pytest.mark.parametrize(
        "time_period, expected_column_format, expected_number_of_events",
        [
            ("month", "%y-%m", 4),
            ("week", "%y-%m-%W", 3),
            ("day", "%y-%m-%d", 2),
        ]
    )
    def test_gp2gp_successfully_integrated_trending_raw_data_table_column_token(self, time_period,
                                                                                expected_column_format,
                                                                                expected_number_of_events):
        # Arrange
        index_name, index = self.create_index()

        # reporting window
        report_start = datetime.datetime(year=2023, month=10, day=1)
        report_end = datetime.datetime(year=2023, month=10, day=31)
        cutoff = "0"

        line = "Successfully integrated"

        event_datetime = report_start
        selected_column = event_datetime.strftime(expected_column_format)

        self.LOG.info(f"column: {selected_column}")

        if time_period == "day":
            other_event_datetime = event_datetime + timedelta(days=1, hours=8)
        elif time_period == "week":
            other_event_datetime = event_datetime + timedelta(weeks=1)
        elif time_period == "month":
            other_event_datetime = event_datetime.replace(month=11)

        self.LOG.info(f"current_event: {event_datetime.strftime('%Y-%m-%dT%H:%M:%S%z')}")
        self.LOG.info(f"other_event: {other_event_datetime.strftime('%Y-%m-%dT%H:%M:%S%z')}")

        snapshot_total_number_of_successful_integrations = 5
        total_outside_selection = snapshot_total_number_of_successful_integrations - expected_number_of_events

        try:
            for i in range(expected_number_of_events):
                index.submit(
                    json.dumps(
                        create_sample_event(
                            f'ehr_successful_integrations_{i}',
                            registration_event_datetime=event_datetime.strftime("%Y-%m-%dT%H:%M:%S%z"),
                            event_type=EventType.EHR_INTEGRATIONS.value,
                            sendingSupplierName="EMIS",
                            requestingSupplierName="TPP",
                            payload=create_integration_payload(
                                outcome="INTEGRATED"
                            )
                        )),
                    sourcetype="myevent"
                )

            for i in range(total_outside_selection):
                index.submit(
                    json.dumps(
                        create_sample_event(
                            f'ehr_other_successful_integrations_{i}',
                            registration_event_datetime=other_event_datetime.strftime("%Y-%m-%dT%H:%M:%S%z"),
                            event_type=EventType.EHR_INTEGRATIONS.value,
                            sendingSupplierName="EMIS",
                            requestingSupplierName="TPP",
                            payload=create_integration_payload(
                                outcome="INTEGRATED"
                            )
                        )),
                    sourcetype="myevent"
                )

            # Act
            test_query = self.generate_splunk_query_from_report(
                'gp2gp_successfully_integrated_trending_report/gp2gp_successfully_integrated_trending_raw_data_table')

            test_query = set_variables_on_query(test_query, {
                "$index$": index_name,
                "$start_time$": report_start.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "$end_time$": report_end.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "$cutoff$": cutoff,
                "$time_period$": time_period,
                "$column$": selected_column,
                "$line$": line,
            })

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service)
            self.LOG.info(f'telemetry: {telemetry}')

            # Assert

            assert len(telemetry) == expected_number_of_events

            for idx in range(expected_number_of_events):
                assert jq.all(
                    f".[] "
                    + f'| select( .conversation_id == "ehr_successful_integrations_{idx}") '
                    + f'| select( .reporting_supplier_name == "TEST_SYSTEM_SUPPLIER") '
                    + f'| select( .requesting_supplier_name == "TPP") '
                    + f'| select( .sending_supplier_name == "EMIS") '
                    + f'| select( .reporting_practice_ods_code == "A00029") '
                    + f'| select( .requesting_practice_ods_code == "A00029") '
                    + f'| select( .sending_practice_ods_code == "B00157") ', telemetry
                )

        finally:
            self.delete_index(index_name)

    @pytest.mark.parametrize(
        "time_period, expected_date_format, line, expected_number_of_events",
        [
            ("month", "%y-%m", "Successfully integrated", 6),
            ("month", "%y-%m", "Not successfully integrated", 5),
            ("week", "%y-%m-%W", "Successfully integrated", 4),
            ("week", "%y-%m-%W", "Not successfully integrated", 3),
            ("day", "%y-%m-%d", "Successfully integrated", 2),
            ("day", "%y-%m-%d", "Not successfully integrated", 1),
        ]
    )
    def test_gp2gp_successfully_integrated_trending_raw_data_table_line_token(self, time_period,
                                                                              expected_date_format,
                                                                              line,
                                                                              expected_number_of_events):
        # Arrange
        index_name, index = self.create_index()

        # reporting window
        report_start = generate_report_start_date()
        report_end = generate_report_end_date()
        cutoff = "0"

        event_datetime = datetime_utc_now()
        selected_column = event_datetime.strftime(expected_date_format)
        self.LOG.info(f"selected column for {line} data: {selected_column}")

        current_event_outcome = "INTEGRATED" if line == "Successfully integrated" else "REJECTED"
        other_event_outcome = "REJECTED" if line == "Successfully integrated" else "INTEGRATED"

        try:
            for i in range(expected_number_of_events):
                index.submit(
                    json.dumps(
                        create_sample_event(
                            f'ehr_integrations_{i}',
                            registration_event_datetime=event_datetime.strftime("%Y-%m-%dT%H:%M:%S%z"),
                            event_type=EventType.EHR_INTEGRATIONS.value,
                            sendingSupplierName="EMIS",
                            requestingSupplierName="TPP",
                            payload=create_integration_payload(
                                outcome=current_event_outcome
                            )
                        )),
                    sourcetype="myevent"
                )

                index.submit(
                    json.dumps(
                        create_sample_event(
                            f'ehr_other_integrations_{i}',
                            registration_event_datetime=event_datetime.strftime("%Y-%m-%dT%H:%M:%S%z"),
                            event_type=EventType.EHR_INTEGRATIONS.value,
                            sendingSupplierName="EMIS",
                            requestingSupplierName="TPP",
                            payload=create_integration_payload(
                                outcome=other_event_outcome
                            )
                        )),
                    sourcetype="myevent"
                )

            # Act
            test_query = self.generate_splunk_query_from_report(
                'gp2gp_successfully_integrated_trending_report/gp2gp_successfully_integrated_trending_raw_data_table')

            test_query = set_variables_on_query(test_query, {
                "$index$": index_name,
                "$start_time$": report_start.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "$end_time$": report_end.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "$cutoff$": cutoff,
                "$time_period$": time_period,
                "$column$": selected_column,
                "$line$": line,
            })

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service)
            self.LOG.info(f'telemetry: {telemetry}')

            # Assert

            assert len(telemetry) == expected_number_of_events

            for idx in range(expected_number_of_events):
                assert jq.all(
                    f".[] "
                    + f'| select( .conversation_id == "ehr_integrations_{idx}") '
                    + f'| select( .reporting_supplier_name == "TEST_SYSTEM_SUPPLIER") '
                    + f'| select( .requesting_supplier_name == "TPP") '
                    + f'| select( .sending_supplier_name == "EMIS") '
                    + f'| select( .reporting_practice_ods_code == "A00029") '
                    + f'| select( .requesting_practice_ods_code == "A00029") '
                    + f'| select( .sending_practice_ods_code == "B00157") ', telemetry
                )

        finally:
            self.delete_index(index_name)
