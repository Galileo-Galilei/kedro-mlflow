# Changelog

## [Unreleased]

## [0.11.7] - 2023-01-28

### Added

-   :sparkles: Added a `MlflowModelRegistryDataSet`  in `kedro_mlflow.io.models` to enable fetching a mlflow model from the mlflow model registry by its name([#260](https://github.com/Galileo-Galilei/kedro-mlflow/issues/260))

### Fixed

-   :bug: Use  `__default__` as a run name if the pipeline is not specified in the `kedro run` commmand to avoid empty names ([#392](https://github.com/Galileo-Galilei/kedro-mlflow/issues/392))

## [0.11.6] - 2023-01-09

### Changed

-   :sparkles: `kedro-mlflow` now uses the default configuration (ignoring `mlflow.yml`) if an active run already exists in the process where the pipeline is started, and uses this active run for logging. This enables using ` kedro-mlflow`  with an orchestrator which starts mlflow itself before running kedro (e.g. airflow,  the `mlflow run` command, AzureML...) ([#358](https://github.com/Galileo-Galilei/kedro-mlflow/issues/358))

## [0.11.5] - 2022-12-12

### Added

-   :sparkles: Added an extra `server.mlflow_registry_uri` key in `mlflow.yml` to set the mlflow registry uri. ([#260](https://github.com/Galileo-Galilei/kedro-mlflow/issues/260))
-   :sparkles: Add support for authorization with expiring tokens by adding an extra `server.request_header_provider` entry in `mlflow.yml` ([#357](https://github.com/Galileo-Galilei/kedro-mlflow/issues/357))

### Fixed

-   :bug: `MlflowArtifactDataSet.load()` now correctly loads the artifact when both `artifact_path` and `run_id` arguments are specified. Previous fix in `0.11.4` did not work because when the file already exist locally, mlflow did not download it again so tests were incorrectly passing ([#362](https://github.com/Galileo-Galilei/kedro-mlflow/issues/362))

### Removed

-   :fire: :boom: Remove `reload_kedro_mlflow` line magic for notebook because kedro will deprecate the entrypoint in 0.18.3. It is still possible to access the mlflow client associated to the configuration in a notebook with `context.mlflow.server._mlflow_client` ([#349](https://github.com/Galileo-Galilei/kedro-mlflow/issues/349)). This is not considered as a breaking change since apparently no one uses it according to a [discussion with kedro's team](https://github.com/kedro-org/kedro/issues/878#issuecomment-1226545251).

## [0.11.4] - 2022-10-04

### Fixed

-   :bug: `MlflowArtifactDataSet.load()` now correctly loads the artifact when both `artifact_path` and `run_id` arguments are specified instead of raising an error ([#362](https://github.com/Galileo-Galilei/kedro-mlflow/issues/362))

## [0.11.3] - 2022-09-06

### Changed

-   :loud_sound: `kedro-mlflow` has its default logging level set to `INFO`. This was the default for `kedro<=0.18.1`. For `kedro>=0.18.2`, you can change the level in `logging.yml` ([#348](https://github.com/Galileo-Galilei/kedro-mlflow/issues/348))

### Fixed

-   :bug: `kedro-mlflow` now uses the `package_name` as experiment name by default if it is not specified. This is done to ensure consistency with the behaviour with no `mlflow.yml` file ([#328](https://github.com/Galileo-Galilei/kedro-mlflow/issues/328))
-   :memo: Update broken links to the most recent kedro and mlflow documentation

## [0.11.2] - 2022-08-28

### Changed

-   :sparkles: `kedro-mlflow` now runs even without a `mlflow.yml` file in your `conf/<env>` folder. As a consequence, running `kedro mlflow init` is now optional and should be only used for advanced configuration. ([#328](https://github.com/Galileo-Galilei/kedro-mlflow/issues/328))

## [0.11.1] - 2022-07-06

### Fixed

-   :bug: Make `pipeline_ml_factory` now correctly uses `kpm_kwargs` and `log_model_kwargs` instead of always using the default values. ([#329](https://github.com/Galileo-Galilei/kedro-mlflow/issues/329))
-   :bug: `kedro mlflow init` command no longer raises both a success and an error message when the command is failing. ([#336](https://github.com/Galileo-Galilei/kedro-mlflow/issues/336))

### Changed

-   :recycle: Refactor `KedroMlflowConfig` which no longer needs the `project_path` at instantiation. The uri validaiton is done at `setup()` time to be able to use the configuration not at a root of a kedro project. This is _not_ considered as a breaking change, because the recommended way to retrieve the config is to use `session.load_context().mlflow` which automatically calls `setup()` and hence behaviour inside a kedro project is unmodified. ([#314](https://github.com/Galileo-Galilei/kedro-mlflow/issues/314))

## [0.11.0] - 2022-06-18

### Added

-   :sparkles: :boom: The `MLFLOW_TRACKING_URI` environment variable is now used as the default tracking uri if the `server.mlflow_tracking_uri` config key is `None`. The `mlflow.yml` is changed to `server: mlflow_tracking_uri: null` to enforce this new behaviour as the default value. If the environment variable does not exists, it will behave like before. ([#321](https://github.com/Galileo-Galilei/kedro-mlflow/issues/321)).

### Changed

-   :recycle: :boom: Unify the `MlflowPipelineHook` and `MlflowNodeHook` in a single `MlflowHook` to ensure consistency in registration order ([#315](https://github.com/Galileo-Galilei/kedro-mlflow/issues/315))
-   :recycle: :technologist: :boom: The `get_mlflow_config` public function is removed. If you need to access the mlflow configuration, you can do it automatically in the context `mlflow` attribute, e.g. `session.load_context().mlflow` ([#310](https://github.com/Galileo-Galilei/kedro-mlflow/issues/310))

### Removed

-   :coffin: :boom: Remove unused `stores_environment_variables` configuration option. This key must be removed from `mlflow.yml`.
-   :arrow_up: :bug: Upgrade requirements to make support for `kedro>=0.18.1, kedro<0.19.0` explicit. This is the only valid compatibility range since `kedro-mlflow==0.10.0`, but requirements had not been updated yet ([#309](https://github.com/Galileo-Galilei/kedro-mlflow/issues/309)).

## [0.10.0] - 2022-05-15

### Added

-   :arrow_up: Add support for `kedro==0.18.1` which was broken due to kedro's removal of `_active_session` private global variable ([#309](https://github.com/Galileo-Galilei/kedro-mlflow/issues/309)).

### Fixed

-   :memo: Fix typo in documentation ([#302](https://github.com/Galileo-Galilei/kedro-mlflow/issues/302))

### Changed

-   :recycle: :boom: Refactor the `get_mlflow_config` function which now takes `context` instead of `session` as input ([#309](https://github.com/Galileo-Galilei/kedro-mlflow/issues/309))

### Removed

-   :boom: :arrow_down: Drop support for `kedro=0.18.0`. `kedro-mlflow` now supports only `kedro>=0.18.1, kedro<0.19.0` ([#309](https://github.com/Galileo-Galilei/kedro-mlflow/issues/309)).

## [0.9.0] - 2022-04-01

### Added

-   :sparkles: Add support for `kedro=0.18.X` ([#290](https://github.com/Galileo-Galilei/kedro-mlflow/issues/290))
-   :sparkles: `kedro-mlflow` is now available on `conda-forge` and can be installed with `conda install kedro-mlflow`. This is retroactive to `kedro-mlflow==0.8.1` ([#118](https://github.com/Galileo-Galilei/kedro-mlflow/issues/118))

### Removed

-   :boom: :wastebasket: Drop support for `kedro=0.17.X` ([#290](https://github.com/Galileo-Galilei/kedro-mlflow/issues/290))

## [0.8.1] - 2022-02-13

### Added

-   :sparkles: Open the UI in the default browser when the `mlflow_tracking_uri` in `mlflow.yml` is a http address instead of launching the ui server. ([#275](https://github.com/Galileo-Galilei/kedro-mlflow/issues/275))

### Fixed

-   :bug: Force the input dataset in `KedroPipelineModel` to be a `MemoryDataSet` to remove unnecessary dependency to the underlying Kedro `AbstractDataSet` used during training ([#273](https://github.com/Galileo-Galilei/kedro-mlflow/issues/273))
-   :bug: Make `MlflowArtifactDataset` correctly log in mlflow Kedro DataSets without a `_path` attribute like `kedro.io.PartitionedDataSet`  ([#258](https://github.com/Galileo-Galilei/kedro-mlflow/issues/258)).
-   :bug: Automatically persist pipeline parameters when calling the `kedro mlflow modelify` command for consistency with how `PipelineML` objects are handled and for ease of use ([#282](https://github.com/Galileo-Galilei/kedro-mlflow/issues/282)).

## [0.8.0] - 2022-01-05

### Added

-   :sparkles: Add a `kedro mlflow modelify` command to export a pipeline as a mlflow model ([#261](https://github.com/Galileo-Galilei/kedro-mlflow/issues/261))
-   :memo: Format code blocks in documentation with `blacken-docs`
-   :construction_worker: Enforce the use of `black` and `isort` in the CI to enforce style guidelines for developers

### Changed

-   :sparkles: :boom: The `pipeline_ml_factory` accepts 2 new arguments `log_model_kwargs` (which will be passed _as is_ to `mlflow.pyfunc.log_model`) and `kpm_kwargs` (which will be passed _as is_ to `KedroPipelineModel`). This ensures perfect consistency with mlflow API and offers new possibility like saving the project source code alongside the model ([#67](https://github.com/Galileo-Galilei/kedro-mlflow/issues/67)). Note that `model_signature`, `conda_env` and `model_name` arguments are removed, and replace respectively by `log_model_kwargs["signature"]`, `log_model_kwargs["conda_env"]` and `log_model_kwargs["artifact_path"]`.
-   :sparkles: :boom: The `KedroPipelineModel` custom mlflow model now accepts any kedro `Pipeline` as input (provided they have a single DataFrame input and a single output because this is an mlflow limitation) instead of only `PipelineML` objects. This simplifies the API for user who want to customise the model logging ([#171](https://github.com/Galileo-Galilei/kedro-mlflow/issues/171)). `KedroPipelineModel.__init__` argument `pipeline_ml` is renamed `pipeline` to reflect this change.
-   :wastebasket: `kedro_mlflow.io.metrics.MlflowMetricsDataSet` is no longer deprecated because there is no alternative for now to log many metrics at the same time.
-   :boom: Refactor `mlflow.yml` to match mlflow's API ([#77](https://github.com/Galileo-Galilei/kedro-mlflow/issues/77)). To migrate projects with `kedro<0.8.0`, please update their `mlflow.yml` with `kedro mlflow init --force` command.

### Fixed

-   :bug: `KedroMlflowConfig.setup()` methods now sets the experiment globally to ensure all runs are launched under the experiment specified in the configuration even in interactive mode ([#256](https://github.com/Galileo-Galilei/kedro-mlflow/issues/256)).

### Removed

-   :fire: :boom: `KedroMlflowConfig` and `get_mlflow_config` were deprecated since `0.7.3` and are now removed from `kedro_mlflow.framework.context`. Direct import must now use `kedro_mlflow.config`.

## [0.7.6] - 2021-10-08

### Fixed

-   :bug: The reserved keyword "databricks" is no longer converted to a local filepath before setting the `MLFLOW_TRACKING_URI` to enable integration with databricks managed platform. ([#248](https://github.com/Galileo-Galilei/kedro-mlflow/issues/248))

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
-   :sparkles: `MlflowPipelineHook` and `MlflowNodeHook` are now [auto-registered](https://kedro.readthedocs.io/en/latest/hooks/introduction.html#registering-your-hook-implementations-with-kedro) if you use `kedro>=0.16.4` ([#29](https://github.com/Galileo-Galilei/kedro-mlflow/issues/29))

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

[Unreleased]: https://github.com/Galileo-Galilei/kedro-mlflow/compare/0.11.7...HEAD

[0.11.7]: https://github.com/Galileo-Galilei/kedro-mlflow/compare/0.11.6...0.11.7

[0.11.6]: https://github.com/Galileo-Galilei/kedro-mlflow/compare/0.11.5...0.11.6

[0.11.5]: https://github.com/Galileo-Galilei/kedro-mlflow/compare/0.11.4...0.11.5

[0.11.4]: https://github.com/Galileo-Galilei/kedro-mlflow/compare/0.11.3...0.11.4

[0.11.3]: https://github.com/Galileo-Galilei/kedro-mlflow/compare/0.11.2...0.11.3

[0.11.2]: https://github.com/Galileo-Galilei/kedro-mlflow/compare/0.11.1...0.11.2

[0.11.1]: https://github.com/Galileo-Galilei/kedro-mlflow/compare/0.11.0...0.11.1

[0.11.0]: https://github.com/Galileo-Galilei/kedro-mlflow/compare/0.10.0...0.11.0

[0.10.0]: https://github.com/Galileo-Galilei/kedro-mlflow/compare/0.9.0...0.10.0

[0.9.0]: https://github.com/Galileo-Galilei/kedro-mlflow/compare/0.8.1...0.9.0

[0.8.1]: https://github.com/Galileo-Galilei/kedro-mlflow/compare/0.8.0...0.8.1

[0.8.0]: https://github.com/Galileo-Galilei/kedro-mlflow/compare/0.7.6...0.8.0

[0.7.6]: https://github.com/Galileo-Galilei/kedro-mlflow/compare/0.7.5...0.7.6

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
