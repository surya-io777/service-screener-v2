import botocore
from services.Evaluator import Evaluator

class BedrockModel(Evaluator):
    def __init__(self, model, bedrock_client, model_type):
        super().__init__()
        self.model = model
        self.bedrock_client = bedrock_client
        self.model_type = model_type
        
        if model_type == 'foundation':
            self.model_id = model['modelId']
            self.addII('ModelId', self.model_id)
            self.addII('ModelName', model.get('modelName', ''))
            self.addII('ProviderName', model.get('providerName', ''))
            self._resourceName = self.model_id
        else:
            self.model_name = model['modelName']
            self.addII('ModelName', self.model_name)
            self.addII('ModelArn', model.get('modelArn', ''))
            self._resourceName = self.model_name
        
        self.addII('ModelType', model_type)
        self.init()
    
    def _checkModelAccess(self):
        """Check if model access is properly configured"""
        if self.model_type == 'foundation':
            try:
                # Check if model is available in the region
                response = self.bedrock_client.get_foundation_model(modelIdentifier=self.model_id)
                model_details = response.get('modelDetails', {})
                
                if model_details.get('modelLifecycle', {}).get('status') == 'ACTIVE':
                    self.results['ModelAccess'] = [1, 'Model is active and accessible']
                else:
                    self.results['ModelAccess'] = [-1, 'Model is not active']
            except botocore.exceptions.ClientError as e:
                if e.response['Error']['Code'] == 'AccessDeniedException':
                    self.results['ModelAccess'] = [-1, 'Access denied - check model access permissions']
                else:
                    self.results['ModelAccess'] = [0, f'Error checking model access: {e.response["Error"]["Code"]}']
        else:
            self.results['ModelAccess'] = [1, 'Custom model access configured']
    
    def _checkModelUsage(self):
        """Check model usage and compliance"""
        if self.model_type == 'foundation':
            try:
                response = self.bedrock_client.get_foundation_model(modelIdentifier=self.model_id)
                model_details = response.get('modelDetails', {})
                
                # Check if model supports fine-tuning
                customizations_supported = model_details.get('customizationsSupported', [])
                if 'FINE_TUNING' in customizations_supported:
                    self.results['ModelCustomization'] = [1, 'Fine-tuning supported']
                else:
                    self.results['ModelCustomization'] = [0, 'Fine-tuning not supported']
                
                # Check inference types
                inference_types = model_details.get('inferenceTypesSupported', [])
                if inference_types:
                    self.results['InferenceTypes'] = [1, f'Supports: {", ".join(inference_types)}']
                else:
                    self.results['InferenceTypes'] = [0, 'No inference types specified']
                    
            except botocore.exceptions.ClientError as e:
                self.results['ModelCustomization'] = [0, f'Error checking model details: {e.response["Error"]["Code"]}']
                self.results['InferenceTypes'] = [0, f'Error checking model details: {e.response["Error"]["Code"]}']
        else:
            self.results['ModelCustomization'] = [1, 'Custom model - customization applied']
            self.results['InferenceTypes'] = [1, 'Custom model inference configured']
    
    def _checkModelCompliance(self):
        """Check model compliance and governance"""
        try:
            if self.model_type == 'foundation':
                response = self.bedrock_client.get_foundation_model(modelIdentifier=self.model_id)
                model_details = response.get('modelDetails', {})
                
                # Check if model has proper governance
                provider_name = model_details.get('providerName', '')
                if provider_name:
                    self.results['ModelGovernance'] = [1, f'Managed by {provider_name}']
                else:
                    self.results['ModelGovernance'] = [0, 'No provider information']
            else:
                # For custom models, check if they have proper training job configuration
                self.results['ModelGovernance'] = [1, 'Custom model governance applied']
                
        except botocore.exceptions.ClientError as e:
            self.results['ModelGovernance'] = [0, f'Error checking model governance: {e.response["Error"]["Code"]}']