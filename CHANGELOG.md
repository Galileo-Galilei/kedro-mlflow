# Upcoming release
## Major features and improvements
## Bug fixes and other changes
## Breaking changes to the API

# 0.2.0
## Major features and improvements
- Bump the codebase test coverage to 100% to improve stability
- Improve rendering of template with a trailing newline to make them  ```black```-valid
- Add a ``PipelineML.extract_pipeline_artifacts`` methods to make artifacts retrieving easier for a given pipeline
- Use an official kedro release (``>0.16.0, <0.17.0``) instead of the development branch

## Bug fixes and other changes
- Add ```debug``` folder to gitignore for to avoid involuntary data leakage
- Remove the inadequate warning *"You have not initialized your project yet"* when calling ```kedro mlflow init```
- Remove useless check to see if the commands are called inside a Kedro project since the commands are dynamically displayed based on whether the call is made inside a kedro project or not
- Fix typos in error messages
- Fix hardcoded path to the ``run.py`` template
- Make not implemented function raise a ``NotImplementError`` instead of failing silently
- Fix wrong parsing when the ``mlflow_tracking_uri`` key of the ``mlflow.yml`` configuration file was an absolute local path
- Remove unused ``KedroMlflowContextClass``
- Force the ``MlflowPipelineHook.before_pipeline_run`` method to set the ``mlflow_tracking_uri`` to the one from the configuration to enforce configuration file to be prevalent on environment variables or current active tracking uri in interactive mode
- Fix wrong environment parsing case when passing a conda environment as a python dictionary in ``MlflowPipelineHook``
- Fix wrong artifact logging of ``MlflowDataSet`` when a run was already active and the save method was called in an interactive python session.
- Force the user to declare an ``input_name`` for a ``PipelineMl`` object to fix difficult inference of what is the pipeline input
- Update ``run.py`` template to fit kedro new one.
- Force ``_generate_kedro_commands`` to separate an option and its arguments with a "=" sign for readibility

## Breaking changes to the API
- ``hooks``, ``context`` and ``cli`` folders are moved to ``framework`` to fit kedro new folder architecture
- Rename ``get_mlflow_conf`` in ``get_mlflow_config`` for consistency (with ``ConfigLoader``, ``KedroMlflowConfig``...)
- Rename keys of ``KedroMlflowConfig.to_dict()`` to remove the "_opts" suffix for consistency with the ``KedroMlflowConfig.from_dict`` method

# 0.1.0
## Major features and improvements
- Add cli ``kedro mlflow init`` to udpdate the template and ``kedro mlflow ui`` to open ``mlflow`` user interface with your project configuration
- Add hooks ``MlflowNodeHook`` and ``MlflowPipelineHook`` for parameters autologging and model autologging
- Add ``MlflowDataSet`` for artifacts autologging
- Add ``PipelineMl`` class and its ``pipeline_ml`` factory for pipeline packaging and service
