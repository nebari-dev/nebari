import pathlib
import collections
import json

import yaml
from cookiecutter.main import cookiecutter
from cookiecutter.generate import generate_files


def render_default_template(output_directory, config_filename=None, force=False):
    import qhub_ops

    input_directory = pathlib.Path(qhub_ops.__file__).parent / "template"
    render_template(input_directory, output_directory, config_filename, force=force)


def render_template(
    input_directory, output_directory, config_filename=None, force=False
):
    # would be nice to remove assumption that input directory
    # is in local filesystem
    input_directory = pathlib.Path(input_directory)
    if not input_directory.is_dir():
        raise ValueError(f"input directory={input_directory} is not a directory")

    output_directory = pathlib.Path(output_directory)
    if not output_directory.is_dir():
        raise ValueError(f"output directory={output_directory} is not a directory")

    prompt_filename = input_directory / "hooks" / "prompt_gen_project.py"

    if config_filename is not None:
        filename = pathlib.Path(config_filename)

        if not filename.is_file():
            raise ValueError(f"cookiecutter configuration={filename} is not filename")

        with filename.open() as f:
            config = yaml.safe_load(f)

        with (input_directory / "cookiecutter.json").open() as f:
            config = collections.ChainMap(config, json.load(f))

        generate_files(
            repo_dir=str(input_directory),
            context={"cookiecutter": config},
            output_dir=str(output_directory),
            overwrite_if_exists=force,
        )
    elif prompt_filename.is_file():
        with prompt_filename.open() as f:
            content = f.read()

        global_context = {}
        exec(content, global_context, global_context)
        config = global_context["COOKIECUTTER_CONFIG"]

        cookiecutter(
            str(input_directory),
            no_input=True,
            extra_context=config,
            output_dir=str(output_directory),
            overwrite_if_exists=force,
        )
    else:
        cookiecutter(
            str(input_directory),
            output_dir=str(output_directory),
            overwrite_if_exists=force,
        )
