import json

import constants as _C
from frameworks.Framework import Framework

class HIPAA(Framework):
    def __init__(self, data):
        super().__init__(data)
        pass
    
    def gateCheck(self):
        return True