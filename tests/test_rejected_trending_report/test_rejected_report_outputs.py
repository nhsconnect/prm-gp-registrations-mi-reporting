import datetime
import json
import pytest
from time import sleep
import jq
from helpers.splunk \
    import get_telemetry_from_splunk, create_sample_event, set_variables_on_query, \
    create_integration_payload, create_transfer_compatibility_payload
from tests.test_base import TestBase, EventType
from helpers.datetime_helper import create_date_time


class TestRejectedTrendingReportOutputs(TestBase):

    @pytest.mark.parametrize("time_period, expected_output", [
        ("month", {"0": {"time_period": "23-10",
                         "Not rejected": "5",
                         "Rejected": "1"
                         }
                   }
         ),
        ("week", {"0": {"time_period": "23-10-39",
                        "Not rejected": "1",
                        "Rejected": "1"
                        },
                  "1": {"time_period": "23-10-40",
                        "Not rejected": "4",
                        "Rejected": "0"
                        },
                  }
         ),
        ("day", {"0": {"time_period": "23-10-01",
                       "Not rejected": "1",
                       "Rejected": "1"
                       },
                 "1": {"time_period": "23-10-02",
                       "Not rejected": "1",
                       "Rejected": "0"
                       },
                 "2": {"time_period": "23-10-03",
                       "Not rejected": "1",
                       "Rejected": "0"
                       },
                 "3": {"time_period": "23-10-04",
                       "Not rejected": "1",
                       "Rejected": "0"
                       },
                 "4": {"time_period": "23-10-05",
                       "Not rejected": "1",
                       "Rejected": "0"
                       },
                 }
         ),
    ])
    def test_gp2gp_successfully_integrated_report_trending_count(self, time_period, expected_output):

        # Arrange
        index_name, index = self.create_index()

        # reporting window
        report_start = datetime.datetime(year=2023, month=10, day=1)
        report_end = datetime.datetime(year=2023, month=10, day=31)
        cutoff = "0"

        try:
            different_outcomes_list = {"successful_status": ["INTEGRATED",
                                                             "INTEGRATED_AND_SUPPRESSED",
                                                             "SUPPRESSED_AND_REACTIVATED",
                                                             "FILED_AS_ATTACHMENT",
                                                             "INTERNAL_TRANSFER"
                                                             ],
                                       "rejected_status": ["REJECTED"]
                                       }
            for outcomes in different_outcomes_list.values():
                for idx, outcome in enumerate(outcomes):
                    index.submit(
                        json.dumps(
                            create_sample_event(
                                f'ehr_integrations_{outcome}',
                                registration_event_datetime=create_date_time(report_start.replace(day=idx + 1),
                                                                             "08:00:00"),
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
                'gp2gp_rejected_trending_report/'
                'gp2gp_rejected_report_trending_count')

            test_query = set_variables_on_query(test_query, {
                "$index$": index_name,
                "$start_time$": report_start.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "$end_time$": report_end.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "$cutoff$": cutoff,
                "$time_period$": time_period
            })

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service)
            self.LOG.info(f'telemetry: {telemetry}')

            # Assert
            expected_values = expected_output

            for row, row_values in expected_values.items():
                row_values_as_jq_str = ' '.join(
                    [f"| select(.\"{key}\"==\"{value}\") " for key, value in row_values.items()]
                )
                self.LOG.info(f'.[{row}] {row_values_as_jq_str} ')
                assert jq.first(
                    f'.[{row}] {row_values_as_jq_str} ', telemetry)

        finally:
            self.delete_index(index_name)

    @pytest.mark.parametrize("time_period, expected_output", [
        ("month", {"0": {"time_period": "23-10",
                         "Not rejected": "83.33",
                         "Rejected": "16.67"
                         }
                   }
         ),
        ("week", {"0": {"time_period": "23-10-39",
                        "Not rejected": "50.00",
                        "Rejected": "50.00"
                        },
                  "1": {"time_period": "23-10-40",
                        "Not rejected": "100.00",
                        "Rejected": "0.00"
                        },
                  }
         ),
        ("day", {"0": {"time_period": "23-10-01",
                       "Not rejected": "50.00",
                       "Rejected": "50.00"
                       },
                 "1": {"time_period": "23-10-02",
                       "Not rejected": "100.00",
                       "Rejected": "0.00"
                       },
                 "2": {"time_period": "23-10-03",
                       "Not rejected": "100.00",
                       "Rejected": "0.00"
                       },
                 "3": {"time_period": "23-10-04",
                       "Not rejected": "100.00",
                       "Rejected": "0.00"
                       },
                 "4": {"time_period": "23-10-05",
                       "Not rejected": "100.00",
                       "Rejected": "0.00"
                       },
                 }
         ),
    ])
    def test_gp2gp_successfully_integrated_report_trending_percentage(self, time_period, expected_output):

        # Arrange
        index_name, index = self.create_index()

        # reporting window
        report_start = datetime.datetime(year=2023, month=10, day=1)
        report_end = datetime.datetime(year=2023, month=10, day=31)
        cutoff = "0"

        try:
            different_outcomes_list = {"successful_status": ["INTEGRATED",
                                                             "INTEGRATED_AND_SUPPRESSED",
                                                             "SUPPRESSED_AND_REACTIVATED",
                                                             "FILED_AS_ATTACHMENT",
                                                             "INTERNAL_TRANSFER"
                                                             ],
                                       "rejected_status": ["REJECTED"]
                                       }
            for outcomes in different_outcomes_list.values():
                for idx, outcome in enumerate(outcomes):
                    index.submit(
                        json.dumps(
                            create_sample_event(
                                f'ehr_integrations_{outcome}',
                                registration_event_datetime=create_date_time(report_start.replace(day=idx + 1),
                                                                             "08:00:00"),
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
                'gp2gp_rejected_trending_report/'
                'gp2gp_rejected_report_trending_percentage')

            test_query = set_variables_on_query(test_query, {
                "$index$": index_name,
                "$start_time$": report_start.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "$end_time$": report_end.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "$cutoff$": cutoff,
                "$time_period$": time_period
            })

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service)
            self.LOG.info(f'telemetry: {telemetry}')

            # Assert
            expected_values = expected_output

            for row, row_values in expected_values.items():
                row_values_as_jq_str = ' '.join(
                    [f"| select(.\"{key}\"==\"{value}\") " for key, value in row_values.items()]
                )
                self.LOG.info(f'.[{row}] {row_values_as_jq_str} ')
                assert jq.first(
                    f'.[{row}] {row_values_as_jq_str} ', telemetry)

        finally:
            self.delete_index(index_name)
