import botocore
from utils.Config import Config
from services.Service import Service
from services.bedrock.drivers.BedrockModel import BedrockModel
from services.bedrock.drivers.BedrockKnowledgeBase import BedrockKnowledgeBase
from utils.Tools import _pi

class Bedrock(Service):
    def __init__(self, region):
        super().__init__(region)
        ssBoto = self.ssBoto
        self.bedrockClient = ssBoto.client('bedrock', config=self.bConfig)
        
    def getFoundationModels(self):
        models = []
        try:
            response = self.bedrockClient.list_foundation_models()
            models = response.get('modelSummaries', [])
        except botocore.exceptions.ClientError as e:
            print(f"Error getting foundation models: {e}")
        return models
    
    def getCustomModels(self):
        models = []
        try:
            response = self.bedrockClient.list_custom_models()
            models = response.get('modelSummaries', [])
        except botocore.exceptions.ClientError as e:
            print(f"Error getting custom models: {e}")
        return models
    
    def getKnowledgeBases(self):
        knowledge_bases = []
        try:
            bedrock_agent_client = self.ssBoto.client('bedrock-agent', config=self.bConfig)
            response = bedrock_agent_client.list_knowledge_bases()
            knowledge_bases = response.get('knowledgeBaseSummaries', [])
        except botocore.exceptions.ClientError as e:
            print(f"Error getting knowledge bases: {e}")
        return knowledge_bases
    
    def advise(self):
        objs = {}
        
        # Check foundation models
        foundation_models = self.getFoundationModels()
        for model in foundation_models:
            model_id = model['modelId']
            _pi('Bedrock::FoundationModel', model_id)
            
            obj = BedrockModel(model, self.bedrockClient, 'foundation')
            obj.run(self.__class__)
            objs[f"FoundationModel::{model_id}"] = obj.getInfo()
            del obj
        
        # Check custom models
        custom_models = self.getCustomModels()
        for model in custom_models:
            model_name = model['modelName']
            _pi('Bedrock::CustomModel', model_name)
            
            obj = BedrockModel(model, self.bedrockClient, 'custom')
            obj.run(self.__class__)
            objs[f"CustomModel::{model_name}"] = obj.getInfo()
            del obj
        
        # Check knowledge bases
        knowledge_bases = self.getKnowledgeBases()
        for kb in knowledge_bases:
            kb_id = kb['knowledgeBaseId']
            _pi('Bedrock::KnowledgeBase', kb_id)
            
            obj = BedrockKnowledgeBase(kb, self.ssBoto)
            obj.run(self.__class__)
            objs[f"KnowledgeBase::{kb_id}"] = obj.getInfo()
            del obj
        
        return objs