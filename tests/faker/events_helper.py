from faker import Faker
from faker.providers import BaseProvider
from faker.providers.address.en_GB import Provider as en_GB_provider
from faker.providers.misc import Provider as misc_provider
from tests.test_base import EventType


class EventsHelperProvider(en_GB_provider, misc_provider):
    system_suppliers_list = ["EMIS", "TPP", "VISION", "MEDICUS"]
    supplier_ods_codes = ["YGJ", "YGA", "YGC", "YGMYW"]
    integration_outcomes = [
        "INTEGRATED",
        "INTEGRATED_AND_SUPPRESSED",
        "SUPPRESSED_AND_REACTIVATED",
        "FILED_AS_ATTACHMENT",
        "INTERNAL_TRANSFER",
    ]

    clinical_type_list = [
        "SCANNED_DOCUMENT",
        "ORIGINAL_TEXT_DOCUMENT",
        "OCR_TEXT_DOCUMENT",
        "IMAGE",
        "AUDIO_DICTATION",
        "OTHER_AUDIO",
        "OTHER_DIGITAL_SIGNAL",
        "EDI_MESSAGE",
        "NOT_AVAILABLE",
        "OTHER",
    ]
    generated_by_list = ["SENDER", "PRE_EXISTING"]

    mime_type_list = [
        "audio/mpeg",
        "image/jpeg",
        "application/pdf",
    ]
    reasons_list = [
        "FILE_TYPE_UNSUPPORTED",
        "FILE_DELETED",
        "FILE_NOT_FOUND",
        "FILE_LOCKED",
        "UNABLE_TO_DETERMINE_PROBLEM",
    ]

    def random_supplier_ods_code(self):
        return self.random_element(self.supplier_ods_codes)

    def random_practice_ods_code(self):
        return self.bothify(text="?#####").upper()

    def random_practice_name(self):
        return f"{self.city()} Medical Practice"

    def generate_payload(self, EventType: EventType):
        match EventType:
            case EventType.REGISTRATIONS:
                return {
                    "registration": {
                        "type": "NEW_GP_REGISTRATION",
                        "returningPatient": False,
                        "multifactorAuthenticationPresent": True,
                    },
                    "demographicTraceStatus": self.random_demographic_trace_status(),
                    "gpLinks": self.generate_gp_links(),
                }
            case EventType.EHR_INTEGRATIONS:
                return {
                    "integration": {
                        "outcome": f"{self.random_element(self.integration_outcomes)}"
                    }
                }
            case EventType.EHR_RESPONSES:
                placeholders = []
                number_random_placeholders = self.random_int(min=1, max=10)
                for i in range(number_random_placeholders):
                    placeholders.append(
                        {
                            "generatedBy": self.random_element(self.generated_by_list),
                            "clinicalType": self.random_element(
                                self.clinical_type_list
                            ),
                            "reason": self.random_element(self.clinical_type_list),
                            "originalMimeType": self.random_element(
                                self.mime_type_list
                            ),
                        }
                    )
                return {
                    "ehr": {
                        f"ehrStructuredSizeBytes": self.random_int(min=100, max=9999)
                    },
                    "placeholders": placeholders,
                }
            case EventType.TRANSFER_COMPATIBILITY_STATUSES:
                transfer_compatible = self.boolean(chance_of_getting_true=80)

                return_val = {
                    "transferCompatibilityStatus": {
                        "internalTransfer": self.boolean(chance_of_getting_true=30),
                        "transferCompatible": transfer_compatible,
                    }
                }

                if not transfer_compatible:
                    reason = "Previous practice not eligible for transfer"
                    return_val["transferCompatibilityStatus"]["reason"] = reason

                return return_val

            case EventType.DOCUMENT_RESPONSES:
                document_migration_successful = self.boolean(chance_of_getting_true=50)

                return_val = {
                    "attachment": {
                        "clinicalType": self.random_element(self.clinical_type_list),
                        "mimeType": self.random_element(self.mime_type_list),
                        "sizeBytes": self.random_int(min=1000000, max=9999999),
                    },
                    "documentMigration": {
                        "successful": f"{document_migration_successful}"
                    },
                }

                if not document_migration_successful:
                    reason = "Large file size"
                    return_val["documentMigration"]["reason"] = reason

                return return_val

            case EventType.ERRORS:
                return {
                    "error": {
                        "errorCode": "99",
                        "errorDescription": "unexpected error",
                        "failurePoint": "EHR_RESPONSE",
                    }
                }

            case _:
                pass

    def random_demographic_trace_status(self):
        matched = self.boolean(chance_of_getting_true=50)

        return_val = {"matched": matched, "multifactorAuthenticationPresent": matched}

        if not matched:
            reason = "No PDS trace results returned"
            return_val["reason"] = reason

        return return_val

    def generate_gp_links(self):
        return {"gpLinksComplete": False}
