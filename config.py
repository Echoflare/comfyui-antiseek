import os
import json

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")

class AntiSeekConfig:
    def __init__(self):
        self.salt = ""
        self.key_name = "s_tag"
        self.load()

    def load(self):
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.salt = data.get("salt", "")
                    self.key_name = data.get("key_name", "s_tag")
            except:
                pass

    def save(self):
        data = {
            "salt": self.salt,
            "key_name": self.key_name
        }
        try:
            with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
        except:
            pass

global_config = AntiSeekConfig()