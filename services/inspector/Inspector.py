import boto3
import botocore

from utils.Config import Config
from services.Service import Service
from services.inspector.drivers.InspectorCommon import InspectorCommon

class Inspector(Service):
    def __init__(self, region):
        super().__init__(region)
        ssBoto = self.ssBoto
        self.inspectorClient = ssBoto.client('inspector2', config=self.bConfig)
        
    def getResources(self):
        arr = []
        try:
            results = self.inspectorClient.batch_get_account_status(
                accountIds=[self.getAccountId()]
            )
            arr = results.get('accounts', [])
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] not in ['AccessDeniedException', 'ValidationException']:
                raise
        return arr
    
    def getAccountId(self):
        try:
            sts = self.ssBoto.client('sts')
            return sts.get_caller_identity()['Account']
        except:
            return 'unknown'
    
    def advise(self):
        objs = {}
        
        # Inspector is account-level service
        obj = InspectorCommon({}, self.inspectorClient, self.getAccountId())
        obj.run(self.__class__)
        objs['Inspector::Account'] = obj.getInfo()
        del obj
        
        return objs