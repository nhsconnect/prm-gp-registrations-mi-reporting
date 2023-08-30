from tests.faker.providers.events.registration_factory import RegistrationEvent


re = RegistrationEvent()

json = re.get_json()

print(f"Json: {json}")