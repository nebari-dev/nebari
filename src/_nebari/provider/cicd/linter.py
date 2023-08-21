import json
import os
import textwrap
from pathlib import Path

import requests

from _nebari.schema import verify


def nebari_validate(config):
    # Gather the output of `nebari validate`.
    print("Validate: info: validating Nebari configuration in nebari-config.yaml")

    def parse_validation(message):
        # this will just separate things for now, but can be enhanced
        return str(message)

    try:
        verify(config)
        msg = "validate: info: successfully validated Nebari configuration"
        print(msg)
        return True, msg, 0

    except BaseException as e:
        msg = "validate: error: failed to validate Nebari configuration."
        print(msg)
        validate_comment = parse_validation(e)
        validate_comment_wrapper = f"\n```\n{validate_comment}\n``` "
        return False, validate_comment_wrapper, 1


def generate_lint_message(config):
    # prep for linting
    pr_config = Path("nebari-config.yaml")
    # lint/validate nebari-config.yaml
    all_pass, messages, validate_code = nebari_validate(config)

    pass_lint = textwrap.dedent(
        """
            This is an automatic response from the Nebari linter.
            I just wanted to let you know that I linted your `nebari-config.yaml` in your PR and I didn't find any
            problems.
            """
    )

    # it should be better to parse this messages first
    bad_lint = (
        textwrap.dedent(
            """
            This is an automatic response from the Nebari linter.
            I just wanted to let you know that I linted your `nebari-config.yaml` in your PR and found some errors:\n"""
        )
        + f"{messages}"
    )

    if not pr_config:
        status = "no configuration file"
        message = textwrap.dedent(
            """
            This is an automatic response from the Nebari linter.
            I was trying to look for the `nebari-config.yaml` file to lint for you, but couldn't find any...
            """
        )

    elif all_pass:
        status = "Success"
        message = pass_lint
    else:
        status = "Failure"
        message = bad_lint

    lint = {
        "message": f"#### `nebari validate` {status} \n" + message,
        "code": validate_code,
    }
    return lint


def comment_on_pr(config):
    lint = generate_lint_message(config)
    message = lint["message"]
    exitcode = lint["code"]

    print(
        "If the comment was not published, the following would "
        "have been the message:\n{}".format(message)
    )

    # comment on PR
    owner, repo_name = os.environ["REPO_NAME"].split("/")
    pr_id = os.environ["PR_NUMBER"]

    token = os.environ["GITHUB_TOKEN"]
    url = f"https://api.github.com/repos/{owner}/{repo_name}/issues/{pr_id}/comments"

    payload = {"body": message}
    headers = {"Content-Type": "application/json", "Authorization": f"token {token}"}
    requests.post(url=url, headers=headers, data=json.dumps(payload))

    return exit(exitcode)
