import argparse
from tests.faker.conversation_service import ConversationService
import json

ap = argparse.ArgumentParser()
ap.add_argument(
    "-c", "--conversations", required=True, help="number of conversations to generate"
)
ap.add_argument(
    "-reg",
    "--error_registrations",
    required=False,
    help="number to stop at REGISTRAION with errors?",
)

ap.add_argument(
    "-com",
    "--error_trans_compat",
    required=False,
    help="number to stop at TRANSFER_COMPATIBILITY_STATUSES with errors?",
)

ap.add_argument(
    "-req",
    "--error_ehr_request",
    required=False,
    help="number to stop at EHR_REQUESTS with errors?",
)

ap.add_argument(
    "-res",
    "--error_ehr_response",
    required=False,
    help="number to stop at EHR_RESPONSES with errors?",
)

ap.add_argument(
    "-red",
    "--error_ready_integrate",
    required=False,
    help="number to stop at READY_TO_INTEGRATE_STATUSES with errors?",
)

ap.add_argument(
    "-int",
    "--error_integration",
    required=False,
    help="number to stop at EHR_INTEGRATIONS with errors?",
)

args = vars(ap.parse_args())

print(f"Args:{args}")
# -------------------------------

number_of_conversations = int(args["conversations"])
number_to_error_at_registrations = int(args["error_registrations"])
number_to_error_at_transfer_compatibility_statuses = int(args["error_trans_compat"])
number_to_error_at_ehr_request = int(args["error_ehr_request"])
number_to_error_at_ehr_response = int(args["error_ehr_response"])
number_to_error_at_ready_to_integrate = int(args["error_ready_integrate"])
number_to_error_at_integration = int(args["error_integration"])


conversationService = ConversationService()
conversations = conversationService.generate_conversations(
    number_of_conversations,
    number_to_error_at_registrations,
    number_to_error_at_transfer_compatibility_statuses,
    number_to_error_at_ehr_request,
    number_to_error_at_ehr_response,
    number_to_error_at_ready_to_integrate,
    number_to_error_at_integration
)


for i, value in enumerate(conversations):
    
    events = value.Events

    for y, event in enumerate(events):
        
        print(f"Conversaion: {i}, Event: {y} EventType: {event.eventType}")

        print(event.get_json())
        

