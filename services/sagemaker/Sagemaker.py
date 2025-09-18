import botocore
from utils.Config import Config
from services.Service import Service
from services.sagemaker.drivers.SagemakerNotebook import SagemakerNotebook
from services.sagemaker.drivers.SagemakerEndpoint import SagemakerEndpoint
from services.sagemaker.drivers.SagemakerModel import SagemakerModel
from utils.Tools import _pi

class Sagemaker(Service):
    def __init__(self, region):
        super().__init__(region)
        ssBoto = self.ssBoto
        self.sagemakerClient = ssBoto.client('sagemaker', config=self.bConfig)
        
    def getNotebookInstances(self):
        notebooks = []
        try:
            paginator = self.sagemakerClient.get_paginator('list_notebook_instances')
            for page in paginator.paginate():
                for notebook in page.get('NotebookInstances', []):
                    if self.tags:
                        tags_response = self.sagemakerClient.list_tags(ResourceArn=notebook['NotebookInstanceArn'])
                        tags = tags_response.get('Tags', [])
                        if not self.resourceHasTags(tags):
                            continue
                    notebooks.append(notebook)
        except botocore.exceptions.ClientError as e:
            print(f"Error getting notebook instances: {e}")
        return notebooks
    
    def getEndpoints(self):
        endpoints = []
        try:
            paginator = self.sagemakerClient.get_paginator('list_endpoints')
            for page in paginator.paginate():
                for endpoint in page.get('Endpoints', []):
                    if self.tags:
                        tags_response = self.sagemakerClient.list_tags(ResourceArn=endpoint['EndpointArn'])
                        tags = tags_response.get('Tags', [])
                        if not self.resourceHasTags(tags):
                            continue
                    endpoints.append(endpoint)
        except botocore.exceptions.ClientError as e:
            print(f"Error getting endpoints: {e}")
        return endpoints
    
    def getModels(self):
        models = []
        try:
            paginator = self.sagemakerClient.get_paginator('list_models')
            for page in paginator.paginate():
                for model in page.get('Models', []):
                    if self.tags:
                        tags_response = self.sagemakerClient.list_tags(ResourceArn=model['ModelArn'])
                        tags = tags_response.get('Tags', [])
                        if not self.resourceHasTags(tags):
                            continue
                    models.append(model)
        except botocore.exceptions.ClientError as e:
            print(f"Error getting models: {e}")
        return models
    
    def advise(self):
        objs = {}
        
        # Check notebook instances
        notebooks = self.getNotebookInstances()
        for notebook in notebooks:
            notebook_name = notebook['NotebookInstanceName']
            _pi('SageMaker::NotebookInstance', notebook_name)
            
            obj = SagemakerNotebook(notebook, self.sagemakerClient)
            obj.run(self.__class__)
            objs[f"NotebookInstance::{notebook_name}"] = obj.getInfo()
            del obj
        
        # Check endpoints
        endpoints = self.getEndpoints()
        for endpoint in endpoints:
            endpoint_name = endpoint['EndpointName']
            _pi('SageMaker::Endpoint', endpoint_name)
            
            obj = SagemakerEndpoint(endpoint, self.sagemakerClient)
            obj.run(self.__class__)
            objs[f"Endpoint::{endpoint_name}"] = obj.getInfo()
            del obj
        
        # Check models
        models = self.getModels()
        for model in models:
            model_name = model['ModelName']
            _pi('SageMaker::Model', model_name)
            
            obj = SagemakerModel(model, self.sagemakerClient)
            obj.run(self.__class__)
            objs[f"Model::{model_name}"] = obj.getInfo()
            del obj
        
        return objs