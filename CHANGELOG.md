# Changelog

## [Unreleased]

### Added

- Add dataset ``MlflowMetricsDataSet`` for metrics logging ([#9](https://github.com/Galileo-Galilei/kedro-mlflow/issues/9)) and update documentation for metrics.
- Add CI workflow `create-release` to ensure release consistency and up-to-date CHANGELOG. ([#57](https://github.com/Galileo-Galilei/kedro-mlflow/issues/57), [#68](https://github.com/Galileo-Galilei/kedro-mlflow/pull/68))
- Add templates for issues and pull requests ([#57](https://github.com/Galileo-Galilei/kedro-mlflow/issues/57), [#68](https://github.com/Galileo-Galilei/kedro-mlflow/pull/68))

### Fixed

- Versioned datasets artifacts logging are handled correctly ([#41](https://github.com/Galileo-Galilei/kedro-mlflow/issues/41))
- MlflowDataSet handles correctly datasets which are inherited from AbstractDataSet ([#45](https://github.com/Galileo-Galilei/kedro-mlflow/issues/45))
- Change the test in `_generate_kedro_command` to accept both empty `Iterable`s(default in CLI mode) and `None` values (default in interactive mode) ([#50](https://github.com/Galileo-Galilei/kedro-mlflow/issues/50))
- Force to close all mlflow runs when a pipeline fails. It prevents further execution of the pipeline to be logged within the same mlflow run_id as the failing pipeline. ([#10](https://github.com/Galileo-Galilei/kedro-mlflow/issues/10))
- Fix various documentation typos ([#34](https://github.com/Galileo-Galilei/kedro-mlflow/pull/34), [#35](https://github.com/Galileo-Galilei/kedro-mlflow/pull/35), [#36](https://github.com/Galileo-Galilei/kedro-mlflow/pull/36) and more)
- Update README (add badges for readibility, add a "main contributors" section to give credit, fix typo in install command, link to milestones for more up-to-date priorities) ([#57](https://github.com/Galileo-Galilei/kedro-mlflow/issues/57), [#68](https://github.com/Galileo-Galilei/kedro-mlflow/pull/68))
- Fix bug in CI deployment workflow and rename it to `publish` ([#57](https://github.com/Galileo-Galilei/kedro-mlflow/issues/57), [#68](https://github.com/Galileo-Galilei/kedro-mlflow/pull/68))
- Fix a bug in `MlflowDataSet` which sometimes failed to log on remote storage (S3, Azure Blob storage) with underlying `log_artifacts` when the kedro's `AbstractDataset._filepath` was a `pathlib.PurePosixPath` object instead of a string ([#74](https://github.com/Galileo-Galilei/kedro-mlflow/issues/74)).

### Changed

- Remove `conda_env` and `model_name` arguments from `MlflowPipelineHook` and add them to `PipelineML` and `pipeline_ml`. This is necessary for incoming hook auto-discovery in future release and it enables having multiple `PipelineML` in the same project ([#58](https://github.com/Galileo-Galilei/kedro-mlflow/pull/58)). This mechanically fixes [#54](https://github.com/Galileo-Galilei/kedro-mlflow/issues/54) by making `conda_env` path absolute for airflow suppport.
- `flatten_dict_params`, `recursive` and `sep` arguments of the `MlflowNodeHook` are moved to the `mlflow.yml` config file to prepare plugin auto registration. This also modifies the `run.py` template (to remove the args) and the `mlflow.yml` keys to add a `hooks` entry. ([#59](https://github.com/Galileo-Galilei/kedro-mlflow/pull/59))
- Rename CI workflow to `test` ([#57](https://github.com/Galileo-Galilei/kedro-mlflow/issues/57), [#68](https://github.com/Galileo-Galilei/kedro-mlflow/pull/68))
- The `input_name` attributes of `PipelineML` is now a python property and makes a check at setting time to prevent setting an invalid value. The check ensures that `input_name` is a valid input of the `inference` pipeline.


### Deprecated

- Deprecate `MlflowDataSet` which is renamed as `MlflowArtifactDataSet` for consistency with the other datasets. It will raise a `DeprecationWarning` in this realease, and will be totally supressed in next minor release. Please update your `catalog.yml` entries accordingly as soon as possible. ([#63](https://github.com/Galileo-Galilei/kedro-mlflow/issues/63))
- Deprecate `pipeline_ml` which is renamed as `pipeline_ml_factory` to avoid confusion between a `PipelineML` instance and the helper function to create `PipelineMl` instances from Kedro `Pipeline`s.

## [0.2.1] - 2018-08-06

### Added
Many documentation improvements:
  - Add a Code of conduct
  - Add a Contributing guide
  - Refactor README.md to separate clearly from documentation
  - Fix broken links
  - Fix bad markdown rendering
  - Split old README.md information in dedicated sections

### Changed

- Enable ``pipeline_ml`` to accept artifacts (encoder, binarizer...) to be "intermediary" outputs of the pipeline and not only "terminal" outputs (i.e. node outputs which are not re-used as another node input). This closes a bug discovered in a more general discussion in [#16](https://github.com/Galileo-Galilei/kedro-mlflow/issues/16).
- Only non-empty CLI arguments and options are logged as tags in MLflow ([#32](https://github.com/Galileo-Galilei/kedro-mlflow/issues/16))

## [0.2.0] - 2020-07-18

### Added

- Bump the codebase test coverage to 100% to improve stability
- Improve rendering of template with a trailing newline to make them  ```black```-valid
- Add a ``PipelineML.extract_pipeline_artifacts`` methods to make artifacts retrieving easier for a given pipeline
- Use an official kedro release (``>0.16.0, <0.17.0``) instead of the development branch

### Changed

- ``hooks``, ``context`` and ``cli`` folders are moved to ``framework`` to fit kedro new folder architecture
- Rename ``get_mlflow_conf`` in ``get_mlflow_config`` for consistency (with ``ConfigLoader``, ``KedroMlflowConfig``...)
- Rename keys of ``KedroMlflowConfig.to_dict()`` to remove the "_opts" suffix for consistency with the ``KedroMlflowConfig.from_dict`` method

### Fixed

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

## [0.1.0] - 2020-04-18

### Added

- Add cli ``kedro mlflow init`` to udpdate the template and ``kedro mlflow ui`` to open ``mlflow`` user interface with your project configuration
- Add hooks ``MlflowNodeHook`` and ``MlflowPipelineHook`` for parameters autologging and model autologging
- Add ``MlflowDataSet`` for artifacts autologging
- Add ``PipelineMl`` class and its ``pipeline_ml`` factory for pipeline packaging and service

[unreleased]: https://github.com/Galileo-Galilei/kedro-mlflow/compare/0.2.1...HEAD
[0.2.1]: https://github.com/Galileo-Galilei/kedro-mlflow/compare/0.2.0...0.2.1
[0.2.0]: https://github.com/Galileo-Galilei/kedro-mlflow/compare/0.1.0...0.2.0
[0.1.0]: https://github.com/Galileo-Galilei/kedro-mlflow/releases/tag/0.1.0
