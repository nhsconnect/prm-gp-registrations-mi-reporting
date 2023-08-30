from faker import Faker
from faker.providers import BaseProvider
from ..events_helper_provider import EventsHelperProvider
from datetime import datetime
from tests.test_base import EventType
import json


class RegistrationEvent(BaseProvider):   

    def __init__(self):
        
        fake = Faker()
        fake.add_provider(EventsHelperProvider)

        self.eventId = fake.uuid4()
        self.eventGeneratedDateTime = datetime.utcnow().isoformat()
        self.eventType = "REGISTRATIONS"
        self.reportingSystemSupplier = fake.random_supplier_ods_code()
        self.reportingPracticeOdsCode = fake.random_practice_ods_code()
        self.requestingPracticeOdsCode = fake.random_practice_ods_code()
        self.requestingPracticeName = fake.random_practice_name()
        self.requestingPracticeIcbOdsCode = None
        self.requestingPracticeIcbName = None
        self.sendingPracticeOdsCode = fake.random_practice_ods_code()
        self.sendingPracticeName = fake.random_practice_name()
        self.sendingPracticeIcbOdsCode = None
        self.sendingPracticeIcbName = None
        self.conversationId = fake.uuid4()
        self.registrationEventDateTime = datetime.utcnow().isoformat()
        self.payload = fake.generate_payload(EventType.REGISTRATIONS)
       

        # self.last_name = fake.last_name()
        # self.phone = random.randint(9000000000, 9999999999)
        # self.city = fake.city()
        # self.about = "This is a sample text : about"

    def get_json(self):   

        return json.dumps(self, default=lambda o: o.__dict__, 
            sort_keys=False, indent=4)    
    

        # return {
        #     'eventId': self.eventId,
        #     'eventGeneratedDateTime': self.eventGeneratedDateTime,
        #     'eventType': self.eventType,
        #     'reportingSystemSupplier': self.reportingSystemSupplier,
        #     'reportingPracticeOdsCode': self.reportingPracticeOdsCode,
        #     'requestingPracticeOdsCode': self.requestingPracticeOdsCode,
        #     'requestingPracticeName': self.requestingPracticeName,
        #     'requestingPracticeIcbOdsCode':self.requestingPracticeIcbOdsCode,
        #     'requestingPracticeIcbName':self.requestingPracticeIcbName,
        #     'requestingPracticeIcbName':self.requestingPracticeIcbName,
        #     'sendingPracticeOdsCode':self.sendingPracticeOdsCode,
        #     'sendingPracticeName':self.sendingPracticeName,
        #     'sendingPracticeIcbOdsCode':self.sendingPracticeIcbOdsCode,
        #     'sendingPracticeIcbName':self.sendingPracticeIcbName,
        #     'conversationId':self.conversationId,
        #     'registrationEventDateTime': self.registrationEventDateTime,
        #     'payload':self.payload
        # }   