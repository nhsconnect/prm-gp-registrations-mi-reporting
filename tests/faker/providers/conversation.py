from faker import Faker


class Conversation:   

    def __init__(self):   
        self._fake = Faker()

        self._conversationId = self._fake.uuid4()
        self._events = []

    @property
    def Id(self):
        return self._conversationId

    @property
    def Events(self):
        return self._events

    
