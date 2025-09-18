import botocore
from services.Evaluator import Evaluator

class SagemakerEndpoint(Evaluator):
    def __init__(self, endpoint, sagemaker_client):
        super().__init__()
        self.endpoint = endpoint
        self.sagemaker_client = sagemaker_client
        self.endpoint_name = endpoint['EndpointName']
        
        self.addII('EndpointName', self.endpoint_name)
        self.addII('EndpointStatus', endpoint.get('EndpointStatus'))
        self.addII('CreationTime', str(endpoint.get('CreationTime', '')))
        
        self._resourceName = self.endpoint_name
        self.init()
    
    def _checkEndpointEncryption(self):
        """Check if endpoint has encryption enabled"""
        try:
            response = self.sagemaker_client.describe_endpoint(
                EndpointName=self.endpoint_name
            )
            endpoint_config_name = response.get('EndpointConfigName')
            
            config_response = self.sagemaker_client.describe_endpoint_config(
                EndpointConfigName=endpoint_config_name
            )
            kms_key_id = config_response.get('KmsKeyId')
            
            if kms_key_id:
                self.results['EndpointEncryption'] = [1, 'KMS encryption enabled']
            else:
                self.results['EndpointEncryption'] = [-1, 'No KMS encryption']
        except botocore.exceptions.ClientError as e:
            self.results['EndpointEncryption'] = [0, f'Error checking encryption: {e.response["Error"]["Code"]}']
    
    def _checkDataCaptureConfig(self):
        """Check if data capture is configured"""
        try:
            response = self.sagemaker_client.describe_endpoint(
                EndpointName=self.endpoint_name
            )
            endpoint_config_name = response.get('EndpointConfigName')
            
            config_response = self.sagemaker_client.describe_endpoint_config(
                EndpointConfigName=endpoint_config_name
            )
            data_capture_config = config_response.get('DataCaptureConfig')
            
            if data_capture_config and data_capture_config.get('EnableCapture'):
                self.results['DataCaptureConfig'] = [1, 'Data capture enabled']
            else:
                self.results['DataCaptureConfig'] = [-1, 'Data capture not configured']
        except botocore.exceptions.ClientError as e:
            self.results['DataCaptureConfig'] = [0, f'Error checking data capture: {e.response["Error"]["Code"]}']
    
    def _checkAutoScaling(self):
        """Check if auto scaling is configured"""
        try:
            autoscaling_client = self.sagemaker_client._client_config.region_name
            # This is a simplified check - in practice you'd check Application Auto Scaling
            response = self.sagemaker_client.describe_endpoint(
                EndpointName=self.endpoint_name
            )
            endpoint_config_name = response.get('EndpointConfigName')
            
            config_response = self.sagemaker_client.describe_endpoint_config(
                EndpointConfigName=endpoint_config_name
            )
            production_variants = config_response.get('ProductionVariants', [])
            
            has_multiple_instances = any(pv.get('InitialInstanceCount', 1) > 1 for pv in production_variants)
            
            if has_multiple_instances:
                self.results['AutoScaling'] = [1, 'Multiple instances configured']
            else:
                self.results['AutoScaling'] = [0, 'Single instance - consider auto scaling']
        except botocore.exceptions.ClientError as e:
            self.results['AutoScaling'] = [0, f'Error checking auto scaling: {e.response["Error"]["Code"]}']