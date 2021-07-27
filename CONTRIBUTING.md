# Development workflow

The current workflow is the following:

1. Open an issue to describe your feature request or your bug fix with a detailed explanation of what you want to achieve.
2. Fork the repo
3. Develop locally:
    - Install the precommit file (`pip install pre-commit`, then `pre-commit install`)
    - Create a branch based on the master branch (``git checkout -b <prefix-branchname> master``)
    - Create a conda environment (conda create -n <your-env-name> python==3.7)
    - Activate this environment (`conda activate <your-env-name>`)
    - Install the extra dependencies for tests (`pip install kedro-mlflow[dev,test]`)
    - Apply your changes
    - Run pre-commit (black linting, flake8 errors, isort with ``pre-commit run``)
4. Submit your changes:
    - Ensure test coverage is still 100%
    - Update documentation accordingly
    - Update `CHANGELOG.md` according to ["Keep a Changelog" guidelines](https://keepachangelog.com/en/1.0.0/)
    - Squash all the changes within a single commit as much as possible, and ensure the commit message has the format "[:gitmoji_icon:](https://gitmoji.dev/) Informative description (``#<issue-number>``)"
    - Rebase your branch on ``master`` to ensure linear history
    - Open a pull request against ``master``
5. Ask for review:
    - Assign the review @Galileo-Galilei
    - Wait for review
    - Resolve all discussions (go back to step 3.)
6. The PR will be merged as soon as possible

**We reserve the right to take over (suppress or modify) PR that do not match the workflow or are abandoned.**


# Release workflow

1. Check the issues:
    - Ensure all the [release issues](https://github.com/Galileo-Galilei/kedro-mlflow/milestones) are completed. Eventually move the not addressed yet issues to a further release.
    - Create a [new milestone](https://github.com/Galileo-Galilei/kedro-mlflow/milestones)
2. Create the release candidate:
    - Go to the [create-release-candidate action](https://github.com/Galileo-Galilei/kedro-mlflow/actions?query=workflow%3Acreate-release-candidate)
    - Click "Run workflow"
    - Enter the part of the version to bump (one of `<major>.<minor>.<patch>`)
3. If the workflow has run sucessfully:
    - Go to the newly openened PR named "[Release candidate `<version>`](https://github.com/Galileo-Galilei/kedro-mlflow/pulls)"
    - Check that changelog and version have been properly updated.
    - *(If everything is normal, skip this step)* Eventually pull the branch and make changes if necessary
    - Merge the PR to master
4. Checkout the [publish workflow](https://github.com/Galileo-Galilei/kedro-mlflow/actions?query=workflow%3Apublish) to see if:
    - The package has been uploaded on PyPI sucessfully
    - A Github release has been created
5. If the pipeline has failed, please raise an issue to correct the CI, and ensure merge on master manually.
