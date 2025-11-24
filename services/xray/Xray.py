import boto3
import botocore

from utils.Config import Config
from services.Service import Service
from services.xray.drivers.XrayCommon import XrayCommon

class Xray(Service):
    def __init__(self, region):
        super().__init__(region)
        ssBoto = self.ssBoto
        self.xrayClient = ssBoto.client('xray', config=self.bConfig)
        
    def getResources(self):
        arr = []
        try:
            results = self.xrayClient.get_service_graph()
            arr = results.get('Services', [])
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] not in ['AccessDeniedException']:
                raise
        return arr
    
    def advise(self):
        objs = {}
        
        # X-Ray is account-level service
        obj = XrayCommon({}, self.xrayClient)
        obj.run(self.__class__)
        objs['XRay::Account'] = obj.getInfo()
        del obj
        
        return objs