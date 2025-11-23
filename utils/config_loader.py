import yaml
from typing import Dict
import os

def load_config(path: str = "config.yaml") -> Dict:

    base_dir = os.path.dirname(__file__)
    config_path = os.path.join(base_dir, path)
    
    with open(config_path, 'r') as file:

        return yaml.safe_load(file)