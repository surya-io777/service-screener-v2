import botocore
from services.Evaluator import Evaluator

class SagemakerNotebook(Evaluator):
    def __init__(self, notebook, sagemaker_client):
        super().__init__()
        self.notebook = notebook
        self.sagemaker_client = sagemaker_client
        self.notebook_name = notebook['NotebookInstanceName']
        
        self.addII('NotebookInstanceName', self.notebook_name)
        self.addII('NotebookInstanceStatus', notebook.get('NotebookInstanceStatus'))
        self.addII('InstanceType', notebook.get('InstanceType'))
        
        self._resourceName = self.notebook_name
        self.init()
    
    def _checkNotebookEncryption(self):
        """Check if notebook instance has encryption enabled"""
        try:
            response = self.sagemaker_client.describe_notebook_instance(
                NotebookInstanceName=self.notebook_name
            )
            kms_key_id = response.get('KmsKeyId')
            
            if kms_key_id:
                self.results['NotebookEncryption'] = [1, 'KMS encryption enabled']
            else:
                self.results['NotebookEncryption'] = [-1, 'No KMS encryption']
        except botocore.exceptions.ClientError as e:
            self.results['NotebookEncryption'] = [0, f'Error checking encryption: {e.response["Error"]["Code"]}']
    
    def _checkDirectInternetAccess(self):
        """Check if direct internet access is disabled"""
        try:
            response = self.sagemaker_client.describe_notebook_instance(
                NotebookInstanceName=self.notebook_name
            )
            direct_internet_access = response.get('DirectInternetAccess', 'Enabled')
            
            if direct_internet_access == 'Disabled':
                self.results['DirectInternetAccess'] = [1, 'Direct internet access disabled']
            else:
                self.results['DirectInternetAccess'] = [-1, 'Direct internet access enabled']
        except botocore.exceptions.ClientError as e:
            self.results['DirectInternetAccess'] = [0, f'Error checking internet access: {e.response["Error"]["Code"]}']
    
    def _checkRootAccess(self):
        """Check if root access is disabled"""
        try:
            response = self.sagemaker_client.describe_notebook_instance(
                NotebookInstanceName=self.notebook_name
            )
            root_access = response.get('RootAccess', 'Enabled')
            
            if root_access == 'Disabled':
                self.results['RootAccess'] = [1, 'Root access disabled']
            else:
                self.results['RootAccess'] = [-1, 'Root access enabled']
        except botocore.exceptions.ClientError as e:
            self.results['RootAccess'] = [0, f'Error checking root access: {e.response["Error"]["Code"]}']
    
    def _checkVPCConfiguration(self):
        """Check if notebook is deployed in VPC"""
        try:
            response = self.sagemaker_client.describe_notebook_instance(
                NotebookInstanceName=self.notebook_name
            )
            subnet_id = response.get('SubnetId')
            security_groups = response.get('SecurityGroups', [])
            
            if subnet_id and security_groups:
                self.results['VPCConfiguration'] = [1, f'Deployed in VPC with {len(security_groups)} security groups']
            else:
                self.results['VPCConfiguration'] = [-1, 'Not deployed in VPC']
        except botocore.exceptions.ClientError as e:
            self.results['VPCConfiguration'] = [0, f'Error checking VPC configuration: {e.response["Error"]["Code"]}']