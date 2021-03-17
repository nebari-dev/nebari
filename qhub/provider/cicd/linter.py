import os
import json
import textwrap
import pathlib
import subprocess
import requests


def qhub_validate(logger):
    # Gather the output of `qhub validate`.
    logger.info("Validate: info: validating QHub configuration in qhub-config.yaml")

    command = "qhub validate qhub-config.yaml"
    validate_output = subprocess.run([command], shell=True, capture_output=True)

    def parse_validation(message: str):
        # this will just separate things for now, but can be enhanced
        return message.split('provider',1)[1]

    if validate_output.returncode == 0:
        msg = "validate: info: successfully validated QHub configuration"
        logger.info(msg)
        return True, msg, validate_output.returncode
    else:
        msg = "validate: error: failed to validate QHub configuration."
        logger.info(msg)
        validate_comment = parse_validation(validate_output.stderr.decode("utf-8"))
        validate_comment_wrapper = f" ```{validate_comment}``` "
        return False, validate_comment_wrapper, validate_output.returncode


def generate_lint_message(logger):

    def find_config(path):
        for root, dirs, files in os.walk(path):
            if "qhub-config.yaml" in files:
                return os.path.join(root, "qhub-config.yaml")

    # prep for linting
    pr_config = find_config(pathlib.Path().absolute())
    # lint/validate qhub-config.yaml
    all_pass, messages, validate_code = qhub_validate(logger)

    pass_lint = textwrap.dedent(
            """
            This is an automatic response from the QHub-cloud linter.
            I just wanted to let you know that I linted your `qhub-config.yaml` in your PR and I didn'\''t find any
            problems.
            """
    )

    # it should be better to parse this messages first
    bad_lint = (
        textwrap.dedent(
            """
            This is an automatic response from the QHub-cloud linter.
            I just wanted to let you know that I linted your `qhub-config.yaml` in your PR and found some errors:\n"""
        )
        + f"{messages}"
    )

    if not pr_config:
        status = "no configuration file"
        message = textwrap.dedent(
            """
            This is an automatic response from the QHub-cloud linter.
            I was trying to look for the `qhub-config.yaml` file to lint for you, but couldn'\''t find any...
            """
        )

    elif all_pass:
        status = "Success"
        message = pass_lint
    else:
        status = "Failure"
        message = bad_lint

    lint = {
            "message": f"#### `qhub validate` {status} \n" + message,
            "code": validate_code,
        }
    return lint

def make_comment(message):
    # make PR
    owner, repo_name = os.environ['REPO_NAME'].split('/')
    pr_id = os.environ['PR_NUMBER']

    token = os.environ['GITHUB_TOKEN']
    url = f"https://api.github.com/repos/{owner}/{repo_name}/issues/{pr_id}/comments"
    
    payload = {'body':message}
    headers = {'Content-Type':'application/json', 'Authorization':f'token {token}'}
    requests.post(url=url, headers=headers, data=json.dumps(payload))

def qhub_linter():
    import logging

    logger = logging.getLogger("qhub-cloud.linting")
    lint = generate_lint_message(logger)

    print(
        "If the comment was not published, the following would "
        "have been the message:\n{}".format(lint['message'])
    )
    make_comment(lint['message'])
   
    return exit(lint['code'])