from __future__ import annotations
import argparse
from pathlib import Path
from huggingface_hub import snapshot_download
REPO_ID='neuronpedia/jacobian-lens'
p=argparse.ArgumentParser(); p.add_argument('--model-folder', required=True); p.add_argument('--out', default='lenses')
a=p.parse_args()
snapshot_download(repo_id=REPO_ID, repo_type='model', allow_patterns=[f'{a.model_folder}/**'], local_dir=a.out)
print(f'Downloaded {a.model_folder} into {Path(a.out)/a.model_folder}')
print('Find lens files with: find lenses/%s -name "*.pt" -print' % a.model_folder)
