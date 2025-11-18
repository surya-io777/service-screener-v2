import boto3
import botocore

from utils.Config import Config
from services.Service import Service
from services.awsconfig.drivers.AwsconfigCommon import AwsconfigCommon

class Awsconfig(Service):
    def __init__(self, region):
        super().__init__(region)
        ssBoto = self.ssBoto
        self.configClient = ssBoto.client('config', config=self.bConfig)
        
    def getResources(self):
        arr = []
        try:
            results = self.configClient.describe_configuration_recorders()
            arr = results.get('ConfigurationRecorders', [])
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] != 'NoSuchConfigurationRecorderException':
                raise
        return arr
    
    def advise(self):
        objs = {}
        
        recorders = self.getResources()
        if not recorders:
            # Create a placeholder for account-level checks
            obj = AwsconfigCommon({}, self.configClient)
            obj.run(self.__class__)
            objs['Config::Account'] = obj.getInfo()
            del obj
        else:
            for recorder in recorders:
                print('... (Config) inspecting ' + recorder.get('name', 'Unknown'))
                obj = AwsconfigCommon(recorder, self.configClient)
                obj.run(self.__class__)
                objs[f"Config::{recorder.get('name', 'Unknown')}"] = obj.getInfo()
                del obj
        
        return objs