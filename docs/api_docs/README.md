# Nebari API docs

The Nebari API docs are generated from this repo, then merged into the nebari-docs repo via PR opened by GitHub Actions.

## Environment

From the root of the repo:

```bash
pip install -e ".[docs]"
```

## Workflow

The docs may be built manually through the following workflow, or executed as part of an autoupdate via GH Actions CI.

The workflow described below will create the API docs and run a formatting script to do a bit of cleanup.

```bash
# work out of the api_docs directory in the nebari repo
cd docs/api_docs/
# auto generate the api docs
pydoc-markdown -I "../../" -p nebari --render-toc > api_temp.md
# make formatting modifications and copy into the docs repo
python api_doc_mods.py --autogen_path api_temp.md --outpath api_doc.md
# run linting and formatting
pre-commit run --files api_doc.md
```
