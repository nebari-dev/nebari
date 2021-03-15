from glob import glob
import os
import textwrap
import time
import tempfile
import shutil
import logging
import pathlib
import subprocess

from git import GitCommandError, Repo
import github

# from .utils import tmp_directory

LOGGER = logging.getLogger("qhub-cloud.linting")


def find_config(path):
    # in the case where the file location can't be easily reached
    for root, dirs, files in os.walk(path):
        if 'qhub-config.yaml' in files:
            return os.path.join(root, 'qhub-config.yaml')


def parse_validation(message: str):
    # this will just separate things for now, but can be enhanced
    return message.split('File "/opt/hostedtoolcache/Python/3.8.8/x64/lib/python3.8/site-packages/qhub/cli/validate.py",', 1)[1]


def qhub_validate():
    # Gather the output of `qhub validate`.
    LOGGER.info('Validate: info: validating QHub configuration in qhub-config.yaml')

    command = 'qhub validate qhub-config.yaml'
    validate_output = subprocess.run([command], shell=True, capture_output=True)
    print(validate_output)
    print(validate_output.returncode)

    if validate_output.returncode == 0:
        msg = 'validate: info: successfully validated QHub configuration'
        LOGGER.info(msg)
        return True, msg, validate_output
    else:
        msg = f'validate: error: failed to validate QHub configuration.'
        validate_comment = parse_validation(validate_output.stderr.decode('utf-8'))
        validate_comment_wrapper = f" ```{validate_comment}``` "
        return False, validate_comment_wrapper, validate_output.returncode


def generate_lint_message(repo_owner, repo_name, pr_id):
    gh = github.Github(os.environ['GITHUB_TOKEN'])

    owner = gh.get_user(repo_owner)
    remote_repo = owner.get_repo(repo_name)

    pull_request = remote_repo.get_pull(pr_id)
    if pull_request.state != "open":
        return {}
    mergeable = pull_request.mergeable

    # Raise an error if the PR is not mergeable.
    if not mergeable:
        status = 'merge_conflict'
        message = textwrap.dedent("""
                This is an automatic response from the QHub-cloud linter. 
                I was trying to look for the QHub-configuration file to lint for you, but it appears we have a merge 
                conflict.
                """)

        lint = {'message': f'#### `qhub validate` {status} \n' + message, 'code': 1}
        return lint

    # prep for linting
    pr_config = find_config(pathlib.Path().absolute())
    # lint/validate qhub-config.yaml
    all_pass, messages, validate_code = qhub_validate()

    pass_lint = textwrap.dedent(f"""
            This is an automatic response from the QHub-cloud linter.
            I just wanted to let you know that I linted your `qhub-config.yaml` in your PR and I didn't find any 
            problems.
            """)

    bad_lint = textwrap.dedent(f"""
            This is an automatic response from the QHub-cloud linter. 
            I just wanted to let you know that I linted your `qhub-config.yaml` in your PR and found some errors.
            Here's what I've got... \n""") + f"{messages}"
    # it should be better to parse this 'messages' first (user friendly)

    if not pr_config:
        status = 'no configuration file'
        message = textwrap.dedent("""
            This is an automatic response from the qQHub-cloud linter.
            I was trying to look for the `qhub-config.yaml` file to lint for you, but couldn't find any...
            """)

    elif all_pass:
        status = 'Success'
        message = pass_lint
    else:
        status = 'Failure'
        message = bad_lint

    pull_request = remote_repo.get_pull(pr_id)
    if pull_request.state == "open":
        lint = {'message': f'#### `qhub validate` {status} \n' + message, 'code': validate_code}
    else:
        lint = {}

    return lint


def comment_on_pr(owner, repo_name, pr_id, message):
    my_last_comment = None
    bot = 'github-actions[bot]'

    # github API config
    github_token = os.environ['GITHUB_TOKEN']
    gh = github.Github(github_token)

    user = gh.get_user(owner)
    repo = user.get_repo(repo_name)
    issue = repo.get_issue(pr_id)

    comments = list(issue.get_comments())
    comment_owners = [comment.user.login for comment in comments]
    
    if bot in comment_owners:
        # look for the bot last comments
        my_comments = [
            comment for comment in comments
            if comment.user.login == bot]
        if len(my_comments) > 0:
            my_last_comment = my_comments[-1]

    # Only comment if we haven't before, or if the message we have is different.
    if my_last_comment is None or my_last_comment.body != message:
        my_last_comment = issue.create_comment(message)

    return my_last_comment


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('repo')
    parser.add_argument('pr', type=int)
   
    args = parser.parse_args()
    owner, repo_name = args.repo.split('/')

    lint = generate_lint_message(owner, repo_name, args.pr)

    comment_on_pr(owner, repo_name, args.pr, lint['message'])
    print('The following correspond to the message contents:\n{}'.format(lint['message']))
    
    return exit(lint['code'])


if __name__ == '__main__':
    main()