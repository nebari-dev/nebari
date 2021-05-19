# Contributing to qhub

:sparkles: :raised_hands:  Welcome to the qhub repository! :sparkles: :raised_hands:

You're probably reading this because you are interested in contributing to qhub. That's great to hear! This document will help you through your journey of open source. Here, you'll get a quick overview of how we organize things and, most importantly, how to get involved.

We welcome all contributions to this project via GitHub issues and pull requests. Please follow these guidelines to make sure your contributions can be easily integrated into the projects. As you start contributing to qhub, don't forget that your ideas are more important than perfect pull requests.

If you have any questions that aren't discussed below, please let us know through one of the many ways to get in touch.

## Table of contents

- [Contributing to qhub](#contributing-to-qhub)
  - [Table of contents](#table-of-contents)
  - [:computer: Contributing through GitHub](#computer-contributing-through-github)
  - [:pencil: Writing in Markdown](#pencil-writing-in-markdown)
  - [:sparkle: Where to start: issues](#sparkle-where-to-start-issues)
    - [Submitting issues](#submitting-issues)
    - [Issue labels](#issue-labels)
  - [:computer: Contributing to the codebase](#computer-contributing-to-the-codebase)
    - [Step-by-step guide to your first contribution](#step-by-step-guide-to-your-first-contribution)

## :computer: Contributing through GitHub

[Git][git] is a handy tool for version control.
[GitHub][github] sits on top of Git and supports collaborative and distributed working.

We know that it can be daunting to start using Git and GitHub if you haven't worked with them in the past, but _qhub_ maintainers are here to help you figure out any of the jargon or confusing instructions you encounter!

To contribute via GitHub, you'll need to set up a free account and sign in.
Here are some [instructions](https://help.github.com/articles/signing-up-for-a-new-github-account/) to help you get going.

## :pencil: Writing in Markdown

GitHub has a helpful page on [getting started with writing and formatting on GitHub](https://help.github.com/articles/getting-started-with-writing-and-formatting-on-github).

Most of the writing that you'll do will be in [markdown][markdown].
You can think of markdown as a few little symbols around your text that will allow GitHub to render the text with a bit of formatting.
For example, you could write words as **bold** (`**bold**`), or in _italics_ (`_italics_`), or as a [link][rick-roll] (`[link](https://youtu.be/dQw4w9WgXcQ)`) to another webpage.

Also, when writing in markdown, please start each new sentence on a new line.
While these formats in the same way as if the new line wasn't included, it makes the [diffs produced during the pull request](https://help.github.com/en/articles/about-comparing-branches-in-pull-requests) review easier to read! :sparkles:

## :sparkle: Where to start: issues

Before you open a new issue, please check the [open issues][qhub-issues]. See if the issue has already been reported or if your idea has already been discussed. If so, it's often better to leave a comment on a current issue, rather than opening a new one. Old issues also often include helpful tips and solutions to common problems.

If you are looking for specific help with qhub or its configuration, check our [Github discussions][qhub-qa].

### Submitting issues

When opening an issue, use a **descriptive title** and provide your environment details (i.e. operating system, Python, Kubernetes and Conda version). Our [issue templates][qhub-templates] help you remember the most important details to include.

There are three issues templates to choose from:

1. **Bug Report**: With this template, create an issue report that can help others fix something that's currently broken.
2. **Documentation**: Use this template to provide feedback on our documentation or suggest additions and improvements.
3. **Feature request**: Is there anything that would make the community work better? Have you spotted something missing in qhub? Use this template to share your feature ideas with the qhub team.

A few more tips:

- **Describing your issue**: Try to provide as many details as possible. What exactly goes wrong? How is it failing? Is there an error? "XY doesn't work" usually isn't that helpful for tracking down problems. Always remember to include the code you ran and if possible, extract only the relevant parts and don't dump your entire script.
This will make it easier for us to reproduce the error. Screenshots are also great ways to demonstrate errors or unexpected behaviours.

- **Sharing long blocks of code or logs**: If you need to include extended code, logs or tracebacks, you can wrap them in `<details> and </details>`. This collapses the content, so it only becomes visible on click, making it easier to read and follow.

### Issue labels

Check our [labels page][qhub-labels] for an overview of the system we use to tag our issues and pull requests.

## :computer: Contributing to the codebase

You don't have to be a Python or Kubernetes pro to contribute, and we're happy to help you get started. If you're new to qhub, an excellent place to start are the issues marked with the [type: good first issue](https://github.com/Quansight/qhub/labels/type%3A%20good%20first%20issue) label, which we use to tag bugs and feature requests that are easy (i.e. low entry-barrier or little in-depth knowledge needed) and self-contained. If you've decided to take on one of these problems and you're making good progress, don't forget to add a quick comment to the issue to assign this to yourself. You can also use the issue to ask questions or share your work in progress.

### Step-by-step guide to your first contribution

Never made an open-source contribution before? Wondering how contributions work in the q-hub world? Here's a quick rundown!

1. Find an issue that you are interested in addressing or a feature you would like to address.
2. Fork the repository associated with the issue to your local GitHub organization.


[qhub-repo]: https://github.com/Quansight/qhub/
[qhub-issues]: https://github.com/Quansight/qhub/issues
[qhub-labels]: https://github.com/Quansight/qhub/labels
[qhub-templates]: https://github.com/Quansight/qhub/issues/new/choose
[qhub-qa]: https://github.com/Quansight/qhub/discussions/categories/q-a
[issue-template]: https://github.com/Quansight/qhub/blob/master/ISSUE_TEMPLATE.md
[git]: https://git-scm.com
[github]: https://github.com
[github-branches]: https://help.github.com/articles/creating-and-deleting-branches-within-your-repository
[github-fork]: https://help.github.com/articles/fork-a-repo
[github-flow]: https://guides.github.com/introduction/flow
[github-mergeconflicts]: https://help.github.com/articles/about-merge-conflicts
[github-pullrequest]: https://help.github.com/articles/creating-a-pull-request
[github-review]: https://help.github.com/articles/about-pull-request-reviews
[github-syncfork]: https://help.github.com/articles/syncing-a-fork
[markdown]: https://daringfireball.net/projects/markdown
[rick-roll]: https://www.youtube.com/watch?v=dQw4w9WgXcQ
[jerry-maguire]: https://media.giphy.com/media/uRb2p09vY8lEs/giphy.gif
[all-contributors]: https://github.com/kentcdodds/all-contributors#emoji-key
