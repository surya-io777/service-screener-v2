import botocore
from services.Evaluator import Evaluator

class SagemakerModel(Evaluator):
    def __init__(self, model, sagemaker_client):
        super().__init__()
        self.model = model
        self.sagemaker_client = sagemaker_client
        self.model_name = model['ModelName']
        
        self.addII('ModelName', self.model_name)
        self.addII('CreationTime', str(model.get('CreationTime', '')))
        
        self._resourceName = self.model_name
        self.init()
    
    def _checkModelEncryption(self):
        """Check if model has encryption enabled"""
        try:
            response = self.sagemaker_client.describe_model(
                ModelName=self.model_name
            )
            
            # Check VPC config for network isolation
            vpc_config = response.get('VpcConfig')
            if vpc_config:
                self.results['ModelNetworkIsolation'] = [1, 'VPC configuration enabled']
            else:
                self.results['ModelNetworkIsolation'] = [-1, 'No VPC configuration']
            
            # Check if model has proper IAM role
            execution_role_arn = response.get('ExecutionRoleArn')
            if execution_role_arn:
                self.results['ModelExecutionRole'] = [1, 'Execution role configured']
            else:
                self.results['ModelExecutionRole'] = [-1, 'No execution role']
                
        except botocore.exceptions.ClientError as e:
            self.results['ModelNetworkIsolation'] = [0, f'Error checking model: {e.response["Error"]["Code"]}']
            self.results['ModelExecutionRole'] = [0, f'Error checking model: {e.response["Error"]["Code"]}']
    
    def _checkModelArtifacts(self):
        """Check if model artifacts are properly configured"""
        try:
            response = self.sagemaker_client.describe_model(
                ModelName=self.model_name
            )
            
            primary_container = response.get('PrimaryContainer', {})
            model_data_url = primary_container.get('ModelDataUrl')
            
            if model_data_url and model_data_url.startswith('s3://'):
                self.results['ModelArtifacts'] = [1, 'Model artifacts stored in S3']
            else:
                self.results['ModelArtifacts'] = [-1, 'Model artifacts not properly configured']
                
        except botocore.exceptions.ClientError as e:
            self.results['ModelArtifacts'] = [0, f'Error checking model artifacts: {e.response["Error"]["Code"]}']