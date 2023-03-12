import os
import json
import os
from time import sleep
import uuid
from splunklib.binding import HTTPError
from splunklib import client
import splunklib.results as results

splunk_token = os.environ['SPLUNK_TOKEN']
splunk_host = os.environ.get('SPLUNK_HOST')

service = client.connect(token=splunk_token)

def test_reporting_window_then_return_event_within():
    path = os.path.join(os.path.dirname(__file__), '../queries', 'gp2gp_reporting_window.splunk')
    index = get_or_create_index("test_index")

    example_events = [{
        "eventId":str(uuid.uuid4()),
        "eventGeneratedDateTime":"2023-03-10T12:53:01",
        "eventType":"READY_TO_INTEGRATE_STATUSES",
        "reportingSystemSupplier":"200000000260",
        "reportingPracticeOdsCode":"A00029",
        "requestingPracticeOdsCode":"A00029",
        "requestingPracticeName":"GP A",
        "requestingPracticeIcbOdsCode":None,
        "requestingPracticeIcbName":None,
        "sendingPracticeOdsCode":"B00157",
        "sendingPracticeName":"GP B",
        "sendingPracticeIcbOdsCode":None,
        "sendingPracticeIcbName":None,
        "conversationId":"WITHIN_REPORT_WINDOW",
        "registrationEventDateTime":"2023-03-10T12:53:01",
        "payload":None
    }, {
        "eventId":str(uuid.uuid4()),
        "eventGeneratedDateTime":"2023-03-20T12:53:01",
        "eventType":"READY_TO_INTEGRATE_STATUSES",
        "reportingSystemSupplier":"200000000260",
        "reportingPracticeOdsCode":"A00029",
        "requestingPracticeOdsCode":"A00029",
        "requestingPracticeName":"GP A",
        "requestingPracticeIcbOdsCode":None,
        "requestingPracticeIcbName":None,
        "sendingPracticeOdsCode":"B00157",
        "sendingPracticeName":"GP B",
        "sendingPracticeIcbOdsCode":None,
        "sendingPracticeIcbName":None,
        "conversationId":"OUTSIDE_REPORT_WINDOW",
        "registrationEventDateTime":"2023-03-10T12:53:01",
        "payload":None
    }]
    for event in example_events:
        index.submit(json.dumps(event), sourcetype="myevent")

    test_query = open(path).read()
    test_query = set_variables_on_query(test_query, {
        "$cutoff$": "2",
        "$report_start$": "2023-03-09",
        "$report_end$": "2023-03-11"
    })

    telemetry = get_telemetry_from_splunk(test_query)

    service.indexes.delete("test_index")
    
    assert len(telemetry) == 1


def get_or_create_index(index_id):
    if index_id in service.indexes:
        return service.indexes[index_id]
   
    return service.indexes.create(index_id)


def set_variables_on_query(search_query, vars):
    result = search_query
    for key in vars:
        result = result.replace(key, vars[key])
    return result


def get_telemetry_from_splunk(search_query):
    try:
        service.parse(search_query, parse_only=True)
    except HTTPError as e:
        print(f"query '{search_query}' is invalid:\n\t{str(e)}", 2)
        return
    
    job = service.jobs.create(search_query,
        earliest_time="-6w@w",
        latest_time="@w",
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