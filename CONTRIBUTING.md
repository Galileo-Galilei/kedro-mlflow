# Development workflow

The current workflow is the following:

1. Fork the repo
2. Install the precommit file
3. Open an issue to describe your feature request or your bug fix with detailed explanation of what you
4. Create a branch based on the develop branch (``git checkout -b <prefix-branchname> develop``)
5. Make your changes
6. Run precommit (black linting, flake8 errors, isort)
7. Ensure test coverage is still 100%
8. Update documentation accordingly
9. Update CHANGELOG.md
10. Squash all the changes within a single commit as smuch as possible, and ensure the commit message has the format "FIX ``#<issue-number>`` - Informative description"
11. Rebase your branch on ``develop`` to ensure linear history
12. Open a merge request against ``develop``
13. Ask for review
14. Resolve all discussions
15. The PR will be merged as soon as possible

We reserve the right to take over (suppress or modify) PR that do not match the workflow or are abandoned.
