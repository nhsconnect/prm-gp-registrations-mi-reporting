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


class TestInProgressSlaSnapshotGraph(TestBase):
    def in_flight(self):       

        # Arrange
        index_name, index = self.create_index()

        # reporting window
        report_start = generate_report_start_date()
        report_end = generate_report_end_date()
        cutoff = "0"

        try:
            index.submit(
                json.dumps(
                    create_sample_event(
                        "test_in_flight",
                        registration_event_datetime=create_date_time(
                            report_start, "05:00:00"
                        ),
                        event_type=EventType.EHR_REQUESTS.value,
                        sendingSupplierName="EMIS",
                        requestingSupplierName="TPP",
                        payload=create_transfer_compatibility_payload(
                            internalTransfer=False,
                            transferCompatible=True,
                            reason="test_in_flight",
                        ),
                    )
                ),
                sourcetype="myevent",
            )

            # Act
            test_query = self.generate_splunk_query_from_report(
                "gp2gp_in_progress_sla_snapshot_report/gp2gp_in_progress_sla_snapshot_report_base"
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
            expected_values = {"in-flight": "1"}

            for idx, (key, value) in enumerate(expected_values.items()):
                assert jq.first(
                    f'.[{idx}] | select( .label=="{key}") | select (.count=="{value}")',
                    telemetry,
                )

        finally:
            self.delete_index(index_name)
