import json
import os
script_dir = os.path.dirname(os.path.abspath(__file__))
prefix = f"{script_dir}/"

with open(f"{prefix}save_data.json", "r") as f:
    data = json.load(f)

SCREEN_SIZE = data["size"]

winner = None
money = data["money"]

bullet_entities = [
    
]



explosive_entities = [

]

