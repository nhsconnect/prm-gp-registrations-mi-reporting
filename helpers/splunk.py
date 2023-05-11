""" Helper for use with splunk API ."""
import uuid
from time import sleep
from splunklib.binding import HTTPError
import splunklib.results as results


def get_telemetry_from_splunk(search_query, service) -> None:
    try:
        service.parse(search_query, parse_only=True)
    except HTTPError as error:
        print(f"query '{search_query}' is invalid:\n\t{str(error)}", 2)
        return

    job = service.jobs.create(search_query,
                              earliest_time="-3y@d",
                              latest_time="+3y@d",
                              )
    while True:
        while not job.is_ready():
            pass
        stats = {'isDone': job['isDone'],
                 'doneProgress': job['doneProgress'],
                 'scanCount': job['scanCount'],
                 'eventCount': job['eventCount'],
                 'resultCount': job['resultCount']}
        if stats['isDone'] == '1':
            break
        sleep(2)
    rr = results.JSONResultsReader(job.results(output_mode='json'))
    telemetry = []
    for result in rr:
        if isinstance(result, results.Message):
            print(result.type, result.message)
        elif isinstance(result, dict):
            telemetry.append(result)
    job.cancel()
    return telemetry


def create_integration_payload(outcome=None) -> dict:
    return {
        "integration": {
            "outcome": outcome
        }
    }


def create_transfer_compatibility_payload(internalTransfer: bool, transferCompatible: bool, reason: str = None) -> dict:
    return {
        "transferCompatibilityStatus": {
            "internalTransfer": internalTransfer,
            "transferCompatible": transferCompatible,
            "reason": reason
        }
    }


def create_error_payload(errorCode: str, errorDescription: str, failurePoint: str) -> dict:
    return {
        "error": {
            "errorCode": errorCode,
            "errorDescription": errorDescription,
            "failurePoint": failurePoint
        }
    }


def create_registration_payload(returningPatient: bool = False, multifactorAuthenticationPresent: bool = True, dtsMatched: bool = True) -> dict:
    return {
        "registration": {
            "type": "NEW_GP_REGISTRATION",
            "returningPatient": returningPatient,
            "multifactorAuthenticationPresent": multifactorAuthenticationPresent
        },
        "demographicTraceStatus": {
            "matched": dtsMatched,
            "reason": "no PDS trace results returned",
            "multifactorAuthenticationPresent": True
        },
        "gpLinks": {
            "gpLinksComplete": True
        }
    }


def create_sample_event(
    conversation_id=str(uuid.uuid4()),
    registration_event_datetime="2023-03-10T12:53:01",
    event_type="READY_TO_INTEGRATE_STATUSES",
    payload=None,
    requestingPracticeSupplierName="TEST_SUPPLIER",
    sendingPracticeSupplierName="TEST_SUPPLIER2"
) -> dict:
    return {
        "eventId": str(uuid.uuid4()),
        "eventGeneratedDateTime": "2023-03-20T12:53:01",
        "eventType": event_type,
        "reportingSystemSupplier": "200000000260",
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
        "requestingPracticeSupplierName": requestingPracticeSupplierName,
        "sendingPracticeSupplierName": sendingPracticeSupplierName
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
