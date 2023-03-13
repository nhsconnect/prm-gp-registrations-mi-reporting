import os
import json
import os
from time import sleep
import uuid
from splunklib.binding import HTTPError
from splunklib import client
import splunklib.results as results
import jq
import re

splunk_token = os.environ['SPLUNK_TOKEN']
splunk_host = os.environ.get('SPLUNK_HOST')

service = client.connect(token=splunk_token)


def teardown_function():
    service.indexes.delete("test_index")


def test_reporting_window_then_return_event_within():
    index = get_or_create_index("test_index")

    index.submit(
        json.dumps(
            create_sample_event(
                conversationId = "WITHIN_REPORT_WINDOW",
                registrationEventDateTime = "2023-03-10T00:00:00"
            )),
            sourcetype="myevent")
    index.submit(
        json.dumps(
            create_sample_event(
                conversationId = "OUTSIDE_REPORT_WINDOW",
                registrationEventDateTime = "2023-03-20T00:00:00"
            )),
            sourcetype="myevent")

    test_query = get_search('gp2gp_reporting_window')
    test_query = set_variables_on_query(test_query, "test_index", {
        "$cutoff$": "2",
        "$report_start$": "2023-03-09",
        "$report_end$": "2023-03-11"
    })
    print(test_query)

    telemetry = get_telemetry_from_splunk(test_query)
    
    assert len(telemetry) == 1
    assert jq.first('.[]._raw | fromjson.conversationId', telemetry) == 'WITHIN_REPORT_WINDOW'


def get_search(search_name):
    path = os.path.join(os.path.dirname(__file__), '../queries', f'{search_name}.splunk')
    return open(path).read()


def create_sample_event(
        conversationId=str(uuid.uuid4()),
        registrationEventDateTime="2023-03-10T12:53:01"
    ):
    return {
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
        "conversationId":conversationId,
        "registrationEventDateTime":registrationEventDateTime,
        "payload":None
    }


def get_or_create_index(index_id):
    if index_id in service.indexes:
        return service.indexes[index_id]
   
    return service.indexes.create(index_id)


def set_variables_on_query(search_query, index, vars):
    result = re.sub(r'index=[^|\s]+', f'index={index}', search_query)
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