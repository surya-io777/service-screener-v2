import boto3
import botocore

from utils.Config import Config
from services.Service import Service
from services.securityhub.drivers.SecurityhubCommon import SecurityhubCommon

class Securityhub(Service):
    def __init__(self, region):
        super().__init__(region)
        ssBoto = self.ssBoto
        self.securityhubClient = ssBoto.client('securityhub', config=self.bConfig)
        
    def getResources(self):
        arr = []
        try:
            results = self.securityhubClient.describe_hub()
            arr = [results]
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] not in ['InvalidAccessException', 'LimitExceededException']:
                raise
        return arr
    
    def advise(self):
        objs = {}
        
        # Security Hub is account-level service
        obj = SecurityhubCommon({}, self.securityhubClient)
        obj.run(self.__class__)
        objs['SecurityHub::Account'] = obj.getInfo()
        del obj
        
        return objs