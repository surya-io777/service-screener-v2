import boto3
import botocore
import constants as _C

from services.Evaluator import Evaluator

class AwsconfigCommon(Evaluator):
    def __init__(self, recorder, configClient):
        super().__init__()
        self.init()
        self.recorder = recorder
        self.configClient = configClient
        self._resourceName = recorder.get('name', 'Account')
        
    def _checkConfigEnabled(self):
        if not self.recorder:
            self.results['ConfigEnabled'] = [-1, "AWS Config is not enabled"]
            return
        
        # Check if recorder is recording
        try:
            status = self.configClient.describe_configuration_recorder_status(
                ConfigurationRecorderNames=[self.recorder['name']]
            )
            if not status['ConfigurationRecordersStatus'][0]['recording']:
                self.results['ConfigRecording'] = [-1, f"Configuration recorder {self.recorder['name']} is not recording"]
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] not in ['AccessDeniedException']:
                self.results['ConfigRecording'] = [-1, f"Unable to check recording status: {str(e)}"]
        except Exception as e:
            self.results['ConfigRecording'] = [-1, f"Unable to check recording status: {str(e)}"]
    
    def _checkDeliveryChannel(self):
        try:
            channels = self.configClient.describe_delivery_channels()
            if not channels.get('DeliveryChannels'):
                self.results['DeliveryChannel'] = [-1, "No delivery channel configured"]
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] not in ['AccessDeniedException']:
                self.results['DeliveryChannel'] = [-1, f"Unable to check delivery channels: {str(e)}"]
        except Exception as e:
            self.results['DeliveryChannel'] = [-1, f"Unable to check delivery channels: {str(e)}"]
    
    def _checkConfigRules(self):
        try:
            rules = self.configClient.describe_config_rules()
            rule_count = len(rules.get('ConfigRules', []))
            if rule_count == 0:
                self.results['ConfigRules'] = [-1, "No Config rules configured"]
            else:
                self.results['ConfigRulesCount'] = [1, f"{rule_count} Config rules configured"]
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] not in ['AccessDeniedException']:
                self.results['ConfigRules'] = [-1, f"Unable to check Config rules: {str(e)}"]
        except Exception as e:
            self.results['ConfigRules'] = [-1, f"Unable to check Config rules: {str(e)}"]