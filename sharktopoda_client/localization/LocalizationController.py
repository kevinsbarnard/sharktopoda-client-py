from logging import Logger
from typing import List
from sharktopoda_client.IOBus import IOBus
from sharktopoda_client.localization.Localization import Localization


class LocalizationController(IOBus):
    
    def __init__(self):
        super().__init__()
        
        self.log = Logger('LocalizationController')
        
        self.localizations: List[Localization] = []
        
        