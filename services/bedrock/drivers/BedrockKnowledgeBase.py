import botocore
from services.Evaluator import Evaluator

class BedrockKnowledgeBase(Evaluator):
    def __init__(self, knowledge_base, boto_session):
        super().__init__()
        self.knowledge_base = knowledge_base
        self.kb_id = knowledge_base['knowledgeBaseId']
        self.bedrock_agent_client = boto_session.client('bedrock-agent')
        
        self.addII('KnowledgeBaseId', self.kb_id)
        self.addII('Name', knowledge_base.get('name', ''))
        self.addII('Status', knowledge_base.get('status', ''))
        
        self._resourceName = self.kb_id
        self.init()
    
    def _checkKnowledgeBaseEncryption(self):
        """Check if knowledge base has encryption configured"""
        try:
            response = self.bedrock_agent_client.get_knowledge_base(knowledgeBaseId=self.kb_id)
            kb_details = response.get('knowledgeBase', {})
            
            # Check storage configuration for encryption
            storage_config = kb_details.get('storageConfiguration', {})
            if storage_config.get('type') == 'OPENSEARCH_SERVERLESS':
                opensearch_config = storage_config.get('opensearchServerlessConfiguration', {})
                if opensearch_config:
                    self.results['KnowledgeBaseEncryption'] = [1, 'OpenSearch Serverless encryption enabled']
                else:
                    self.results['KnowledgeBaseEncryption'] = [-1, 'No encryption configuration found']
            elif storage_config.get('type') == 'PINECONE':
                self.results['KnowledgeBaseEncryption'] = [0, 'Pinecone encryption depends on external configuration']
            else:
                self.results['KnowledgeBaseEncryption'] = [0, 'Unknown storage type']
                
        except botocore.exceptions.ClientError as e:
            self.results['KnowledgeBaseEncryption'] = [0, f'Error checking encryption: {e.response["Error"]["Code"]}']
    
    def _checkDataSourceConfiguration(self):
        """Check if data sources are properly configured"""
        try:
            response = self.bedrock_agent_client.list_data_sources(knowledgeBaseId=self.kb_id)
            data_sources = response.get('dataSourceSummaries', [])
            
            if data_sources:
                active_sources = [ds for ds in data_sources if ds.get('status') == 'AVAILABLE']
                if active_sources:
                    self.results['DataSourceConfiguration'] = [1, f'{len(active_sources)} active data sources']
                else:
                    self.results['DataSourceConfiguration'] = [-1, 'No active data sources']
            else:
                self.results['DataSourceConfiguration'] = [-1, 'No data sources configured']
                
        except botocore.exceptions.ClientError as e:
            self.results['DataSourceConfiguration'] = [0, f'Error checking data sources: {e.response["Error"]["Code"]}']
    
    def _checkKnowledgeBaseAccess(self):
        """Check if knowledge base has proper access controls"""
        try:
            response = self.bedrock_agent_client.get_knowledge_base(knowledgeBaseId=self.kb_id)
            kb_details = response.get('knowledgeBase', {})
            
            role_arn = kb_details.get('roleArn')
            if role_arn:
                self.results['KnowledgeBaseAccess'] = [1, 'IAM role configured for access control']
            else:
                self.results['KnowledgeBaseAccess'] = [-1, 'No IAM role configured']
                
        except botocore.exceptions.ClientError as e:
            self.results['KnowledgeBaseAccess'] = [0, f'Error checking access controls: {e.response["Error"]["Code"]}']
    
    def _checkKnowledgeBaseStatus(self):
        """Check if knowledge base is in a healthy state"""
        status = self.knowledge_base.get('status', '')
        
        if status == 'ACTIVE':
            self.results['KnowledgeBaseStatus'] = [1, 'Knowledge base is active']
        elif status == 'CREATING':
            self.results['KnowledgeBaseStatus'] = [0, 'Knowledge base is being created']
        elif status == 'DELETING':
            self.results['KnowledgeBaseStatus'] = [0, 'Knowledge base is being deleted']
        elif status == 'FAILED':
            self.results['KnowledgeBaseStatus'] = [-1, 'Knowledge base is in failed state']
        else:
            self.results['KnowledgeBaseStatus'] = [0, f'Unknown status: {status}']