import json
import numpy as np
import pandas as pd
from pathlib import Path

class NHTSALoader:
    """
    Reads NHTSA test folder metadata
    """
    def __init__(self, folder_path:str):
        self.folder = Path(folder_path)
        