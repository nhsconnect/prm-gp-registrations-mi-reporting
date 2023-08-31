from faker import Faker
from faker.providers import BaseProvider
from ..events_helper_provider import EventsHelperProvider
from datetime import datetime
from tests.test_base import EventType
import json


class Event:
    def __init__(self, EventType):
        self._fake = Faker()
        self._fake.add_provider(EventsHelperProvider)

        self._conversationId = self._fake.uuid4()
        self._eventGeneratedDateTime = datetime.utcnow().isoformat()
        self._eventType = EventType
        self._reportingSystemSupplier = self._fake.random_supplier_ods_code()
        self._reportingPracticeOdsCode = self._fake.random_practice_ods_code()
        self._requestingPracticeOdsCode = self._fake.random_practice_ods_code()
        self._requestingPracticeName = self._fake.random_practice_name()
        self._requestingPracticeIcbOdsCode = None
        self._requestingPracticeIcbName= None
        self._requestingSupplierName = self._reportingSystemSupplier
        self._sendingPracticeOdsCode = self._fake.random_practice_ods_code()
        self._sendingPracticeName = self._fake.random_practice_name()
        self._sendingPracticeIcbOdsCode = None
        self._sendingPracticeIcbName=None
        self._sendingSupplierName =  self._fake.random_supplier_ods_code()
        self._registrationEventDateTime = datetime.utcnow().isoformat()
        self._payload = self._fake.generate_payload(EventType) 


    @property
    def conversationId(self):
        return self._conversationId

    @property
    def eventGeneratedDateTime(self):
        return self._eventGeneratedDateTime
    
    @property
    def reportingSystemSupplier(self):
        return self._reportingSystemSupplier
    
    @property
    def reportingPracticeOdsCode(self):
        return self._reportingPracticeOdsCode
    
    @property
    def requestingPracticeOdsCode(self):
        return self._requestingPracticeOdsCode
    
    @property
    def requestingPracticeName(self):
        return self._requestingPracticeName
    
    @property
    def requestingPracticeIcbOdsCode(self):
        return self._requestingPracticeIcbOdsCode
    
    @property
    def requestingPracticeIcbName(self):
        return self._requestingPracticeIcbName

    @property
    def eventType(self):
        return self._eventType
    
    @property
    def requestingSupplierName(self):
        return self._requestingSupplierName
    
    @property
    def sendingPracticeOdsCode(self):
        return self._sendingPracticeOdsCode
    
    @property
    def sendingPracticeName(self):
        return self._sendingPracticeName

    @property
    def sendingPracticeIcbOdsCode(self):
        return self._sendingPracticeIcbOdsCode
    
    @property
    def sendingPracticeIcbName(self):
        return self._sendingPracticeIcbName
    
    @property
    def sendingSupplierName(self):
        return self._sendingSupplierName
    
    @property
    def registrationEventDateTime(self):
        return self._registrationEventDateTime
    
    @property
    def payload(self):
        return self._payload

    def get_json(self):     
     
     
     return {
            "conversationId": self.conversationId,            
            "eventGeneratedDateTime": self.eventGeneratedDateTime,
            'eventType': self.eventType.value,
            'reportingSystemSupplier': self.reportingSystemSupplier,
            'reportingPracticeOdsCode': self.reportingPracticeOdsCode,
            'requestingPracticeOdsCode': self.requestingPracticeOdsCode,
            'requestingPracticeName': self.requestingPracticeName,
            'requestingPracticeIcbOdsCode':self.requestingPracticeIcbOdsCode,
            'requestingPracticeIcbName':self.requestingPracticeIcbName,
            'requestingPracticeIcbName':self.requestingPracticeIcbName,
            'sendingPracticeOdsCode':self.sendingPracticeOdsCode,
            'sendingPracticeName':self.sendingPracticeName,
            'sendingPracticeIcbOdsCode':self.sendingPracticeIcbOdsCode,
            'sendingPracticeIcbName':self.sendingPracticeIcbName,
            'conversationId':self.conversationId,
            'registrationEventDateTime': self.registrationEventDateTime,
            'payload':self.payload
        }

       


class RegistrationsEvent(Event, BaseProvider):
    def __init__(self):
        Event.__init__(self, EventType.REGISTRATIONS)       
     

    def get_json(self):
        
        base_json = super().get_json()

        # print(f"base json: {base_json}")
        # base_json.update({"foo": "bar"})

        return base_json

class ReadyToIntegrateStatusesEvent(Event, BaseProvider):

    def __init__(self):
        Event.__init__(self, EventType.READY_TO_INTEGRATE_STATUSES)    
    
class EhrIntegrationsEvent(Event, BaseProvider):

    def __init__(self):
        Event.__init__(self, EventType.EHR_INTEGRATIONS)

class ErrorsEvent(Event, BaseProvider):

    def __init__(self):
        Event.__init__(self, EventType.ERRORS)

class EhrResponsesEvent(Event, BaseProvider):

    def __init__(self):
        Event.__init__(self, EventType.EHR_RESPONSES)

class EhrRequestsEvent(Event, BaseProvider):

    def __init__(self):
        Event.__init__(self, EventType.EHR_REQUESTS)

class TransferCompatibilityStatusesEvent(Event, BaseProvider):

    def __init__(self):
        Event.__init__(self, EventType.TRANSFER_COMPATIBILITY_STATUSES)

