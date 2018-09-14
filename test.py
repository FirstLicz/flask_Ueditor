import json
import os
import traceback
import re

from app import basedir

with open(os.path.join(basedir, 'static', 'ueditor', 'python', 'config.json'), encoding='utf8') as f:
    t = f.read()
    try:
        result = json.loads(re.sub(r'\/\*.*\*\/', '', t))
    except Exception as e:
        traceback.print_exc(e)
print(result)
