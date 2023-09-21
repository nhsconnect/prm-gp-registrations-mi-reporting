import json
import pytest
from time import sleep
import jq
from helpers.splunk \
    import get_telemetry_from_splunk, create_sample_event, set_variables_on_query, \
    create_integration_payload
from tests.test_base import TestBase, EventType
from helpers.datetime_helper import create_date_time, generate_report_start_date, \
    generate_report_end_date


class TestSuccessfullyIntegratedRawDataTableOutputs(TestBase):

    def test_gp2gp_successfully_integrated_raw_data_table_successfully_integrated(self):

        # Arrange
        index_name, index = self.create_index()

        # reporting window
        report_start = generate_report_start_date()
        report_end = generate_report_end_date()
        cutoff = "0"

        try:
            different_outcomes_list = ["INTEGRATED",
                                       "INTEGRATED_AND_SUPPRESSED",
                                       "SUPPRESSED_AND_REACTIVATED",
                                       "FILED_AS_ATTACHMENT",
                                       "INTERNAL_TRANSFER",
                                       "REJECTED"
                                       ]
            different_outcomes_list.sort()

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

            # Act
            test_query = self.generate_splunk_query_from_report(
                'gp2gp_successfully_integrated_snapshot_report/'
                'gp2gp_successfully_integrated_raw_data_table')

            test_query = set_variables_on_query(test_query, {
                "$index$": index_name,
                "$start_time$": report_start.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "$end_time$": report_end.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "$cutoff$": cutoff,
                "$column$": "Successfully integrated"
            })

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service)
            self.LOG.info(f'telemetry: {telemetry}')

            # Assert
            successful_outcomes = [outcome for outcome in different_outcomes_list if outcome != "REJECTED"]
            conversation_ids = [f"ehr_integrations_{outcome}" for outcome in successful_outcomes]
            for idx in range(len(conversation_ids)):
                assert jq.first(
                    f".[{idx}] "
                    + f'| select( .conversation_id == "{conversation_ids[idx]}") '
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

    def test_gp2gp_successfully_integrated_raw_data_table_not_successfully_integrated(self):

        # Arrange
        index_name, index = self.create_index()

        # reporting window
        report_start = generate_report_start_date()
        report_end = generate_report_end_date()
        cutoff = "0"

        try:
            different_outcomes_list = ["INTEGRATED",
                                       "INTEGRATED_AND_SUPPRESSED",
                                       "SUPPRESSED_AND_REACTIVATED",
                                       "FILED_AS_ATTACHMENT",
                                       "INTERNAL_TRANSFER",
                                       "REJECTED"
                                       ]
            different_outcomes_list.sort()

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

            # Act
            test_query = self.generate_splunk_query_from_report(
                'gp2gp_successfully_integrated_snapshot_report/'
                'gp2gp_successfully_integrated_raw_data_table')

            test_query = set_variables_on_query(test_query, {
                "$index$": index_name,
                "$start_time$": report_start.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "$end_time$": report_end.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "$cutoff$": cutoff,
                "$column$": "Not successfully integrated"
            })

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service)
            self.LOG.info(f'telemetry: {telemetry}')

            # Assert
            assert jq.first(
                f".[0] "
                + f'| select( .conversation_id == "ehr_integrations_REJECTED") '
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
