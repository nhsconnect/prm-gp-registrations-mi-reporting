from faker import Faker
from faker.providers import BaseProvider
from faker.providers.address.en_GB import Provider as en_GB_provider
from faker.providers.misc import Provider as misc_provider
from tests.test_base import EventType




class EventsHelperProvider(en_GB_provider, misc_provider):

    system_suppliers_list = ["EMIS", "TPP", "VISION", "MEDICUS"]
    supplier_ods_codes = ["YGJ", "YGA", "YGC", "YGMYW"]

    def random_supplier_ods_code(self):
        return self.random_element(self.supplier_ods_codes)
    

    def random_practice_ods_code(self):
        return self.bothify(text='?#####').upper()
    
    def random_practice_name(self):
        return f"{self.city()} Medical Practice"
    
    def generate_payload(self, EventType):

        match EventType:
            case EventType.REGISTRATIONS:
                return {
                    'registration':{
                        "type":'NEW_GP_REGISTRATION',
                        "returningPatient": False,
                        "multifactorAuthenticationPresent": True
                    },
                    "demographicTraceStatus": self.random_demographic_trace_status(),
                    "gpLinks": self.generate_gp_links()
                }                
            case _:
                pass       
         
    
    def random_demographic_trace_status(self):

        matched = self.boolean(chance_of_getting_true=50)

        return_val = {
            "matched": matched,
            "multifactorAuthenticationPresent":matched
        }

        if not matched:
            reason =  "No PDS trace results returned"
            return_val["reason"]  = reason

        return return_val
    
    def generate_gp_links(self):
        return {"gpLinksComplete": False}
