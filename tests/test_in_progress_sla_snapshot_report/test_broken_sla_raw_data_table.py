import pytest
import json
import uuid
from datetime import timedelta, date
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


class TestInProgressSlaRawDataTable(TestBase):

    @pytest.mark.parametrize("column",
                             [
                                 "B24",
                                 "B24 + BEhrR",
                                 "B24 + BEhrS",
                                 "B24 + BEhrS + BEhrR",
                                 "BEhrR",
                                 "BEhrS",
                                 "BEhrS + BEhrR",
                                 "IF",
                             ])
    def test_in_progress_sla_raw_data_table_output(self, column):
        """
        Tests the output as requested for the in-progress 24hr sla raw data table
        """

        # reporting window
        report_start = date.today() - timedelta(days=1)
        report_end = generate_report_end_date()
        cutoff = "0"

        try:

            # Arrange
            index_name, index = self.create_index()

            conversation_id = "none"

            # in-progress
            if column == "IF":
                in_flight_conversation_id = "test_in_flight"
                conversation_id = in_flight_conversation_id

                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id=in_flight_conversation_id,
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

                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id=in_flight_conversation_id,
                            registration_event_datetime=(
                                    datetime_utc_now() - timedelta(minutes=5)
                            ).strftime("%Y-%m-%dT%H:%M:%S%z"),
                            event_type=EventType.EHR_REQUESTS.value,
                            sendingSupplierName="EMIS",
                            requestingSupplierName="TPP"
                        )
                    ),
                    sourcetype="myevent",
                )

                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id=in_flight_conversation_id,
                            registration_event_datetime=(
                                    datetime_utc_now() - timedelta(minutes=4)
                            ).strftime("%Y-%m-%dT%H:%M:%S%z"),
                            event_type=EventType.EHR_RESPONSES.value,
                            sendingSupplierName="EMIS",
                            requestingSupplierName="TPP",
                        )
                    ),
                    sourcetype="myevent",
                )
            elif column == "B24":
                broken_24hr_sla_conversation_id = "test_broken_24hr_sla"
                conversation_id = broken_24hr_sla_conversation_id

                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id=broken_24hr_sla_conversation_id,
                            registration_event_datetime=(
                                    datetime_utc_now() - timedelta(hours=25)
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
                            conversation_id=broken_24hr_sla_conversation_id,
                            registration_event_datetime=(
                                    datetime_utc_now() - timedelta(hours=25)
                            ).strftime("%Y-%m-%dT%H:%M:%S%z"),
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

                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id=broken_24hr_sla_conversation_id,
                            registration_event_datetime=(
                                    datetime_utc_now() - timedelta(hours=25)
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
                            conversation_id=broken_24hr_sla_conversation_id,
                            registration_event_datetime=(datetime_utc_now()).strftime(
                                "%Y-%m-%dT%H:%M:%S%z"
                            ),
                            event_type=EventType.READY_TO_INTEGRATE_STATUSES.value,
                            sendingSupplierName="EMIS",
                            requestingSupplierName="TPP",
                        )
                    ),
                    sourcetype="myevent",
                )
            elif column == "BEhrS":
                broken_ehr_sending_outside_sla_conversation_id = (
                    "test_broken_ehr_sending_outside_sla"
                )
                conversation_id = broken_ehr_sending_outside_sla_conversation_id

                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id=broken_ehr_sending_outside_sla_conversation_id,
                            registration_event_datetime=(
                                    datetime_utc_now() - timedelta(minutes=25)
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
                            conversation_id=broken_ehr_sending_outside_sla_conversation_id,
                            registration_event_datetime=(
                                    datetime_utc_now() - timedelta(minutes=21)
                            ).strftime("%Y-%m-%dT%H:%M:%S%z"),
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

                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id=broken_ehr_sending_outside_sla_conversation_id,
                            registration_event_datetime=(datetime_utc_now()).strftime(
                                "%Y-%m-%dT%H:%M:%S%z"
                            ),
                            event_type=EventType.EHR_RESPONSES.value,
                            sendingSupplierName="EMIS",
                            requestingSupplierName="TPP",
                        )
                    ),
                    sourcetype="myevent",
                )
            elif column == "BEhrR":
                broken_ehr_requesting_sla_conversation_id = "broken_ehr_requesting_sla"
                conversation_id = broken_ehr_requesting_sla_conversation_id

                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id=broken_ehr_requesting_sla_conversation_id,
                            registration_event_datetime=(
                                    datetime_utc_now() - timedelta(minutes=21)
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
                            conversation_id=broken_ehr_requesting_sla_conversation_id,
                            registration_event_datetime=(datetime_utc_now()).strftime(
                                "%Y-%m-%dT%H:%M:%S%z"
                            ),
                            event_type=EventType.EHR_REQUESTS.value,
                            sendingSupplierName="EMIS",
                            requestingSupplierName="TPP",
                        )
                    ),
                    sourcetype="myevent",
                )
            elif column == "B24 + BEhrR":
                broken_24hr_and_ehr_requesting_sla_conversation_id = "test_broken_24hr_sla_and_ehr_requesting_sla"
                conversation_id = broken_24hr_and_ehr_requesting_sla_conversation_id

                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id=broken_24hr_and_ehr_requesting_sla_conversation_id,
                            registration_event_datetime=(
                                    datetime_utc_now() - timedelta(hours=25, minutes=21)
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
                            conversation_id=broken_24hr_and_ehr_requesting_sla_conversation_id,
                            registration_event_datetime=(
                                    datetime_utc_now() - timedelta(hours=25)
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
                            conversation_id=broken_24hr_and_ehr_requesting_sla_conversation_id,
                            registration_event_datetime=(
                                    datetime_utc_now() - timedelta(hours=25)
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
                            conversation_id=broken_24hr_and_ehr_requesting_sla_conversation_id,
                            registration_event_datetime=(datetime_utc_now()).strftime(
                                "%Y-%m-%dT%H:%M:%S%z"
                            ),
                            event_type=EventType.READY_TO_INTEGRATE_STATUSES.value,
                            sendingSupplierName="EMIS",
                            requestingSupplierName="TPP",
                        )
                    ),
                    sourcetype="myevent",
                )
            elif column == "B24 + BEhrS":
                broken_24hr_and_ehr_sending_sla_conversation_id = "test_broken_24hr_sla_and_ehr_sending_sla"
                conversation_id = broken_24hr_and_ehr_sending_sla_conversation_id

                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id=broken_24hr_and_ehr_sending_sla_conversation_id,
                            registration_event_datetime=(
                                    datetime_utc_now() - timedelta(hours=25, minutes=21)
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
                            conversation_id=broken_24hr_and_ehr_sending_sla_conversation_id,
                            registration_event_datetime=(
                                    datetime_utc_now() - timedelta(hours=25, minutes=21)
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
                            conversation_id=broken_24hr_and_ehr_sending_sla_conversation_id,
                            registration_event_datetime=(
                                    datetime_utc_now() - timedelta(hours=25)
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
                            conversation_id=broken_24hr_and_ehr_sending_sla_conversation_id,
                            registration_event_datetime=(datetime_utc_now()).strftime(
                                "%Y-%m-%dT%H:%M:%S%z"
                            ),
                            event_type=EventType.READY_TO_INTEGRATE_STATUSES.value,
                            sendingSupplierName="EMIS",
                            requestingSupplierName="TPP",
                        )
                    ),
                    sourcetype="myevent",
                )
            elif column == "BEhrS + BEhrR":
                broken_ehr_sending_and_requesting_sla_conversation_id = "test_broken_ehr_sending_sla_and_ehr_requesting_sla"
                conversation_id = broken_ehr_sending_and_requesting_sla_conversation_id

                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id=broken_ehr_sending_and_requesting_sla_conversation_id,
                            registration_event_datetime=(
                                    datetime_utc_now() - timedelta(minutes=42)
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
                            conversation_id=broken_ehr_sending_and_requesting_sla_conversation_id,
                            registration_event_datetime=(
                                    datetime_utc_now() - timedelta(minutes=21)
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
                            conversation_id=broken_ehr_sending_and_requesting_sla_conversation_id,
                            registration_event_datetime=(
                                datetime_utc_now()
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
                            conversation_id=broken_ehr_sending_and_requesting_sla_conversation_id,
                            registration_event_datetime=(datetime_utc_now()).strftime(
                                "%Y-%m-%dT%H:%M:%S%z"
                            ),
                            event_type=EventType.READY_TO_INTEGRATE_STATUSES.value,
                            sendingSupplierName="EMIS",
                            requestingSupplierName="TPP",
                        )
                    ),
                    sourcetype="myevent",
                )
            elif column == "B24 + BEhrS + BEhrR":
                broken_all_slas_conversation_id = "test_broken_all_sla"
                conversation_id = broken_all_slas_conversation_id

                index.submit(
                    json.dumps(
                        create_sample_event(
                            conversation_id=broken_all_slas_conversation_id,
                            registration_event_datetime=(
                                    datetime_utc_now() - timedelta(hours=25, minutes=42)
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
                            conversation_id=broken_all_slas_conversation_id,
                            registration_event_datetime=(
                                    datetime_utc_now() - timedelta(hours=25, minutes=21)
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
                            conversation_id=broken_all_slas_conversation_id,
                            registration_event_datetime=(
                                    datetime_utc_now() - timedelta(hours=25)
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
                            conversation_id=broken_all_slas_conversation_id,
                            registration_event_datetime=(datetime_utc_now()).strftime(
                                "%Y-%m-%dT%H:%M:%S%z"
                            ),
                            event_type=EventType.READY_TO_INTEGRATE_STATUSES.value,
                            sendingSupplierName="EMIS",
                            requestingSupplierName="TPP",
                        )
                    ),
                    sourcetype="myevent",
                )

            # not eligible for transfer
            not_eligible_conv_id = "not_eligible_1"
            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=not_eligible_conv_id,
                        registration_event_datetime=(
                                datetime_utc_now() - timedelta(minutes=6)
                        ).strftime("%Y-%m-%dT%H:%M:%S%z"),
                        event_type=EventType.TRANSFER_COMPATIBILITY_STATUSES.value,
                        sendingSupplierName="EMIS",
                        requestingSupplierName="TPP",
                        payload=create_transfer_compatibility_payload(
                            internalTransfer=False,
                            transferCompatible=False,
                            reason="test",
                        ),
                    )
                ),
                sourcetype="myevent",
            )

            # technical failure
            tech_failure_conv_id = "tech_failure_1"

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=tech_failure_conv_id,
                        registration_event_datetime=(
                                datetime_utc_now() - timedelta(hours=25)
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
                        conversation_id=tech_failure_conv_id,
                        registration_event_datetime=(
                                datetime_utc_now() - timedelta(hours=25)
                        ).strftime("%Y-%m-%dT%H:%M:%S%z"),
                        event_type=EventType.ERRORS.value,
                        sendingSupplierName="EMIS",
                        requestingSupplierName="TPP",
                        payload=create_error_payload(
                            errorCode="99",
                            errorDescription="test",
                            failurePoint="EHR_SENT"
                        )
                    )
                ),
                sourcetype="myevent",
            )

            # Ready to integrate
            ready_to_integrate_id = "ready_to_integrate_1"
            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=ready_to_integrate_id,
                        registration_event_datetime=(
                            datetime_utc_now()
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
                        conversation_id=ready_to_integrate_id,
                        registration_event_datetime=(
                            datetime_utc_now()
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
                        conversation_id=ready_to_integrate_id,
                        registration_event_datetime=(
                            datetime_utc_now()
                        ).strftime("%Y-%m-%dT%H:%M:%S%z"),
                        event_type=EventType.EHR_RESPONSES.value,
                        sendingSupplierName="EMIS",
                        requestingSupplierName="TPP",
                        payload=create_ehr_response_payload()
                    )
                ),
                sourcetype="myevent",
            )

            index.submit(
                json.dumps(
                    create_sample_event(
                        conversation_id=ready_to_integrate_id,
                        registration_event_datetime=(
                            datetime_utc_now()
                        ).strftime(
                            "%Y-%m-%dT%H:%M:%S%z"
                        ),
                        event_type=EventType.READY_TO_INTEGRATE_STATUSES.value,
                        sendingSupplierName="EMIS",
                        requestingSupplierName="TPP",
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

            assert jq.all(
                f".[] "
                + f'| select( .conversation_id == "{conversation_id}") '
                + f'| select( .report_supplier_name == "TEST_SYSTEM_SUPPLIER")'
                + f'| select( .requesting_supplier_name == "TPP")'
                + f'| select( .sending_supplier_name == "EMIS")'
                + f'| select( .reporting_practice_ods_code == "A00029")'
                + f'| select( .requesting_practice_ods_code == "A00029")'
                + f'| select( .sending_practice_ods_code == "B00157")'
                , telemetry
            )
            assert len(telemetry) == 1

        finally:
            self.delete_index(index_name)
