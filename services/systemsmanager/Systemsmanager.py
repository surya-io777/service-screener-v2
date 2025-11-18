import boto3
import botocore

from utils.Config import Config
from services.Service import Service
from services.systemsmanager.drivers.SystemsmanagerCommon import SystemsmanagerCommon

class Systemsmanager(Service):
    def __init__(self, region):
        super().__init__(region)
        ssBoto = self.ssBoto
        self.ssmClient = ssBoto.client('ssm', config=self.bConfig)
        
    def getResources(self):
        arr = []
        try:
            results = self.ssmClient.describe_instance_information()
            arr = results.get('InstanceInformationList', [])
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] not in ['AccessDeniedException']:
                raise
        return arr
    
    def advise(self):
        objs = {}
        
        # Systems Manager is account-level service
        obj = SystemsmanagerCommon({}, self.ssmClient)
        obj.run(self.__class__)
        objs['SystemsManager::Account'] = obj.getInfo()
        del obj
        
        return objs