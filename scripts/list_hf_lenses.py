from huggingface_hub import HfApi
REPO_ID='neuronpedia/jacobian-lens'
files = HfApi().list_repo_files(REPO_ID, repo_type='model')
folders = sorted({f.split('/')[0] for f in files if '/' in f and not f.startswith('.')})
for f in folders: print(f)
