# Nebari API docs

The Nebari API docs are generated from this repo, then merged into the nebari-docs repo via PR opened by GitHub Actions. 

## Environment


```bash
pip install -e ".[docs]"
```

## Workflow

The docs may be built manually through the following workflow, or executed as part of an autoupdate via GH Actions CI. 

```bash

git clone git@github.com:nebari-dev/nebari-docs.git 
cd nebari-docs/docs/

cd docs/api_docs/

pydoc-markdown -I "../../" -p qhub --render-toc > api_temp.md

python api_doc_mods.py --autogen_path api_temp.md --outpath ../../nebari-docs/docs/docs/references/api_docs.md

cd ../../nebari-docs/docs/docs/references

git diff api_docs.md
```
