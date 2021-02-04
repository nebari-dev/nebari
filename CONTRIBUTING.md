# Contributing to qhub-cloud

:sparkles: :raised_hands:  Welcome to the qhub-cloud repository! :sparkles: :raised_hands:

You're probably reading this because you are interested in contributing to qhub-cloud. That's great to hear! This document will help you through your journey of open source. Here, you'll get a quick overview of we organize things and, most importantly, how to get involved.

We welcome all contributions to this project via GitHub issues and pull requests. Please follow these guidelines to make sure your contributions can be easily integrated into the projects. As you start contributing to qhub-cloud, don't forget that your ideas are more important than perfect pull requests.

If you have any questions that aren't discussed below, please let us know through one of the many ways to get in touch.

## Table of contents

- [Contributing to qhub-cloud](#contributing-to-qhub-cloud)
  - [Table of contents](#table-of-contents)
  - [:computer: Contributing through GitHub](#computer-contributing-through-github)
  - [:pencil: Writing in Markdown](#pencil-writing-in-markdown)
  - [:sparkle: Where to start: issues](#sparkle-where-to-start-issues)
    - [Submitting issues](#submitting-issues)
    - [Issue labels](#issue-labels)

## :computer: Contributing through GitHub

[Git][git] is a really useful tool for version control.
[GitHub][github] sits on top of Git and supports collaborative and distributed working.

We know that it can be daunting to start using Git and GitHub if you haven't worked with them in the past, but _qhub-cloud_ maintainers are here to help you figure out any of the jargon or confusing instructions you encounter!

To contribute via GitHub, you'll need to set up a free account and sign in.
Here are some [instructions](https://help.github.com/articles/signing-up-for-a-new-github-account/) to help you get going.

## :pencil: Writing in Markdown

GitHub has a helpful page on [getting started with writing and formatting on GitHub](https://help.github.com/articles/getting-started-with-writing-and-formatting-on-github).

Most of the writing that you'll do will be in [Markdown][markdown].
You can think of Markdown as a few little symbols around your text that will allow GitHub to render the text with a little bit of formatting.
For example, you could write words as **bold** (`**bold**`), or in _italics_ (`_italics_`), or as a [link][rick-roll] (`[link](https://youtu.be/dQw4w9WgXcQ)`) to another webpage.

Also when writing in Markdown, please start each new sentence on a new line.
While these formats in the same way as if the new line wasn't included, it makes the [diffs produced during the pull request](https://help.github.com/en/articles/about-comparing-branches-in-pull-requests) review easier to read! :sparkles:

## :sparkle: Where to start: issues

Before you open a new issue, please check the [open issues][qhub-cloud-issues]. See if the issue has already been reported or if your idea has already been discussed. If so, it's often better to leave a comment on an existing issue, rather than creating a new one. Old issues also often include helpful tips and solutions to common problems.

If you are looking for specific help with qhub-cloud or its configuration make sure to check our [Github discussions][qhub-cloud-qa].

### Submitting issues

When opening an issue, use a **descriptive title** and provide your environment details (i.e. operating system, Python, Kubernetes and Conda version). Our [issue templates][qhub-cloud-templates] help you remember the most important details to include. 

There are 3 issues templates to choose from:

1. **Bug Report**: With this template, create an issue report that can help others fix something that's currently broken.
2. **Documentation**: Use this template if you want to provide feedback on our documentation or suggest additions and/or improvements.
3. **Feature request**: Is there anything that would make the community work better? Have you spotted something missing in qhub-cloud? Use this template to share your feature ideas with the qhub-cloud team.

A few more tips:

- **Describing your issue**: Try to provide as many details as possible. What exactly goes wrong? How is it failing? Is there an error? "XY doesn't work" usually isn't that helpful for tracking down problems. Always remember to include the code you ran and if possible, extract only the relevant parts and don't dump your entire script.
This will make it easier for us to reproduce the error. Screenshots are also great ways to demonstrate errors or unexpected behaviours.

- **Sharing long blocks of code or logs**: If you need to include long code, logs or tracebacks, you can wrap them in `<details> and </details>`. This collapses the content, so it only becomes visible on click, making the issue easier to read and follow.

### Issue labels

Check our [labels page][qhub-cloud-labels] for an overview of the system we use to tag our issues and pull requests. 

### :computer: Contributing to the codebase

You don't have to be a Python or Kubernetes pro to contribute, and we're happy to help you get started. If you're new to qhub-cloud, a good place to start are the issues marked with the [type: good first issue](https://github.com/Quansight/qhub-cloud/labels/type%3A%20good%20first%20issue) label, which we use to tag bugs and feature requests that are easy and self-contained. If you've decided to take on one of these problems and you're making good progress, don't forget to add a quick comment to the issue to assign this to yourself. You can also use the issue to ask questions, or share your work in progress.

## Making a contribution to the codebase

Never made an open source contribution before? Wondering how contributions work in the nteract world? Here's a quick rundown!

1. Find an issue that you are interested in addressing or a feature that you would like to address.
1. Fork the repository associated with the issue to your local GitHub organization.


[qhub-cloud-repo]: https://github.com/Quansight/qhub-cloud/
[qhub-cloud-issues]: https://github.com/Quansight/qhub-cloud/issues
[qhub-cloud-labels]: https://github.com/Quansight/qhub-cloud/labels
[qhub-cloud-templates]: https://github.com/Quansight/qhub-cloud/issues/new/choose
[qhub-cloud-qa]: https://github.com/Quansight/qhub-cloud/discussions/categories/q-a
[git]: https://git-scm.com
[github]: https://github.com
[github-branches]: https://help.github.com/articles/creating-and-deleting-branches-within-your-repository
[github-fork]: https://help.github.com/articles/fork-a-repo
[github-flow]: https://guides.github.com/introduction/flow
[github-mergeconflicts]: https://help.github.com/articles/about-merge-conflicts
[github-pullrequest]: https://help.github.com/articles/creating-a-pull-request
[github-review]: https://help.github.com/articles/about-pull-request-reviews
[github-syncfork]: https://help.github.com/articles/syncing-a-fork
[issue-template]: https://github.com/Quansight/qhub-cloudblob/master/ISSUE_TEMPLATE.md
[labels-link]: https://github.com/Quansight/qhub-cloudlabels
[labels-approval-request]: https://github.com/Quansight/qhub-cloudlabels/approval%20request
[labels-binderhub]: https://github.com/Quansight/qhub-cloudlabels/binderhub
[labels-book-build]: https://github.com/Quansight/qhub-cloudlabels/book%2Dbuild
[labels-book-dash-feb20]: https://github.com/Quansight/qhub-cloudlabels/book%2Ddash%2Dfeb20
[labels-book-dash-ldn19]: https://github.com/Quansight/qhub-cloudlabels/book%2Ddash%2Dldn2019
[labels-book-dash-mcr19]: https://github.com/Quansight/qhub-cloudlabels/book%2Ddash%2Dmcr2019
[labels-book]: https://github.com/Quansight/qhub-cloudlabels/book
[labels-bug]: https://github.com/Quansight/qhub-cloudlabels/bug
[labels-bug-fixed]: https://github.com/Quansight/qhub-cloudlabels/bug%20fixed
[labels-collaboration-book]: https://github.com/Quansight/qhub-cloudlabels/collaboration%2Dbook
[labels-communication-book]: https://github.com/Quansight/qhub-cloudlabels/communication%2Dbook
[labels-community]: https://github.com/Quansight/qhub-cloudlabels/community
[labels-comms]: https://github.com/Quansight/qhub-cloudlabels/comms
[labels-conflicting-file-error]: https://github.com/Quansight/qhub-cloudlabels/conflicting%2Dfile%2Derror
[labels-dependencies]: https://github.com/Quansight/qhub-cloudlabels/dependencies
[labels-enhancement]: https://github.com/Quansight/qhub-cloudlabels/enhancement
[labels-ethics-book]: https://github.com/Quansight/qhub-cloudlabels/ethics%2Dbook
[labels-events]: https://github.com/Quansight/qhub-cloudlabels/events
[labels-firstissue]: https://github.com/Quansight/qhub-cloudlabels/good%20first%20issue
[labels-helpwanted]: https://github.com/Quansight/qhub-cloudlabels/help%20wanted
[labels-idea-for-discussion]: https://github.com/Quansight/qhub-cloudlabels/idea%2Dfor%2Ddiscussion
[labels-good-first-PR-review]: https://github.com/Quansight/qhub-cloudlabels/good%2Dfirst%2PR%2review
[labels-jupyter]: https://github.com/Quansight/qhub-cloudlabels/jupyter
[labels-project-management]: https://github.com/Quansight/qhub-cloudlabels/project%20management
[labels-newsletter]: https://github.com/Quansight/qhub-cloudlabels/newsletter
[labels-outreach]: https://github.com/Quansight/qhub-cloudlabels/Outreach
[labels-pr-draft]: https://github.com/Quansight/qhub-cloudlabels/PR%3A%20draft
[labels-pr-merged]: https://github.com/Quansight/qhub-cloudlabels/PR%3A%20merged
[labels-pr-partially-approved]: https://github.com/Quansight/qhub-cloudlabels/PR%3A%20partially%2Dapproved
[labels-pr-reviewed-approved]: https://github.com/Quansight/qhub-cloudlabels/PR%3A%20reviewed%2Dapproved
[labels-pr-reviewed-changes-requested]: https://github.com/Quansight/qhub-cloudlabels/PR%3A%20reviewed%2Dchanges%2Drequested
[labels-pr-unreviewed]: https://github.com/Quansight/qhub-cloudlabels/PR%3A%20unreviewed
[labels-project-design-book]: https://github.com/Quansight/qhub-cloudlabels/project%2Ddesign%2Dbook
[labels-question]: https://github.com/Quansight/qhub-cloudlabels/question
[labels-ready-for-merge]: https://github.com/Quansight/qhub-cloudlabels/ready%20for%20merge
[labels-reproducibility-book]: https://github.com/Quansight/qhub-cloudlabels/reproducibility%2Dbook
[labels-research-related-theory]: https://github.com/Quansight/qhub-cloudlabels/research%2Drelated%2Dtheory
[labels-review-request]: https://github.com/Quansight/qhub-cloudlabels/review%20request
[labels-software-skills]: https://github.com/Quansight/qhub-cloudlabels/software%2Dskills
[labels-tools]: https://github.com/Quansight/qhub-cloudlabels/tools
[labels-translation]: https://github.com/Quansight/qhub-cloudlabels/translation
[labels-travel]: https://github.com/Quansight/qhub-cloudlabels/travel
[labels-typo-fix]: https://github.com/Quansight/qhub-cloudlabels/typo%2Dfix
[labels-work-in-progress]: https://github.com/Quansight/qhub-cloudlabels/work%2Din%2Dprogress
[labels-workshops]: https://github.com/Quansight/qhub-cloudlabels/workshops
[markdown]: https://daringfireball.net/projects/markdown
[rick-roll]: https://www.youtube.com/watch?v=dQw4w9WgXcQ
[jerry-maguire]: https://media.giphy.com/media/uRb2p09vY8lEs/giphy.gif
[all-contributors]: https://github.com/kentcdodds/all-contributors#emoji-key