#!/usr/bin/env python3
import json, shutil, tempfile
from pathlib import Path
from hashlib import sha256

# Patch tokenizer config
temp_dir = Path(tempfile.mkdtemp())
for f in ['tokenizer.json', 'tokenizer_config.json']:
    shutil.copy2(Path('gemma-4-E4B-it') / f, temp_dir / f)
tc_path = temp_dir / 'tokenizer_config.json'
with open(tc_path, 'r') as f:
    tc = json.load(f)
if isinstance(tc.get('extra_special_tokens'), list):
    tc['extra_special_tokens'] = {tok: tok for tok in tc['extra_special_tokens']}
with open(tc_path, 'w') as f:
    json.dump(tc, f)

from transformers import AutoTokenizer
tokenizer = AutoTokenizer.from_pretrained(temp_dir)

chktxt = '\n \n\n \n\n\n \t \t\t \t\n  \n   \n    \n     \n\xf0\x9f\x9a\x80 (normal) \xf0\x9f\x98\xb6\xe2\x80\x8d\xf0\x9f\x8c\xab\xef\xb8\x8f (multiple emojis concatenated) \xe2\x9c\x85 \xf0\x9f\xa6\x99\xf0\x9f\xa6\x99 3 33 333 3333 33333 333333 3333333 33333333 3.3 3..3 3...3 \xe1\x9e\x80\xe1\x9e\xb6\xe1\x9e\x93\xe1\x9f\x8b\xe1\x9e\x8f\xe1\x9f\x82\xe1\x9e\x96\xe1\x9e\xb7\xe1\x9e\x9f\xe1\x9f\x81\xe1\x9e\x9f\xe1\x9e\xa2\xe1\x9e\xb6\xe1\x9e\x85\xf0\x9f\x98\x81 ?\xe6\x88\x91\xe6\x83\xb3\xe5\x9c\xa8apple\xe5\xb7\xa5\xe4\xbd\x9c1314151\xe5\xa4\xa9\xef\xbd\x9e ------======= \xd0\xbd\xd0\xb5\xd1\x89\xd0\xbe \xd0\xbd\xd0\xb0 \xd0\x91\xd1\x8a\xd0\xbb\xd0\xb3\xd0\xb0\xd1\x80\xd1\x81\xd0\xba\xd0\xb8 \'\'\'\'\'\'```````""""......!!!!!!?????? I\'ve been \'told he\'s there, \'RE you sure? \'M not sure I\'ll make it, \'D you like some tea? We\'Ve a\'lL'

chktok = tokenizer.encode(chktxt)
chkhsh = sha256(str(chktok).encode()).hexdigest()
print(f'Hash: {chkhsh}')

shutil.rmtree(temp_dir, ignore_errors=True)
