import argparse
from tests.faker.providers.conversation import Conversation
from tests.faker.providers.events.event_factory import (
    RegistrationsEvent,
    ErrorsEvent,
    TransferCompatibilityStatusesEvent,
)
from tests.test_base import EventType
import json


ap = argparse.ArgumentParser()
ap.add_argument(
    "-c", "--conversations", required=True, help="number of conversations to generate"
)
ap.add_argument(
    "-er",
    "--error_registrations",
    required=False,
    help="number to stop at REGISTRAION with errors?",
)

ap.add_argument(
    "-etc",
    "--error_trans_compat",
    required=False,
    help="number to stop at TRANSFER_COMPATIBILITY_STATUSES with errors?",
)

args = vars(ap.parse_args())

print(f"Args:{args}")
# -------------------------------

number_of_conversations = int(args["conversations"])
error_registrations = int(args["error_registrations"])
error_transfer_compatibility_statuses = int(args["error_trans_compat"])


conversations = []

for i in range(number_of_conversations):
    # create a new conversation with generates a conversationId and a list to hold all the events for that conversation.
    conversation = Conversation()

    # add to conversations collection
    conversations.append(conversation)

    # get new conversation_id so that events created as part of this conversation all have the same conversation id
    conversation_id = conversation.Id

    # create the first event - REGISTRATION
    registraions_event = RegistrationsEvent(conversation_id)
    conversation.Events.append(registraions_event)

    if error_registrations > 0:
        registration_error = ErrorsEvent.Create(
            conversation_id=conversation_id, failure_point=EventType.REGISTRATIONS
        )
        error_registrations -= 1
        conversation.Events.append(registration_error)
        continue

    # create the next event - TRANSFER_COMPATIBILITY_STATUSES
    transfer_compat_status_event = TransferCompatibilityStatusesEvent(
        conversation_id=conversation_id
    )

    conversation.Events.append(transfer_compat_status_event)

    if error_transfer_compatibility_statuses > 0:
        transfer_compatibility_statuses_error = ErrorsEvent.Create(
            conversation_id=conversation_id,
            failure_point=EventType.TRANSFER_COMPATIBILITY_STATUSES,
        )
        error_transfer_compatibility_statuses -= 1
        conversation.Events.append(transfer_compatibility_statuses_error)
        continue




    
for i, value in enumerate(conversations):

    events = value.Events

    for y, event in enumerate(events):
        print(f'Conversaion: {i}, Event: {y} EventType: {event.eventType}')

