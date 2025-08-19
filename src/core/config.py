import yaml

class Config:
    def __init__(self, config_file='config/config.yaml'):
        with open(config_file, 'r') as file:
            config = yaml.safe_load(file)
        
        self.server = config['server']
        self.database = config['database']
        self.storage = config['storage']
        self.cameras = config['cameras']
        self.detection = config['detection']
        self.motion = config['motion']
        self.recording = config['recording']
        self.webhooks = config['webhooks']
        self.logging = config['logging']
