import json
import pytest
from time import sleep
import jq
from helpers.splunk \
    import get_telemetry_from_splunk, create_sample_event, set_variables_on_query, \
    create_integration_payload, create_transfer_compatibility_payload
from tests.test_base import TestBase, EventType
from helpers.datetime_helper import create_date_time, generate_report_start_date, \
    generate_report_end_date


class TestSuccessfullyIntegratedSnapshotReportOutputs(TestBase):

    def test_gp2gp_successfully_integrated_report_snapshot_count(self):

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
                        f'ehr_integrations_not_eligible_for_electronic_transfer',
                        registration_event_datetime=create_date_time(report_start, "08:00:00"),
                        event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                        sendingSupplierName="EMIS",
                        requestingSupplierName="TPP",
                        payload=create_transfer_compatibility_payload(
                            internalTransfer=False,
                            transferCompatible=False
                        )

                    )),
                sourcetype="myevent")

            # Act
            test_query = self.generate_splunk_query_from_report(
                'gp2gp_successfully_integrated_snapshot_report/'
                'gp2gp_successfully_integrated_snapshot_report_count')

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
            expected_values = {"0": {"column": "Not successfully integrated",
                                     "count": "1"},
                               "1": {"column": "Successfully integrated",
                                     "count": "5"},
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

    def test_gp2gp_successfully_integrated_report_snapshot_percentage(self):

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
                'gp2gp_successfully_integrated_snapshot_report_percentage')

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
            expected_values = {"0": {"column": "Not successfully integrated",
                                     "count": "16.67"},
                               "1": {"column": "Successfully integrated",
                                     "count": "83.33"},
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
