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
                            set_variables_on_query)
from tests.test_base import EventType, TestBase


class TestInProgressSlaRawDataTable(TestBase):

    @pytest.mark.parametrize("column",["In flight", "Broken 24hr sla", "Broken ehr sending sla", "Broken ehr requesting sla"])   
    def test_in_progress_sla_raw_data_table_output(self, column):
        """
        Tests the output as requested for the in-progress 24hr sla raw data table
        """

        # reporting window
        report_start = generate_report_start_date()
        report_end = generate_report_end_date()
        cutoff = "0"

        try:            

            # Arrange
            index_name, index = self.create_index()
            

            random_conversation_id = f"test_placeholder_graph_{uuid.uuid4()}"
            

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=random_conversation_id,
                        registration_event_datetime=(
                            datetime_utc_now() - timedelta(minutes=6)
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

            # Act
            test_query = self.generate_splunk_query_from_report(
                "gp2gp_in_progress_sla_snapshot_report/"
                "gp2gp_in_progress_sla_snapshot_report_in_progress_sla_raw_data_table"
            )

            test_query = set_variables_on_query(
                test_query,
                {
                    "$index$": index_name,
                    "$start_time$": report_start.strftime("%Y-%m-%dT%H:%m:%s"),
                    "$end_time$": report_end.strftime("%Y-%m-%dT%H:%m:%s"),
                    "$cutoff$": cutoff,
                    "$column$": column
                },
            )

            sleep(2)

            telemetry = get_telemetry_from_splunk(
                self.savedsearch(test_query), self.splunk_service
            )
            self.LOG.info(f"telemetry: {telemetry}")

            # Assert

            if column =="In flight":             

                assert jq.all(
                    f".[0] "
                    + f'| select( .conversation_id == "{random_conversation_id}") '
                    + f'| select( .requesting_supplier_name == "TPP") '  
                    + f'| select( .reporting_practice_ods_code == "A00029") ' 
                    + f'| select( .requesting_practice_ods_code == "A00029") ' 
                    + f'| select( .sending_practice_ods_code == "B00157") '
                    ,telemetry
                )
            else:
                assert telemetry== []

        finally:
            self.delete_index(index_name)

    