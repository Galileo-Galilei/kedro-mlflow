---
name: Bug report
about: If something isn't working
title: '<Title>'
labels: 'Issue: Bug Report'
assignees: ''

---

**_If you like the repo, please give it a :star:_**

## Description

Short description of the problem here.

## Context

How has this bug affected you? What were you trying to accomplish?

## Steps to Reproduce

Please provide a detailed description. A Minimal Reproducible Example would really help to solve your issue faster (see this [Stack Overflow thread](https://stackoverflow.com/help/minimal-reproducible-example) to see how to create a good "reprex"). A link to a github repo is even better.

1. [First Step]
2. [Second Step]
3. [And so on...]

## Expected Result

Tell us what should happen.

## Actual Result

Tell us what happens instead.

```
-- If you received an error, place it here.
```

```
-- Separate them if you have more than one.
```

## Your Environment

Include as many relevant details about the environment in which you experienced the bug:

* `kedro` and `kedro-mlflow` version used (`pip show kedro` and `pip show kedro-mlflow`):
* Python version used (`python -V`):
* Operating system and version:

## Does the bug also happen with the last version on master?

The plugin is still in early development and known bugs are fixed as soon as we can. If you are lucky, your bug is already fixed on the `master` branch which is the most up to date. This branch contains our more recent development unpublished on PyPI yet.

In your environment, please try:

```bash
pip install --upgrade git+https://github.com/Galileo-Galilei/kedro-mlflow
```

And check if you can to reproduce the error. If you can't, just wait for the next release or use the master branch at your own risk!
