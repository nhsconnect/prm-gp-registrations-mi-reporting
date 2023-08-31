import json
from tests.faker.providers.events.event_factory import RegistrationsEvent, ReadyToIntegrateStatusesEvent, EhrIntegrationsEvent,TransferCompatibilityStatusesEvent


# # RegistrationEvent
# re = RegistrationEvent()
# re_json = json.dumps(re.get_json(), indent = 4) 
# print(f"RegistrationEvent Json: {re_json}")

# # ReadyToIntegrateStatuses
# rti = ReadyToIntegrateStatuses()
# rti_json = rti.get_json();
# print(f"ReadyToIntegrateStatuses Json: {rti_json}")


# # EHR_INTEGRATIONS
# ehr_integ = EhrIntegrationsEvent()
# ehr_integ_json = json.dumps(ehr_integ.get_json(), indent = 4) 
# print(f"RegistrationEvent Json: {ehr_integ_json}")


#  Transfer Compatibility Statuses
event = TransferCompatibilityStatusesEvent()
json = json.dumps(event.get_json(), indent = 4) 
print(f"json: {json}")