# Cli commands
## ``cli``
## ``init``
 ``kedro mlflow init``: this command is needed to initalize your project. You cannot run any other commands before you run this one once. It performs 2 actions:
    - creates a ``mlflow.yml`` configuration file in your ``conf/base`` folder
    - replace the ``src/PYTHON_PACKAGE/run.py`` file by an updated version of the template. If your template has been modified since project creation, a warning wil be raised. You can either run ``kedro mlflow init --force`` to ignore this warning (but this will erase your ``run.py``) or [set hooks manually](#new-hooks).
## ``ui``
``kedro mlflow ui``: this command opens the mlflow UI (basically launches the ``mlflow ui`` command with the configuration of your ``mlflow.yml`` file)
