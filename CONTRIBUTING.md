# Contributing to QHub

:sparkles: :raised_hands: Welcome to the QHub repository! :sparkles: :raised_hands:

Everyone is welcome to contribute, and we value everybody's contribution. Code is not the only way to help the community. Your choices aren't limited to programming; as you can see
below, there are many areas where we need **your** help. Answering questions, helping others, reaching out and improving the documentation is immensely valuable to the community.

Whichever way you choose to contribute, please be mindful of respecting our code of conduct.

This document will help you through your journey of open source. Here, you'll get a quick overview of how we organize things and, most importantly, how to get involved.

## Table of contents

- [Contributing to QHub](#contributing-to-qhub)
  - [Table of contents](#table-of-contents)
  - [🏷 Where to start: issues](#-where-to-start-issues)
    - [Submitting issues](#submitting-issues)
    - [Issue labels](#issue-labels)
  - [:computer: Contributing to the codebase](#computer-contributing-to-the-codebase)
    - [Development process - short summary](#development-process---short-summary)
      - [If you are a first-time contributor](#if-you-are-a-first-time-contributor)
      - [Submitting your contribution](#submitting-your-contribution)
      - [Review process](#review-process)
      - [Document changes](#document-changes)
      - [Cross referencing issues](#cross-referencing-issues)

## 🏷 Where to start: issues

Before you open a new issue, please check the [open issues][qhub-issues]. See if the issue has already been reported or if your idea has already been discussed. If so, it's often
better to leave a comment on a current issue rather than opening a new one. Old issues also often include helpful tips and solutions to common problems.

If you are looking for specific help with QHub or its configuration, check our [Github discussions][qhub-qa].

### Submitting issues

When opening an issue, give it a **descriptive title** and provide as much information as possible. Our [issue templates][qhub-templates] help you remember the most important
details to include.

There are three issues templates to choose from:

1. **Bug Report**: With this template, create an issue report that can help others fix something currently broken.
2. **Documentation**: Use this template to provide feedback on our documentation or suggest additions and improvements.
3. **Feature request**: Is there anything to make the community work better? Have you spotted something missing in QHub? Use this template to share your feature ideas with the QHub
   team.

A few more tips:

- **Describing your issue**: Try to provide as many details as possible. What exactly goes wrong? How is it failing? Is there an error? "XY doesn't work" usually isn't that helpful
  for tracking down problems. Always remember to include the code you ran, and if possible, extract only the relevant parts, and don't dump your entire script. This will make it
  easier for us to reproduce the error. Screenshots are also great ways to demonstrate errors or unexpected behaviours.

- **Sharing long blocks of code or logs**: If you need to include extended code, logs or tracebacks, you can wrap them in `<details> and </details>`. This collapses the content, so
  it only becomes visible on click, making it easier to read and follow.

- **Suggesting a new feature:** When suggesting a new feature, please also add details on how this new feature might impact the users' and developers' workflow.

### Issue labels

Check our [labels page][qhub-labels] for an overview of the system we use to tag our issues and pull requests.

## :computer: Contributing to the codebase

You don't have to be a Python or Kubernetes pro to contribute, and we're happy to help you get started. If you're new to QHub, an excellent place to start are the issues marked
with the [type: good first issue](https://github.com/Quansight/QHub/labels/type%3A%20good%20first%20issue) label, which we use to tag bugs and feature requests that require
low-effort (i.e. low entry-barrier or little in-depth knowledge needed) and self-contained. If you've decided to take on one of these problems and you're making good progress,
don't forget to add a quick comment to the issue to assign this to yourself. You can also use the issue to ask questions or share your work in progress.

### Development process - short summary

Never made an open-source contribution before? Wondering how contributions work in the QHub world? Here's a quick rundown!

#### If you are a first-time contributor

1. Go to the [QHub repository][qhub-repo] and click the `fork` button on the top-right corner to create your own copy of the project.

2. Clone the project to your local computer:

   ```bash
   git clone https://github.com/your-username/QHub.git
   ```

3. Change into the directory:

   ```bash
   cd Qhub
   ```

4. Add the upstream repository:

   ```bash
   git remote add upstream https://github.com/Quansight/QHub.git
   ```

Now using the command `git remote -v` will show two remote repositories:

- `upstream`: which refers to the `QHub` repository on Github.
- `origin`: which refers to your personal fork

#### Develop your contribution

1. Find an issue you are interested in addressing or a feature you would like to address.

2. Pull the latest changes from upstream

   ```bash
   git checkout main
   git pull upstream main
   ```

3. Create a branch for the feature you want to work on. Since the branch name will appear in the merge message, use a sensible, self-explanatory name:

   ```bash
   git branch feature/<feature name>
   git switch feature/<feature name>
   # this is an alternative to the git checkout -b feature/<feature name> command
   ```

4. Commit locally as you progress (`git add` and `git commit`). Use an adequately formatted commit message, write tests that fail before your change and pass afterwards, run all
   the tests locally. Be sure to document any changed behaviour in docstrings.

#### Submitting your contribution

1. Push your changes back to your fork on GitHub:

   ```bash
   git push origin feature/<feature name>
   ```

2. Enter your GitHub username and password (repeat contributors or advanced users can remove this step by connecting to GitHub with SSH).

3. Go to GitHub. The new branch will show a green **Pull Request** button. Make sure the title and message are clear, concise, and self-explanatory. Then click the button to submit
   it.

:warning: - If your commit introduces a new feature or changes functionality, please ensure you first create an open Pull Request on our repo with `WIP` (work in progress) in the
title and marked as draft, explaining what you want to do. That way we can discuss it to be sure it makes sense for QHub. Or start by creating an issue and indicate that you would
be interested in solving the problem yourself. This is generally not necessary for bug fixes, documentation updates, etc. However, if you do not get any reaction, do feel free to
ask for a review.

#### Review process

Reviewers (the other developers and interested community members) will write inline and/or general comments on your Pull Request (PR) to help you improve its implementation,
documentation and style. Every developer working on the project has their code reviewed, and we've come to see it as a friendly conversation from which we all learn and the overall
code quality benefits. Therefore, please don't let the review discourage you from contributing: its only aim is to improve the quality of the project, not to criticize (we are,
after all, very grateful for the time you're donating!).

To update your PR, make your changes on your local repository, commit, run tests, and only if they succeed, push to your fork. The PR will update automatically as soon as those
changes are pushed up (to the same branch as before). If you have no idea how to fix the test failures, you may push your changes anyway and ask for help in a PR comment.

Various continuous integration (CI) pipelines are triggered after each PR update to build artefacts, run unit tests, and check the coding style of your branch. The CI tests must
pass before your PR can be merged. If CI fails, you can find why by clicking on the "failed" icon (red cross) and inspecting the build and test log. To avoid overuse and waste of
this resource, test your work locally before committing.

Before merging, a PR must be approved by at least one core team member. Approval means the core team member has carefully reviewed the changes, and the PR is ready for merging.

#### Document changes

Beyond changes to a functions docstring and possible description in the general documentation, if your change introduces any user-facing modifications, they may need to be
mentioned in the release notes.

#### Cross referencing issues

If the PR relates to any issues, you can add the text `xref gh-xxxx` where `xxxx` is the issue number to GitHub comments. Likewise, if the PR solves an issue, replace the `xref`
with `closes`, `fixes` or any other flavours [github accepts](https://help.github.com/en/articles/closing-issues-using-keywords).

In the source code, be sure to preface any issue or PR reference with gh-xxxx.

<!-- Links -->

[qhub-issues]: https://github.com/Quansight/QHub/issues
[qhub-labels]: https://github.com/Quansight/QHub/labels
[qhub-qa]: https://github.com/Quansight/QHub/discussions/categories/q-a
[qhub-repo]: https://github.com/Quansight/QHub/
[qhub-templates]: https://github.com/Quansight/QHub/issues/new/choose
