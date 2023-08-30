from tests.faker.providers.events.event_factory import RegistrationEvent, ReadyToIntegrateStatuses

# RegistrationEvent
re = RegistrationEvent()
re_json = re.get_json()
print(f"RegistrationEvent Json: {re_json}")

# # ReadyToIntegrateStatuses
# rti = ReadyToIntegrateStatuses()
# rti_json = rti.get_json();
# print(f"ReadyToIntegrateStatuses Json: {rti_json}")