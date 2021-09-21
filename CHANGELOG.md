# Changelog

## [Unreleased]

## [0.7.5] - 2021-09-21

### Added

-   :sparkles: Add support for notebook use. When a notebook is opened via a kedro command (e.g. `kedro jupyter notebook`), you can call the `%reload_kedro_mlflow` line magic to setup mlflow configuration automatically. A `mlflow_client` to the database is also created available as a global variable ([#124](https://github.com/Galileo-Galilei/kedro-mlflow/issues/124)).
-   :memo: Add automatic API documentation through docstrings for better consistency between code and docs ([#110](https://github.com/Galileo-Galilei/kedro-mlflow/issues/110)). All docstrings are not updated yet and it will be a long term work.

### Changed

-   :recycle: `KedroMlflowConfig` was refactored with pydantic for improved type checking when loading configuration, overall robustness and autocompletion. Its keys have changed, but it is not considered as a user facing changes since the public function `get_mlflow_config()` and `KedroMlflowConfig().setup()` are not modified.

-   :wastebasket: The `kedro.framework.context` folder is moved to `kedro.config` for consistency with the Kedro repo structure: `get_mlflow_config` import must change from `from kedro_mlflow.framework.context import get_mlflow_config` to `from kedro_mlflow.config import get_mlflow_config`.

## [0.7.4] - 2021-08-30

### Added

-   :sparkles: Create an `MlflowMetricDataSet` to simplify the existing metric API. It enables logging a single float as a metric, eventually automatically increasing the "step" if the metric is going to be updated during time ([#73](https://github.com/Galileo-Galilei/kedro-mlflow/issues/73))
-   :sparkles: Create an `MlflowMetricHistoryDataSet` to simplify the existing metric API. It enables logging the evolution of a given metric during training. ([#73](https://github.com/Galileo-Galilei/kedro-mlflow/issues/73))

### Fixed

-   :bug: Dictionnary parameters with integer keys are now properly logged in mlflow when `flatten_dict_params` is set to `True` in the `mlflow.yml` instead of raising a `TypeError` ([#224](https://github.com/Galileo-Galilei/kedro-mlflow/discussions/224))
-   :bug: The user defined `sep` parameter of the `mlflow.yml` (defined in `node` section) is now used even if the parameters dictionnary has a depth>=2 ([#230](https://github.com/Galileo-Galilei/kedro-mlflow/issues/230))

### Changed

-   :recycle: Move `flatten_dict` function to `hooks.utils` folder and rename it `_flatten_dict` to make more explicit that it is not a user facing function which should not be used directly and comes with no guarantee. This is not considered as a breaking change since it is an undocumented function.
-   :wastebasket: Deprecate `MlflowMetricsDataSet` in favor of the 2 new datasets `MlflowMetricDataSet` and `MlflowMetricHistoryDataSet` newly added. It will be removed in `kedro-mlflow==0.8.0`.

## [0.7.3] - 2021-08-16

### Added

-   :sparkles: Update the `MlflowArtifactDataSet.load()` method to download the data from the `run_id` if it is specified instead of using the local filepath. This can be used for instance to continue training from a pretrained model or to retrieve the best model from an hyperparameter search ([#95](https://github.com/Galileo-Galilei/kedro-mlflow/issues/95))

## [0.7.2] - 2021-05-02

### Fixed

-   :bug: Remove global CLI command `new` (which was not implemented yet) to make project CLI commands available. It is not possible to have 2 CLI groups (one at global level , one at project level) because of a bug in `kedro==0.17.3` ([#193](https://github.com/Galileo-Galilei/kedro-mlflow/issues/193))

## [0.7.1] - 2021-04-09

### Added

-   :sparkles: It is now possible to deactivate tracking (for parameters and datasets) by specifying a key `disabled_tracking: pipelines: [<pipeline-name>]` in the `mlflow.yml` configuration file. ([#92](https://github.com/Galileo-Galilei/kedro-mlflow/issues/92))

-   :sparkles: The `kedro mlflow ui` command `host` and `port` keys can be overwritten at runtime ([#187](https://github.com/Galileo-Galilei/kedro-mlflow/issues/187))

### Fixed

-   :bug: The `kedro mlflow ui` command now reads properly the `ui:host` and `ui:port` keys from the `mlflow.yml` which were incorrectly ignored ([#187](https://github.com/Galileo-Galilei/kedro-mlflow/issues/187))

## [0.7.0] - 2021-03-17

### Added

-   :arrow_up: `kedro-mlflow` now supports `kedro>=0.17.1` ([#144](https://github.com/Galileo-Galilei/kedro-mlflow/issues/144)).

### Changed

-   :pushpin: Drop support for `kedro==0.17.0`, since the kedro core team [made a breaking change in `0.17.1`](https://github.com/quantumblacklabs/kedro/blob/master/RELEASE.md#breaking-changes-to-the-api). All future plugin updates will be only compatible with `kedro>=0.17.1`.

## [0.6.0] - 2021-03-14

### Added

-   :arrow_up: `kedro-mlflow` now supports `kedro==0.17.0` ([#144](https://github.com/Galileo-Galilei/kedro-mlflow/issues/144)). Since the kedro core team made a breaking change in the patch release `0.17.1`, it is not supported yet. They also [recommend to downgrade to 0.17.0 for stability](https://github.com/quantumblacklabs/kedro/issues/716#issuecomment-793983298).
-   :memo: Updated documentation

### Fixed

-   :bug: The support of `kedro==0.17.0` automatically makes the CLI commands available when the configuration is declared in a `pyproject.toml` instead of a `.kedro.yml`, which was not the case in previous version despite we claim it was ([#157](https://github.com/Galileo-Galilei/kedro-mlflow/issues/157)).

### Changed

-   :pushpin: Drop support for `kedro==0.16.x`. All future plugin updates will be only compatible with `kedro>=0.17.0`.

## [0.5.0] - 2021-02-21

### Added

-   :sparkles: A new `long_parameters_strategy` key is added in the `mlflow.yml` (under in the hook/node section). You can specify different strategies (`fail`, `truncate` or `tag`) to handle parameters over 250 characters which cause crashes for some mlflow backend. ([#69](https://github.com/Galileo-Galilei/kedro-mlflow/issues/69))
-   :sparkles: Add an `env` parameter to `kedro mlflow init` command to specify under which `conf/` subfolder the `mlflow.yml` should be created. ([#159](https://github.com/Galileo-Galilei/kedro-mlflow/issues/159))
-   :sparkles: The input parameters of the `inference` pipeline of a `PipelineML` object are now automatically pickle-ised and converted as artifacts. ([#158](https://github.com/Galileo-Galilei/kedro-mlflow/issues/158))
-   :memo: [Detailed documentation on how to use `pipeline_ml_factory`](https://kedro-mlflow.readthedocs.io/en/latest/source/05_framework_ml/index.html) function, and more generally on how to use `kedro-mlflow` as mlops framework. This comes from [an example repo `kedro-mlflow-tutorial`](https://github.com/Galileo-Galilei/kedro-mlflow-tutorial). ([#16](https://github.com/Galileo-Galilei/kedro-mlflow/issues/16))

### Fixed

-   :pushpin: Pin the kedro version to force it to be **strictly** inferior to `0.17` which is not compatible with current `kedro-mlflow` version ([#143](https://github.com/Galileo-Galilei/kedro-mlflow/issues/143))
-   :sparkles: It is no longer assumed for the project to run that the `mlflow.yml` is located under `conf/base`. The project will run as soon as the configuration file is discovered by the registered ConfigLoader ([#159](https://github.com/Galileo-Galilei/kedro-mlflow/issues/159))

### Changed

-   :zap: :boom: The `KedroPipelineModel.load_context()` method now loads all the `DataSets` in memory in the `DataCatalog`. It is also now possible to specify the `runner` to execute the model as well as the `copy_mode` when executing the inference pipeline (instead of deepcopying the datasets between each nodes which is kedro's default). This makes the API serving with `mlflow serve` command considerably faster (~20 times faster) for models which need compiling (e.g. keras, tensorflow ...) ([#133](https://github.com/Galileo-Galilei/kedro-mlflow/issues/133))
-   :sparkles: The CLI projects commands are now always accessible even if you have not called `kedro mlflow init` yet to create a `mlflow.yml` configuration file ([#159](https://github.com/Galileo-Galilei/kedro-mlflow/issues/159))

## [0.4.1] - 2020-12-03

### Added

-   :sparkles: It is now possible to supply credentials for the mlflow tracking server within `mlflow.yml` and `credentials.yml`. They will be exported as environment variables during the run. ([#31](https://github.com/Galileo-Galilei/kedro-mlflow/issues/31))

### Fixed

-   :bug: Fix `TypeError: unsupported operand type(s) for /: 'str' and 'str'` when using `MlflowArtifactDataSet` with `MlflowModelSaverDataSet` ([#116](https://github.com/Galileo-Galilei/kedro-mlflow/issues/116))
-   :memo: Fix various docs typo ([#6](https://github.com/Galileo-Galilei/kedro-mlflow/issues/6))
-   :bug: When the underlying Kedro pipeline fails, the associated mlflow run is now marked as 'FAILED' instead of 'FINISHED'. It is rendered with a red cross instead of the green tick in the mlflow user interface ([#121](https://github.com/Galileo-Galilei/kedro-mlflow/issues/121)).
-   :bug: Fix a bug which made `KedroPipelineModel` impossible to load if one of its artifact was a `MlflowModel<Saver/Logger>DataSet`. These datasets were not deepcopiable because of one their attributes was a module ([#122](https://github.com/Galileo-Galilei/kedro-mlflow/issues/122)).

### Changed

-   :memo: Refactor doc structure for readability ([#6](https://github.com/Galileo-Galilei/kedro-mlflow/issues/6))
-   :zap: :boom: The `KedroMlflowConfig` no longer creates the mlflow experiment and access to the mlflow tracking server when it is instantiated. A new `setup()` method sets up the mlflow configuration (tracking uri, credentials and experiment management) but must now be called explicitly. ([#97](https://github.com/Galileo-Galilei/kedro-mlflow/issues/97))

## [0.4.0] - 2020-11-03

### Added

-   :arrow_up: `kedro-mlflow` now supports `kedro>=0.16.5` ([#62](https://github.com/Galileo-Galilei/kedro-mlflow/issues/62))
-   :sparkles: `kedro-mlflow` now supports configuring the project in `pyproject.toml`  (_Only for kedro>=0.16.5_) ([#96](https://github.com/Galileo-Galilei/kedro-mlflow/issues/96))
-   :sparkles: `pipeline_ml_factory` now accepts that `inference` pipeline `inputs` may be in `training` pipeline `inputs` ([#71](https://github.com/Galileo-Galilei/kedro-mlflow/issues/71))
-   :sparkles: `pipeline_ml_factory` now infer automatically the schema of the input dataset to validate data automatically at inference time. The output schema can be declared manually in `model_signature` argument ([#70](https://github.com/Galileo-Galilei/kedro-mlflow/issues/70))
-   :sparkles: Add two DataSets for model logging and saving: `MlflowModelLoggerDataSet` and `MlflowModelSaverDataSet` ([#12](https://github.com/Galileo-Galilei/kedro-mlflow/issues/12))
-   :sparkles: `MlflowPipelineHook` and `MlflowNodeHook` are now [auto-registered](https://kedro.readthedocs.io/en/latest/07_extend_kedro/02_hooks.html#registering-your-hook-implementations-with-kedro) if you use `kedro>=0.16.4` ([#29](https://github.com/Galileo-Galilei/kedro-mlflow/issues/29))

### Fixed

-   :zap: `get_mlflow_config` now uses the Kedro `ProjectContext` `ConfigLoader` to get configs ([#66](https://github.com/Galileo-Galilei/kedro-mlflow/issues/66)). This indirectly solves the following issues:
    -   `get_mlflow_config` now works in interactive mode if `load_context` is called  with a path different from the working directory ([#30](https://github.com/Galileo-Galilei/kedro-mlflow/issues/30))
    -   kedro_mlflow now works fine with kedro jupyter notebook independently of the working directory ([#64](https://github.com/Galileo-Galilei/kedro-mlflow/issues/64))
    -   You can use global variables in `mlflow.yml` which is now properly parsed if you use a `TemplatedConfigLoader` ([#72](https://github.com/Galileo-Galilei/kedro-mlflow/issues/72))
-   :bug: `MlflowMetricsDataset` now saves in the specified `run_id` instead of the current one when the prefix is not specified ([#62](https://github.com/Galileo-Galilei/kedro-mlflow/issues/62))
-   :memo: Other bug fixes and documentation improvements ([#6](https://github.com/Galileo-Galilei/kedro-mlflow/issues/6), [#99](https://github.com/Galileo-Galilei/kedro-mlflow/issues/99))

### Changed

-   :sparkles: :boom: The `KedroPipelineModel` now unpacks the result of the `inference` pipeline and no longer returns a dictionary with the name in the `DataCatalog` but only the predicted value ([#93](https://github.com/Galileo-Galilei/kedro-mlflow/issues/93))
-   :recycle: :boom: The `PipelineML.extract_pipeline_catalog` is renamed `PipelineML._extract_pipeline_catalog` to indicate it is a private method and is not intended to be used directly by end users who should rely on `PipelineML.extract_pipeline_artifacts` ([#100](https://github.com/Galileo-Galilei/kedro-mlflow/issues/100))
-   :building_construction: :boom: The `MlflowArtifactDataSet` is moved from `kedro_mlflow.io` folder to `kedro_mlflow.io.artifacts`. ([#109](https://github.com/Galileo-Galilei/kedro-mlflow/issues/109))
-   :building_construction: :boom: The `MlflowMetricsDataSet` is moved from `kedro_mlflow.io` folder to `kedro_mlflow.io.metrics`. ([#109](https://github.com/Galileo-Galilei/kedro-mlflow/issues/109))

### Removed

-   :recycle: :boom: `kedro mlflow init` command is no longer declaring hooks in `run.py`. You must now [register your hooks manually](https://kedro-mlflow.readthedocs.io/en/stable/source/02_installation/02_setup.html#declaring-kedro-mlflow-hooks) in the `run.py` if you use `kedro>=0.16.0, <0.16.3` ([#62](https://github.com/Galileo-Galilei/kedro-mlflow/issues/62)).
-   :fire: Remove `pipeline_ml` function which was deprecated in 0.3.0. It is now replaced by `pipeline_ml_factory` ([#105](https://github.com/Galileo-Galilei/kedro-mlflow/issues/105))
-   :fire: Remove `MlflowDataSet` dataset which was deprecated in 0.3.0. It is now replaced by `MlflowArtifactDataSet` ([#105](https://github.com/Galileo-Galilei/kedro-mlflow/issues/105))

## [0.3.0] - 2020-10-11

### Added

-   :sparkles: Add dataset `MlflowMetricsDataSet` for metrics logging ([#9](https://github.com/Galileo-Galilei/kedro-mlflow/issues/9)) and update documentation for metrics.
-   :construction_worker: Add CI workflow `create-release` to ensure release consistency and up-to-date CHANGELOG. ([#57](https://github.com/Galileo-Galilei/kedro-mlflow/issues/57), [#68](https://github.com/Galileo-Galilei/kedro-mlflow/pull/68))
-   :memo: Add templates for issues and pull requests ([#57](https://github.com/Galileo-Galilei/kedro-mlflow/issues/57), [#68](https://github.com/Galileo-Galilei/kedro-mlflow/pull/68))

### Fixed

-   :bug: Versioned datasets artifacts logging are handled correctly ([#41](https://github.com/Galileo-Galilei/kedro-mlflow/issues/41))
-   :bug: MlflowDataSet handles correctly datasets which are inherited from AbstractDataSet ([#45](https://github.com/Galileo-Galilei/kedro-mlflow/issues/45))
-   :zap: Change the test in `_generate_kedro_command` to accept both empty `Iterable`s(default in CLI mode) and `None` values (default in interactive mode) ([#50](https://github.com/Galileo-Galilei/kedro-mlflow/issues/50))
-   :zap: Force to close all mlflow runs when a pipeline fails. It prevents further execution of the pipeline to be logged within the same mlflow run_id as the failing pipeline. ([#10](https://github.com/Galileo-Galilei/kedro-mlflow/issues/10))
-   :memo: Fix various documentation typos ([#34](https://github.com/Galileo-Galilei/kedro-mlflow/pull/34), [#35](https://github.com/Galileo-Galilei/kedro-mlflow/pull/35), [#36](https://github.com/Galileo-Galilei/kedro-mlflow/pull/36) and more)
-   :memo: Update README (add badges for readibility, add a "main contributors" section to give credit, fix typo in install command, link to milestones for more up-to-date priorities) ([#57](https://github.com/Galileo-Galilei/kedro-mlflow/issues/57), [#68](https://github.com/Galileo-Galilei/kedro-mlflow/pull/68))
-   :construction_worker: Fix bug in CI deployment workflow and rename it to `publish` ([#57](https://github.com/Galileo-Galilei/kedro-mlflow/issues/57), [#68](https://github.com/Galileo-Galilei/kedro-mlflow/pull/68))
-   :bug: Fix a bug in `MlflowDataSet` which sometimes failed to log on remote storage (S3, Azure Blob storage) with underlying `log_artifacts` when the kedro's `AbstractDataset._filepath` was a `pathlib.PurePosixPath` object instead of a string ([#74](https://github.com/Galileo-Galilei/kedro-mlflow/issues/74)).
-   :construction_worker: Add a CI for release candidate creation and use actions to enforce semantic versioning and [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) format.

### Changed

-   :recycle: Remove `conda_env` and `model_name` arguments from `MlflowPipelineHook` and add them to `PipelineML` and `pipeline_ml`. This is necessary for incoming hook auto-discovery in future release and it enables having multiple `PipelineML` in the same project ([#58](https://github.com/Galileo-Galilei/kedro-mlflow/pull/58)). This mechanically fixes [#54](https://github.com/Galileo-Galilei/kedro-mlflow/issues/54) by making `conda_env` path absolute for airflow support.
-   :recycle: :boom: `flatten_dict_params`, `recursive` and `sep` arguments of the `MlflowNodeHook` are moved to the `mlflow.yml` config file to prepare plugin auto registration. This also modifies the `run.py` template (to remove the args) and the `mlflow.yml` keys to add a `hooks` entry. ([#59](https://github.com/Galileo-Galilei/kedro-mlflow/pull/59))
-   :construction_worker: Rename CI workflow to `test` ([#57](https://github.com/Galileo-Galilei/kedro-mlflow/issues/57), [#68](https://github.com/Galileo-Galilei/kedro-mlflow/pull/68))
-   :zap: The `input_name` attributes of `PipelineML` is now a python property and makes a check at setting time to prevent setting an invalid value. The check ensures that `input_name` is a valid input of the `inference` pipeline.

### Deprecated

-   :wastebasket: Deprecate `MlflowDataSet` which is renamed as `MlflowArtifactDataSet` for consistency with the other datasets. It will raise a `DeprecationWarning` in this realease, and will be totally supressed in next minor release. Please update your `catalog.yml` entries accordingly as soon as possible. ([#63](https://github.com/Galileo-Galilei/kedro-mlflow/issues/63))
-   :wastebasket: Deprecate `pipeline_ml` which is renamed as `pipeline_ml_factory` to avoid confusion between a `PipelineML` instance and the helper function to create `PipelineMl` instances from Kedro `Pipeline`s.

## [0.2.1] - 2018-08-06

### Added

:memo: Many documentation improvements:

-   Add a Code of conduct
-   Add a Contributing guide
-   Refactor README.md to separate clearly from documentation
-   Fix broken links
-   Fix bad markdown rendering
-   Split old README.md information in dedicated sections

### Changed

-   :bug: Enable `pipeline_ml` to accept artifacts (encoder, binarizer...) to be "intermediary" outputs of the pipeline and not only "terminal" outputs (i.e. node outputs which are not re-used as another node input). This closes a bug discovered in a more general discussion in [#16](https://github.com/Galileo-Galilei/kedro-mlflow/issues/16).
-   :recycle: Only non-empty CLI arguments and options are logged as tags in MLflow ([#32](https://github.com/Galileo-Galilei/kedro-mlflow/issues/16))

## [0.2.0] - 2020-07-18

### Added

-   :white_check_mark: Bump the codebase test coverage to 100% to improve stability
-   :rotating_light: Improve rendering of template with a trailing newline to make them  `black`-valid
-   :sparkles: Add a `PipelineML.extract_pipeline_artifacts` methods to make artifacts retrieving easier for a given pipeline
-   :tada: Use an official kedro release (`>0.16.0, <0.17.0`) instead of the development branch

### Changed

-   :building_construction: :boom: `hooks`, `context` and `cli` folders are moved to `framework` to fit kedro new folder architecture
-   :recycle: :boom: Rename `get_mlflow_conf` in `get_mlflow_config` for consistency (with `ConfigLoader`, `KedroMlflowConfig`...)
-   :recycle: :boom: Rename keys of `KedroMlflowConfig.to_dict()` to remove the "\_opts" suffix for consistency with the `KedroMlflowConfig.from_dict` method

### Fixed

-   :see_no_evil: Add `debug` folder to gitignore for to avoid involuntary data leakage
-   :bug: Remove the inadequate warning _"You have not initialized your project yet"_ when calling `kedro mlflow init`
-   :bug: Remove useless check to see if the commands are called inside a Kedro project since the commands are dynamically displayed based on whether the call is made inside a kedro project or not
-   :bug: Fix typos in error messages
-   :bug: Fix hardcoded path to the `run.py` template
-   :bug: Make not implemented function raise a `NotImplementError` instead of failing silently
-   :bug: Fix wrong parsing when the `mlflow_tracking_uri` key of the `mlflow.yml` configuration file was an absolute local path
-   :coffin: Remove unused `KedroMlflowContextClass`
-   :bug: Force the `MlflowPipelineHook.before_pipeline_run` method to set the `mlflow_tracking_uri` to the one from the configuration to enforce configuration file to be prevalent on environment variables or current active tracking uri in interactive mode
-   :bug: Fix wrong environment parsing case when passing a conda environment as a python dictionary in `MlflowPipelineHook`
-   :bug: Fix wrong artifact logging of `MlflowDataSet` when a run was already active and the save method was called in an interactive python session.
-   :recycle: :boom: Force the user to declare an `input_name` for a `PipelineMl` object to fix difficult inference of what is the pipeline input
-   :recycle: Update `run.py` template to fit kedro new one.
-   :recycle: Force `_generate_kedro_commands` to separate an option and its arguments with a "=" sign for readibility

## [0.1.0] - 2020-04-18

### Added

-   :sparkles: Add cli `kedro mlflow init` to udpdate the template and `kedro mlflow ui` to open `mlflow` user interface with your project configuration
-   :sparkles: Add hooks `MlflowNodeHook` and `MlflowPipelineHook` for parameters autologging and model autologging
-   :sparkles: Add `MlflowDataSet` for artifacts autologging
-   :sparkles: Add `PipelineMl` class and its `pipeline_ml` factory for pipeline packaging and service

[Unreleased]: https://github.com/Galileo-Galilei/kedro-mlflow/compare/0.7.5...HEAD

[0.7.5]: https://github.com/Galileo-Galilei/kedro-mlflow/compare/0.7.4...0.7.5

[0.7.4]: https://github.com/Galileo-Galilei/kedro-mlflow/compare/0.7.3...0.7.4

[0.7.3]: https://github.com/Galileo-Galilei/kedro-mlflow/compare/0.7.2...0.7.3

[0.7.2]: https://github.com/Galileo-Galilei/kedro-mlflow/compare/0.7.1...0.7.2

[0.7.1]: https://github.com/Galileo-Galilei/kedro-mlflow/compare/0.7.0...0.7.1

[0.7.0]: https://github.com/Galileo-Galilei/kedro-mlflow/compare/0.6.0...0.7.0

[0.6.0]: https://github.com/Galileo-Galilei/kedro-mlflow/compare/0.5.0...0.6.0

[0.5.0]: https://github.com/Galileo-Galilei/kedro-mlflow/compare/0.4.1...0.5.0

[0.4.1]: https://github.com/Galileo-Galilei/kedro-mlflow/compare/0.4.0...0.4.1

[0.4.0]: https://github.com/Galileo-Galilei/kedro-mlflow/compare/0.3.0...0.4.0

[0.3.0]: https://github.com/Galileo-Galilei/kedro-mlflow/compare/0.2.1...0.3.0

[0.2.1]: https://github.com/Galileo-Galilei/kedro-mlflow/compare/0.2.0...0.2.1

[0.2.0]: https://github.com/Galileo-Galilei/kedro-mlflow/compare/0.1.0...0.2.0

[0.1.0]: https://github.com/Galileo-Galilei/kedro-mlflow/releases/tag/0.1.0
