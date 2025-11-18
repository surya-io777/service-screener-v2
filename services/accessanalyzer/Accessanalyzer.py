import boto3
import botocore

from utils.Config import Config
from services.Service import Service
from services.accessanalyzer.drivers.AccessanalyzerCommon import AccessanalyzerCommon

class Accessanalyzer(Service):
    def __init__(self, region):
        super().__init__(region)
        ssBoto = self.ssBoto
        self.accessanalyzerClient = ssBoto.client('accessanalyzer', config=self.bConfig)
        
    def getResources(self):
        arr = []
        try:
            results = self.accessanalyzerClient.list_analyzers()
            arr = results.get('analyzers', [])
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] not in ['AccessDeniedException']:
                raise
        return arr
    
    def advise(self):
        objs = {}
        
        analyzers = self.getResources()
        if not analyzers:
            # Create a placeholder for account-level checks
            obj = AccessanalyzerCommon({}, self.accessanalyzerClient)
            obj.run(self.__class__)
            objs['AccessAnalyzer::Account'] = obj.getInfo()
            del obj
        else:
            for analyzer in analyzers:
                print('... (AccessAnalyzer) inspecting ' + analyzer.get('name', 'Unknown'))
                obj = AccessanalyzerCommon(analyzer, self.accessanalyzerClient)
                obj.run(self.__class__)
                objs[f"AccessAnalyzer::{analyzer.get('name', 'Unknown')}"] = obj.getInfo()
                del obj
        
        return objs