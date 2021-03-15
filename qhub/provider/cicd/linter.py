import os
import textwrap
import pathlib
import subprocess

import github


def qhub_validate(logger):
    # Gather the output of `qhub validate`.
    logger.info("Validate: info: validating QHub configuration in qhub-config.yaml")

    command = "qhub validate qhub-config.yaml"
    validate_output = subprocess.run([command], shell=True, capture_output=True)
    print(validate_output)
    print(validate_output.returncode)

    def parse_validation(message: str):
        # this will just separate things for now, but can be enhanced
        return message.split(
            'File "/opt/hostedtoolcache/Python/3.8.8/x64/lib/python3.8/site-packages/qhub/cli/validate.py",',
            1,
        )[1]

    if validate_output.returncode == 0:
        msg = "validate: info: successfully validated QHub configuration"
        logger.info(msg)
        return True, msg, validate_output
    else:
        msg = f"validate: error: failed to validate QHub configuration."
        logger.info(msg)
        validate_comment = parse_validation(validate_output.stderr.decode("utf-8"))
        validate_comment_wrapper = f" ```{validate_comment}``` "
        return False, validate_comment_wrapper, validate_output.returncode


def generate_lint_message(repo_owner, repo_name, pr_id, logger):
    gh = github.Github(os.environ["GITHUB_TOKEN"])

    owner = gh.get_user(repo_owner)
    remote_repo = owner.get_repo(repo_name)

    pull_request = remote_repo.get_pull(pr_id)
    if pull_request.state != "open":
        return {}
    mergeable = pull_request.mergeable

    # Raise an error if the PR is not mergeable.
    if not mergeable:
        status = "merge_conflict"
        message = textwrap.dedent(
            """
                This is an automatic response from the QHub-cloud linter. 
                I was trying to look for the QHub-configuration file to lint for you, but it appears we have a merge 
                conflict.
                """
        )

        lint = {"message": f"#### `qhub validate` {status} \n" + message, "code": 1}
        return lint

    def find_config(path):
        for root, dirs, files in os.walk(path):
            if "qhub-config.yaml" in files:
                return os.path.join(root, "qhub-config.yaml")

    # prep for linting
    pr_config = find_config(pathlib.Path().absolute())
    # lint/validate qhub-config.yaml
    all_pass, messages, validate_code = qhub_validate(logger)

    pass_lint = textwrap.dedent(
        f"""
            This is an automatic response from the QHub-cloud linter.
            I just wanted to let you know that I linted your `qhub-config.yaml` in your PR and I didn't find any 
            problems.
            """
    )

    # it should be better to parse this messages first
    bad_lint = (
        textwrap.dedent(
            f"""
            This is an automatic response from the QHub-cloud linter. 
            I just wanted to let you know that I linted your `qhub-config.yaml` in your PR and found some errors.
            Here's what I've got... \n"""
        )
        + f"{messages}"
    )

    if not pr_config:
        status = "no configuration file"
        message = textwrap.dedent(
            """
            This is an automatic response from the qQHub-cloud linter.
            I was trying to look for the `qhub-config.yaml` file to lint for you, but couldn't find any...
            """
        )

    elif all_pass:
        status = "Success"
        message = pass_lint
    else:
        status = "Failure"
        message = bad_lint

    pull_request = remote_repo.get_pull(pr_id)
    if pull_request.state == "open":
        lint = {
            "message": f"#### `qhub validate` {status} \n" + message,
            "code": validate_code,
        }
    else:
        lint = {}
    return lint


def comment_on_pr(owner, repo_name, pr_id, logger):
    lint = generate_lint_message(owner, repo_name, pr_id, logger)
    message = lint["message"]
    exit_code = lint["code"]

    gh = github.Github(os.environ["GITHUB_TOKEN"])

    user = gh.get_user(owner)
    repo = user.get_repo(repo_name)
    issue = repo.get_issue(pr_id)

    comments = list(issue.get_comments())

    comment_owners = [comment.user.login for comment in comments]
    my_last_comment = None
    my_login = "github-actions[bot]"

    if my_login in comment_owners:
        my_comments = [
            comment for comment in comments if comment.user.login == my_login
        ]
        if len(my_comments) > 0:
            my_last_comment = my_comments[-1]

    # Only comment if we haven't before, or if the message we have is different.
    if my_last_comment is None or my_last_comment.body != message:
        my_last_comment = issue.create_comment(message)

    return my_last_comment, exit_code


def qhub_linter():
    import logging

    logger = logging.getLogger("qhub-cloud.linting")

    owner, repo_name = os.environ["REPO_NAME"].split("/")
    pr_id = os.environ["PR_ID"]

    lint_info = comment_on_pr(owner, repo_name, pr_id, logger=logger)

    print(
        "Comments not published, but the following would "
        "have been the message:\n{}".format(lint_info[0])
    )

    return exit(lint_info[1])
