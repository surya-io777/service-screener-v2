import boto3
import botocore

from utils.Config import Config
from services.Service import Service
from services.ses.drivers.SesCommon import SesCommon

class Ses(Service):
    def __init__(self, region):
        super().__init__(region)
        ssBoto = self.ssBoto
        self.sesClient = ssBoto.client('sesv2', config=self.bConfig)
        
    def getResources(self):
        arr = []
        try:
            results = self.sesClient.list_email_identities()
            arr = results.get('EmailIdentities', [])
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] not in ['AccessDeniedException']:
                raise
        return arr
    
    def advise(self):
        objs = {}
        
        identities = self.getResources()
        if not identities:
            # Create a placeholder for account-level checks
            obj = SesCommon({}, self.sesClient)
            obj.run(self.__class__)
            objs['SES::Account'] = obj.getInfo()
            del obj
        else:
            for identity in identities:
                identity_name = identity.get('IdentityName', 'Unknown')
                print('... (SES) inspecting ' + identity_name)
                obj = SesCommon(identity, self.sesClient)
                obj.run(self.__class__)
                objs[f"SES::{identity_name}"] = obj.getInfo()
                del obj
        
        return objs