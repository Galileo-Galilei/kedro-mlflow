from copy import deepcopy
from pathlib import Path
from typing import Dict, Optional, Union

from kedro.io import DataCatalog, MemoryDataSet
from kedro.runner import AbstractRunner, SequentialRunner
from mlflow.pyfunc import PythonModel

from kedro_mlflow.pipeline.pipeline_ml import PipelineML


class KedroPipelineModel(PythonModel):
    def __init__(
        self,
        pipeline_ml: PipelineML,
        catalog: DataCatalog,
        runner: Optional[AbstractRunner] = None,
        copy_mode: Optional[Union[Dict[str, str], str]] = None,
    ):
        """[summary]

        Args:
            pipeline_ml (PipelineML): A PipelineML object to
            store as a Mlflow Model

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

        self.pipeline_ml = pipeline_ml
        self.initial_catalog = pipeline_ml._extract_pipeline_catalog(catalog)
        # we have the guarantee that there is only one output in inference
        self.output_name = list(pipeline_ml.inference.outputs())[0]
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
    def copy_mode(self):
        return self._copy_mode

    @copy_mode.setter
    def copy_mode(self, copy_mode):

        if isinstance(copy_mode, str) or copy_mode is None:
            # if it is a string, we must create manually the dictionary
            # of all catalog entries with this copy_mode
            self._copy_mode = {
                name: copy_mode
                for name in self.pipeline_ml.inference.data_sets()
                if name != self.output_name
            }
        elif isinstance(copy_mode, dict):
            # if it is a dict we will retrieve the copy mode when necessary
            # it does not matter if this dict does not contain all the catalog entries
            # the others will be returned as None when accessing with dict.get()
            self._copy_mode = {
                name: None
                for name in self.pipeline_ml.inference.data_sets()
                if name != self.output_name
            }
            self._copy_mode.update(copy_mode)
        else:
            raise TypeError(
                f"'copy_mode' must be a 'str' or a 'dict', not '{type(copy_mode)}'"
            )

    def load_context(self, context):

        # a consistency check is made when loading the model
        # it would be better to check when saving the model
        # but we rely on a mlflow function for saving, and it is unaware of kedro
        # pipeline structure
        mlflow_artifacts_keys = set(context.artifacts.keys())
        kedro_artifacts_keys = set(
            self.pipeline_ml.inference.inputs() - {self.pipeline_ml.input_name}
        )
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

        updated_catalog = deepcopy(self.initial_catalog)
        for name, uri in context.artifacts.items():
            updated_catalog._data_sets[name]._filepath = Path(uri)
            self.loaded_catalog.save(name=name, data=updated_catalog.load(name))

    def predict(self, context, model_input):
        # TODO : checkout out how to pass extra args in predict
        # for instance, to enable parallelization

        self.loaded_catalog.save(
            name=self.pipeline_ml.input_name,
            data=model_input,
        )

        run_output = self.runner.run(
            pipeline=self.pipeline_ml.inference, catalog=self.loaded_catalog
        )

        # unpack the result to avoid messing the json
        # file with the name of the Kedro dataset
        unpacked_output = run_output[self.output_name]

        return unpacked_output
