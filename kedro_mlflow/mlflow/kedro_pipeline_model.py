import logging
from pathlib import Path
from typing import Dict, Optional, Union

from kedro.extras.datasets.pickle import PickleDataSet
from kedro.io import DataCatalog, MemoryDataSet
from kedro.pipeline import Pipeline
from kedro.runner import AbstractRunner, SequentialRunner
from mlflow.pyfunc import PythonModel

from kedro_mlflow.pipeline.pipeline_ml import PipelineML


class KedroPipelineModel(PythonModel):
    def __init__(
        self,
        pipeline: Pipeline,
        catalog: DataCatalog,
        input_name: str,
        runner: Optional[AbstractRunner] = None,
        copy_mode: Optional[Union[Dict[str, str], str]] = None,
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
            You can pass either:
                - None to use Kedro default mode for each dataset
                - a single string ("deepcopy", "copy" and "assign")
                to apply to all datasets
                - a dictionnary with (dataset name, copy_mode) key/values
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
            data_sets={
                name: MemoryDataSet(copy_mode=copy_mode)
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
                for name in self.pipeline.data_sets()
                if name != self.output_name
            }
        elif isinstance(copy_mode, dict):
            # if it is a dict we will retrieve the copy mode when necessary
            # it does not matter if this dict does not contain all the catalog entries
            # the others will be returned as None when accessing with dict.get()
            self._copy_mode = {
                name: None
                for name in self.pipeline.data_sets()
                if name != self.output_name
            }
            self._copy_mode.update(copy_mode)
        else:
            raise TypeError(
                f"'copy_mode' must be a 'str' or a 'dict', not '{type(copy_mode)}'"
            )

    def _extract_pipeline_catalog(self, catalog: DataCatalog) -> DataCatalog:

        sub_catalog = DataCatalog()
        for data_set_name in self.pipeline.inputs():
            if data_set_name == self.input_name:
                # there is no obligation that this dataset is persisted
                # thus it is allowed to be an empty memory dataset
                data_set = catalog._data_sets.get(data_set_name) or MemoryDataSet()
                sub_catalog.add(data_set_name=data_set_name, data_set=data_set)
            else:
                try:
                    data_set = catalog._data_sets[data_set_name]
                    if isinstance(
                        data_set, MemoryDataSet
                    ) and not data_set_name.startswith("params:"):
                        raise KedroPipelineModelError(
                            """
                                The datasets of the training pipeline must be persisted locally
                                to be used by the inference pipeline. You must enforce them as
                                non 'MemoryDataSet' in the 'catalog.yml'.
                                Dataset '{data_set_name}' is not persisted currently.
                                """.format(
                                data_set_name=data_set_name
                            )
                        )
                    self._logger.info(
                        f"The data_set '{data_set_name}' is added to the Pipeline catalog."
                    )
                    sub_catalog.add(data_set_name=data_set_name, data_set=data_set)
                except KeyError:
                    raise KedroPipelineModelError(
                        (
                            f"The provided catalog must contains '{data_set_name}' data_set "
                            "since it is the input of the pipeline."
                        )
                    )

        return sub_catalog

    def extract_pipeline_artifacts(
        self, parameters_saving_folder: Optional[Path] = None
    ):

        artifacts = {}
        for name, dataset in self.initial_catalog._data_sets.items():
            if name != self.input_name:
                if name.startswith("params:"):
                    # we need to persist it locally for mlflow access
                    absolute_param_path = (
                        parameters_saving_folder / f"params_{name[7:]}.pkl"
                    )
                    persisted_dataset = PickleDataSet(
                        filepath=absolute_param_path.as_posix()
                    )
                    persisted_dataset.save(dataset.load())
                    artifact_path = absolute_param_path.as_uri()
                    self._logger.info(
                        (
                            f"The parameter '{name[7:]}' is persisted (as pickle) "
                            "at the following location: '{artifact_path}'"
                        )
                    )
                else:
                    # In this second case, we know it cannot be a MemoryDataSet
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
                (
                    "Provided artifacts do not match catalog entries:"
                    f"\n    - 'artifacts - inference.inputs()' = : {in_artifacts_but_not_inference}"
                    f"\n    - 'inference.inputs() - artifacts' = : {in_inference_but_not_artifacts}"
                )
            )

        updated_catalog = self.initial_catalog.shallow_copy()
        for name, uri in context.artifacts.items():
            updated_catalog._data_sets[name]._filepath = Path(uri)
            self.loaded_catalog.save(name=name, data=updated_catalog.load(name))

    def predict(self, context, model_input):
        # TODO : checkout out how to pass extra args in predict
        # for instance, to enable parallelization

        self.loaded_catalog.save(
            name=self.input_name,
            data=model_input,
        )

        run_output = self.runner.run(
            pipeline=self.pipeline, catalog=self.loaded_catalog
        )

        # unpack the result to avoid messing the json
        # file with the name of the Kedro dataset
        unpacked_output = run_output[self.output_name]

        return unpacked_output


class KedroPipelineModelError(Exception):
    """Error raised when the KedroPipelineModel construction fails"""
