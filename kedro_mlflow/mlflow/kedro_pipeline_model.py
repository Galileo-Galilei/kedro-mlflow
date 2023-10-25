import logging
from pathlib import Path
from typing import Dict, Optional, Union

from kedro.framework.hooks import _create_hook_manager
from kedro.io import DataCatalog, MemoryDataset
from kedro.pipeline import Pipeline
from kedro.runner import AbstractRunner, SequentialRunner
from kedro_datasets.pickle import PickleDataset
from mlflow.pyfunc import PythonModel

from kedro_mlflow.pipeline.pipeline_ml import PipelineML


class KedroPipelineModel(PythonModel):
    def __init__(
        self,
        pipeline: Pipeline,
        catalog: DataCatalog,
        input_name: str,
        runner: Optional[AbstractRunner] = None,
        copy_mode: Optional[Union[Dict[str, str], str]] = "assign",
    ):
        """[summary]

        Args:
            pipeline (Pipeline): A Kedro Pipeline object to
            store as a Mlflow Model. Also works with kedro_mlflow PipelineML objects.

            catalog (DataCatalog): The DataCatalog associated
            to the PipelineMl

            runner (Optional[AbstractRunner], optional): The kedro
            AbstractRunner to use. Defaults to SequentialRunner if
            None.

            copy_mode (Optional[Union[Dict[str,str], str]]):
            The copy_mode of each DataSet of the catalog
            when reconstructing the DataCatalog in memory.
            The default is "assign".
            You can pass either:
                - None to use Kedro default mode for each dataset
                - a single string ("deepcopy", "copy" and "assign")
                to apply to all datasets
                - a dictionary with (dataset name, copy_mode) key/values
                pairs. The associated mode must be a valid kedro mode
                ("deepcopy", "copy" and "assign") for each. Defaults to None.
        """

        self.pipeline = (
            pipeline.inference if isinstance(pipeline, PipelineML) else pipeline
        )
        self.input_name = input_name
        self.initial_catalog = self._extract_pipeline_catalog(catalog)

        nb_outputs = len(self.pipeline.outputs())
        if nb_outputs != 1:
            outputs_list_str = "\n - ".join(self.pipeline.outputs())
            raise ValueError(
                f"Pipeline must have one and only one output, got '{nb_outputs}' outputs: \n - {outputs_list_str}"
            )
        self.output_name = list(self.pipeline.outputs())[0]
        self.runner = runner or SequentialRunner()
        self.copy_mode = copy_mode or {}
        # copy mode has been converted because it is a property
        # TODO: we need to use the runner's default dataset in case of multithreading
        self.loaded_catalog = DataCatalog(
            datasets={
                name: MemoryDataset(copy_mode=copy_mode)
                for name, copy_mode in self.copy_mode.items()
            }
        )

    @property
    def _logger(self) -> logging.Logger:
        return logging.getLogger(__name__)

    @property
    def copy_mode(self):
        return self._copy_mode

    @copy_mode.setter
    def copy_mode(self, copy_mode):
        if isinstance(copy_mode, str) or copy_mode is None:
            # if it is a string, we must create manually the dictionary
            # of all catalog entries with this copy_mode
            self._copy_mode = {
                name: copy_mode
                for name in self.pipeline.datasets()
                if name != self.output_name
            }
        elif isinstance(copy_mode, dict):
            # if it is a dict we will retrieve the copy mode when necessary
            # it does not matter if this dict does not contain all the catalog entries
            # the others will be returned as None when accessing with dict.get()
            self._copy_mode = {
                name: None
                for name in self.pipeline.datasets()
                if name != self.output_name
            }
            self._copy_mode.update(copy_mode)
        else:
            raise TypeError(
                f"'copy_mode' must be a 'str' or a 'dict', not '{type(copy_mode)}'"
            )

    def _extract_pipeline_catalog(self, catalog: DataCatalog) -> DataCatalog:
        sub_catalog = DataCatalog()
        for dataset_name in self.pipeline.inputs():
            if dataset_name == self.input_name:
                # there is no obligation that this dataset is persisted
                # and even if it is, we keep only an ampty memory dataset to avoid
                # extra uneccessary dependencies: this dataset will be replaced at
                # inference time and we do not need to know the original type, see
                # https://github.com/Galileo-Galilei/kedro-mlflow/issues/273
                sub_catalog.add(dataset_name=dataset_name, dataset=MemoryDataset())
            else:
                try:
                    dataset = catalog._datasets[dataset_name]
                    if isinstance(
                        dataset, MemoryDataset
                    ) and not dataset_name.startswith("params:"):
                        raise KedroPipelineModelError(
                            f"""
                                The datasets of the training pipeline must be persisted locally
                                to be used by the inference pipeline. You must enforce them as
                                non 'MemoryDataset' in the 'catalog.yml'.
                                Dataset '{dataset_name}' is not persisted currently.
                                """
                        )
                    self._logger.info(
                        f"The dataset '{dataset_name}' is added to the Pipeline catalog."
                    )
                    sub_catalog.add(dataset_name=dataset_name, dataset=dataset)
                except KeyError:
                    raise KedroPipelineModelError(
                        f"The provided catalog must contains '{dataset_name}' dataset "
                        "since it is the input of the pipeline."
                    )

        return sub_catalog

    def extract_pipeline_artifacts(
        self, parameters_saving_folder: Optional[Path] = None
    ):
        artifacts = {}
        for name, dataset in self.initial_catalog._datasets.items():
            if name != self.input_name:
                if name.startswith("params:"):
                    # we need to persist it locally for mlflow access
                    absolute_param_path = (
                        parameters_saving_folder / f"params_{name[7:]}.pkl"
                    )
                    persisted_dataset = PickleDataset(
                        filepath=absolute_param_path.as_posix()
                    )
                    persisted_dataset.save(dataset.load())
                    artifact_path = absolute_param_path.as_uri()
                    self._logger.info(
                        f"The parameter '{name[7:]}' is persisted (as pickle) "
                        "at the following location: f'{artifact_path}'"
                    )
                else:
                    # In this second case, we know it cannot be a MemoryDataset
                    # weird bug when directly converting PurePosixPath to windows: it is considered as relative
                    artifact_path = (
                        Path(dataset._filepath.as_posix()).resolve().as_uri()
                    )

                artifacts[name] = artifact_path

        return artifacts

    def load_context(self, context):
        # a consistency check is made when loading the model
        # it would be better to check when saving the model
        # but we rely on a mlflow function for saving, and it is unaware of kedro
        # pipeline structure
        mlflow_artifacts_keys = set(context.artifacts.keys())
        kedro_artifacts_keys = set(self.pipeline.inputs() - {self.input_name})
        if mlflow_artifacts_keys != kedro_artifacts_keys:
            in_artifacts_but_not_inference = (
                mlflow_artifacts_keys - kedro_artifacts_keys
            )
            in_inference_but_not_artifacts = (
                kedro_artifacts_keys - mlflow_artifacts_keys
            )
            raise ValueError(
                "Provided artifacts do not match catalog entries:"
                f"\n    - 'artifacts - inference.inputs()' = : {in_artifacts_but_not_inference}"
                f"\n    - 'inference.inputs() - artifacts' = : {in_inference_but_not_artifacts}"
            )

        updated_catalog = self.initial_catalog.shallow_copy()
        for name, uri in context.artifacts.items():
            updated_catalog._datasets[name]._filepath = Path(uri)
            self.loaded_catalog.save(name=name, data=updated_catalog.load(name))

    def predict(self, context, model_input):
        # we create an empty hook manager but do NOT register hooks
        # because we want this model be executable outside of a kedro project
        hook_manager = _create_hook_manager()

        self.loaded_catalog.save(
            name=self.input_name,
            data=model_input,
        )

        run_output = self.runner.run(
            pipeline=self.pipeline,
            catalog=self.loaded_catalog,
            hook_manager=hook_manager,
        )

        # unpack the result to avoid messing the json
        # file with the name of the Kedro dataset
        unpacked_output = run_output[self.output_name]

        return unpacked_output


class KedroPipelineModelError(Exception):
    """Error raised when the KedroPipelineModel construction fails"""
