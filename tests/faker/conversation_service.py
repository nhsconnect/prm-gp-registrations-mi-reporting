from tests.faker.conversation import Conversation
from tests.faker.events import (
    Event,
    RegistrationsEvent,
    ErrorsEvent,
    TransferCompatibilityStatusesEvent,
    EhrRequestsEvent,
    EhrResponsesEvent,
    EhrIntegrationsEvent,
    ReadyToIntegrateStatusesEvent,
)
from tests.test_base import EventType

import json
from uuid import uuid4


class ConversationService:
    def generate_conversations(
        self,
        number_of_conversations: int,
        number_to_error_at_registrations: int,
        number_to_error_at_transfer_compatibility_statuses: int,
        number_to_error_at_ehr_request: int,
        number_to_error_at_ehr_response: int,
        number_to_error_at_ready_to_integrate: int,
        number_to_error_at_integration: int,
    ):
        conversations = []

        for i in range(number_of_conversations):
            # create a new conversation with generates a conversationId and a list to hold all the events for that conversation.
            conversation = Conversation()

            # add to conversations collection
            conversations.append(conversation)

            # create the first event - REGISTRATION
            (
                reg_event,
                reg_error_event,
                number_to_error_at_registrations,
            ) = self._generate_events(
                EventType.REGISTRATIONS, conversation, number_to_error_at_registrations
            )

            if reg_error_event is not None:
                continue

            # create the next event - TRANSFER_COMPATIBILITY_STATUSES
            (
                trans_compat_event,
                trans_compat_error_event,
                number_to_error_at_transfer_compatibility_statuses,
            ) = self._generate_events(
                EventType.TRANSFER_COMPATIBILITY_STATUSES,
                conversation,
                number_to_error_at_transfer_compatibility_statuses,
            )
            if trans_compat_error_event is not None:
                continue

            # create the next event - EHR_REQUESTS
            (
                ehr_request_event,
                ehr_request_error_event,
                number_to_error_at_ehr_request,
            ) = self._generate_events(
                event_type=EventType.EHR_REQUESTS,
                conversation=conversation,
                error_counter=number_to_error_at_ehr_request,
            )
            if ehr_request_error_event is not None:
                continue

            # create the next event - EHR_RESPONSES
            (
                ehr_response_event,
                ehr_response_error,
                number_to_error_at_ehr_response,
            ) = self._generate_events(
                event_type=EventType.EHR_RESPONSES,
                conversation=conversation,
                error_counter=number_to_error_at_ehr_response,
            )

            if ehr_response_error is not None:
                continue

            # create the next event - READY_TO_INTEGRATE_STATUSES
            (
                ready_to_integrate_event,
                ready_to_integrate_error_event,
                number_to_error_at_ready_to_integrate,
            ) = self._generate_events(
                event_type=EventType.READY_TO_INTEGRATE_STATUSES,
                conversation=conversation,
                error_counter=number_to_error_at_ready_to_integrate,
            )

            if ready_to_integrate_error_event is not None:
                continue

            # create the next event - EHR_INTEGRATIONS
            (
                integration_event,
                integration_error,
                number_to_error_at_integration,
            ) = self._generate_events(
                event_type=EventType.EHR_INTEGRATIONS,
                conversation=conversation,
                error_counter=number_to_error_at_integration,
            )

            if not integration_error is None:
                integration_event.payload["integration"][
                    "outcome"
                ] = "FAILED_TO_INTEGRATE"
                continue

        return conversations

    def _generate_events(
        self, event_type: EventType, conversation: Conversation, error_counter: int
    ) -> Event:
        new_event = self._generate_event_from_type(
            event_type=event_type, conversation_id=conversation.Id
        )

        conversation.Events.append(new_event)

        # generate an error event if number_to_error_at_* is not zero.
        error_event = None

        if error_counter > 0:
            error_event = ErrorsEvent.Create(
                conversation_id=conversation.Id, failure_point=event_type
            )

            conversation.Events.append(error_event)
            error_counter -= 1

        return new_event, error_event, error_counter

    def _generate_event_from_type(
        self, event_type: EventType, conversation_id: int
    ) -> Event:
        new_event = None

        match event_type:
            case EventType.REGISTRATIONS:
                new_event = RegistrationsEvent(conversation_id)

            case EventType.TRANSFER_COMPATIBILITY_STATUSES:
                new_event = TransferCompatibilityStatusesEvent(conversation_id)

            case EventType.EHR_REQUESTS:
                new_event = EhrRequestsEvent(conversation_id)

            case EventType.EHR_RESPONSES:
                new_event = EhrResponsesEvent(conversation_id)

            case EventType.READY_TO_INTEGRATE_STATUSES:
                new_event = ReadyToIntegrateStatusesEvent(conversation_id)

            case EventType.EHR_INTEGRATIONS:
                new_event = EhrIntegrationsEvent(conversation_id)

            case _:
                pass

        return new_event
