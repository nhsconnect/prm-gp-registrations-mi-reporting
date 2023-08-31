""" Helper for use with splunk API ."""
import os
import uuid
from time import sleep
from splunklib.binding import HTTPError
import splunklib.results as results
from jinja2 import Environment, FileSystemLoader
import random


def get_telemetry_from_splunk(search_query, service) -> None:
    try:
        service.parse(search_query, parse_only=True)
    except HTTPError as error:
        print(f"query '{search_query}' is invalid:\n\t{str(error)}", 2)
        return

    job = service.jobs.create(
        search_query,
        earliest_time="-3y@d",
        latest_time="+3y@d",
    )
    while True:
        while not job.is_ready():
            pass
        stats = {
            "isDone": job["isDone"],
            "doneProgress": job["doneProgress"],
            "scanCount": job["scanCount"],
            "eventCount": job["eventCount"],
            "resultCount": job["resultCount"],
        }
        if stats["isDone"] == "1":
            break
        sleep(2)
    rr = results.JSONResultsReader(job.results(output_mode="json"))
    telemetry = []
    for result in rr:
        if isinstance(result, results.Message):
            print(result.type, result.message)
        elif isinstance(result, dict):
            telemetry.append(result)
    job.cancel()
    return telemetry


def create_ehr_response_payload(
    ehrStructuredSizeBytes: int = 4096, number_of_placeholders: int = 0
) -> dict:
    placeholders = []

    clinical_type_list = [
        "SCANNED_DOCUMENT",
        "ORIGINAL_TEXT_DOCUMENT",
        "OCR_TEXT_DOCUMENT",
        "IMAGE",
        "AUDIO_DICTATION",
        "OTHER_AUDIO",
        "OTHER_DIGITAL_SIGNAL",
        "EDI_MESSAGE",
        "NOT_AVAILABLE",
        "OTHER",
    ]
    generated_by_list = ["SENDER", "PRE_EXISTING"]
    original_mime_type_list = ["audio/mpeg", "image/jpeg", "application/pdf"]
    reasons_list = [
        "FILE_TYPE_UNSUPPORTED",
        "FILE_DELETED",
        "FILE_NOT_FOUND",
        "FILE_LOCKED",
        "UNABLE_TO_DETERMINE_PROBLEM",
    ]

    for i in range(number_of_placeholders):
        placeholders.append(
            {
                "generatedBy": random.choice(generated_by_list),
                "clinicalType": random.choice(clinical_type_list),
                "reason": random.choice(reasons_list),
                "originalMimeType": random.choice(original_mime_type_list),
            }
        )

    return {
        "ehr": {
            "ehrStructuredSizeBytes": ehrStructuredSizeBytes,
            "placeholders": placeholders,
        }
    }

def create_document_response_payload(successful: bool, size_bytes: int = 4096) -> dict:
    clinical_type_list = [
        "SCANNED_DOCUMENT",
        "ORIGINAL_TEXT_DOCUMENT",
        "OCR_TEXT_DOCUMENT",
        "IMAGE",
        "AUDIO_DICTATION",
        "OTHER_AUDIO",
        "OTHER_DIGITAL_SIGNAL",
        "EDI_MESSAGE",
        "NOT_AVAILABLE",
        "OTHER",
    ]
    original_mime_type_list = ["audio/mpeg", "image/jpeg", "application/pdf"]
    reasons_list = [
        "FILE_TYPE_UNSUPPORTED",
        "FILE_DELETED",
        "FILE_NOT_FOUND",
        "FILE_LOCKED",
        "UNABLE_TO_DETERMINE_PROBLEM",
    ]


    return {
        "attachment": {
            "MimeType": random.choice(original_mime_type_list),
            "clinicalType": random.choice(clinical_type_list),
            "sizeBytes": size_bytes
        },
        "documentMigration": {
            "reason": random.choice(reasons_list),
            "successful": successful
        }
    }

def create_integration_payload(outcome=None) -> dict:
    return {"integration": {"outcome": outcome}}


def create_transfer_compatibility_payload(
    internalTransfer: bool, transferCompatible: bool, reason: str = None
) -> dict:
    return {
        "transferCompatibilityStatus": {
            "internalTransfer": internalTransfer,
            "transferCompatible": transferCompatible,
            "reason": reason,
        }
    }


def create_error_payload(
    errorCode: str, errorDescription: str, failurePoint: str
) -> dict:
    return {
        "error": {
            "errorCode": errorCode,
            "errorDescription": errorDescription,
            "failurePoint": failurePoint,
        }
    }


def create_registration_payload(
    returningPatient: bool = False,
    multifactorAuthenticationPresent: bool = True,
    dtsMatched: bool = True,
) -> dict:
    return {
        "registration": {
            "type": "NEW_GP_REGISTRATION",
            "returningPatient": returningPatient,
            "multifactorAuthenticationPresent": multifactorAuthenticationPresent,
        },
        "demographicTraceStatus": {
            "matched": dtsMatched,
            "reason": "no PDS trace results returned",
            "multifactorAuthenticationPresent": True,
        },
        "gpLinks": {"gpLinksComplete": True},
    }


def create_sample_event(
    conversation_id=str(uuid.uuid4()),
    registration_event_datetime="2023-03-10T12:53:01",
    event_type="READY_TO_INTEGRATE_STATUSES",
    payload=None,
    requestingSupplierName="TEST_SUPPLIER",
    sendingSupplierName="TEST_SUPPLIER2",
    reportingSystemSupplier="TEST_SYSTEM_SUPPLIER"
) -> dict:
    return {
        "eventId": str(uuid.uuid4()),
        "eventGeneratedDateTime": "2023-03-20T12:53:01",
        "eventType": event_type,
        "reportingSystemSupplier": reportingSystemSupplier,
        "reportingPracticeOdsCode": "A00029",
        "requestingPracticeOdsCode": "A00029",
        "requestingPracticeName": "GP A",
        "requestingPracticeIcbOdsCode": None,
        "requestingPracticeIcbName": None,
        "sendingPracticeOdsCode": "B00157",
        "sendingPracticeName": "GP B",
        "sendingPracticeIcbOdsCode": None,
        "sendingPracticeIcbName": None,
        "conversationId": conversation_id,
        "registrationEventDateTime": registration_event_datetime,
        "payload": payload,
        "requestingSupplierName": requestingSupplierName,
        "sendingSupplierName": sendingSupplierName,
    }


def get_or_create_index(index_id, service):
    if index_id in service.indexes:
        return service.indexes[index_id]

    return service.indexes.create(index_id)


def set_variables_on_query(search_query, variables):
    # result = re.sub(r'index=[^|\s]+', f'index={index}', search_query)
    result = search_query
    for key in variables:
        result = result.replace(key, variables[key])
    return result


def generate_splunk_query_from_report(self, report_name):
    path = os.path.join(os.path.dirname(__file__), "../reports")
    env = Environment(loader=FileSystemLoader(path))
    template = env.get_template(f"{report_name}.splunk")

    # using with statement
    with open("splunk_query", "w") as file:
        file.write(template.render())

    return template.render()
