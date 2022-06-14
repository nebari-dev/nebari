---
name: Release Checklist
about: For maintainers only.
title: '[RELEASE] <version>'
labels:
 - 'type: release 🏷'
assignees: ''

---

# Release Checklist

## Release details

Scheduled release date - <yyyy/mm/dd>

Release captain responsible - <@gh_username>


## Starting point - a new release is out

- [x] Create *this* issue to track and discuss the upcoming release.
- [ ] Use the previous release issue for any final release-specific discussions, then close.
  - This can be a good time to debrief and discuss improvements to the release process.


## Looking forward - planning

- [ ] [Create milestone for next release](https://github.com/Quansight/qhub/milestones) (if it doesn't already exist) and link it back here.
- [ ] Triage `bugs` to determine what be should included in the release and add it to the milestone.
- [ ] What new features, if any, will be included in the release and add it to the milestone.
  - This will be, in large part, determined by the roadmap.
  - Is there a focus for this release (i.e. UX/UI, stabilitation, etc.)?


## Pre-release process

- [ ] Decide on a date for the release.
  - What outstanding issues need to be addressed?
  - Has documentation been updated appropriately?
  - Are there any breaking changes that should be highlighted?
  - Are there any upstream releases we are waiting on?
  - [Do we need to update the `dask` versions in the `qhub-dask`?](https://github.com/conda-forge/qhub-dask-feedstock/blob/main/recipe/meta.yaml#L13-L16)
  - Will there be an accompanying blog post?
- [ ] Prepare for the release.
  - [ ] Announce build freeze.
  - [ ] Release Candidate (RC) cycle.
    - Is this a hotfix?
      - [ ] Create a new branch off of the last version tag.
        - Use this branch to cut the pre-release and the "official" release.
      - [ ] `git cherry-pick` the commits that should be included.
    - [ ] [Perform end-to-end testing.](https://docs.qhub.dev/en/latest/source/dev_guide/release.html#pre-release-checklist)
      - For minor releases, relying on the end-to-end integration tests might suffice.
    - [ ] [Cut RC via GHA release workflow (w/ "This is a pre-release" checked).](https://github.com/Quansight/qhub/releases/new)
    - [ ] End-user validation.
      - If possible, pull in volunteers to help test.
      - (Repeat steps if necessary)
  - [ ] [Update `RELEASE.md` notes.](https://github.com/Quansight/qhub/blob/main/RELEASE.md)


## Cut the official release

- [ ] [Tag, build and push docker images](https://github.com/nebari-dev/nebari-docker-images/releases/new)
- [ ] [Update and cut release for `qhub-dask` meta package on Conda-Forge.](https://github.com/conda-forge/qhub-dask-feedstock)
- [ ] [Cut Test PyPI release via manual `workflow_dispatch`.](https://github.com/Quansight/qhub/actions/workflows/test-release.yaml)
- [ ] [Cut PyPI release via GHA release workflow.](https://github.com/Quansight/qhub/releases/new)
    - Copy release notes from `RELEASE.md`.
- [ ] [Merge automated release PR for `qhub` on Conda-Forge.](https://github.com/conda-forge/qhub-feedstock)
