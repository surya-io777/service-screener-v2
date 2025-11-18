import boto3
import botocore

from utils.Config import Config
from services.Service import Service
from services.devopsguru.drivers.DevopsguruCommon import DevopsguruCommon

class Devopsguru(Service):
    def __init__(self, region):
        super().__init__(region)
        ssBoto = self.ssBoto
        self.devopsguruClient = ssBoto.client('devops-guru', config=self.bConfig)
        
    def getResources(self):
        arr = []
        try:
            results = self.devopsguruClient.describe_service_integration()
            arr = [results]
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] not in ['AccessDeniedException', 'UnauthorizedOperation']:
                raise
        return arr
    
    def advise(self):
        objs = {}
        
        # DevOps Guru is account-level service
        obj = DevopsguruCommon({}, self.devopsguruClient)
        obj.run(self.__class__)
        objs['DevOpsGuru::Account'] = obj.getInfo()
        del obj
        
        return objs