from copy import deepcopy
from pathlib import Path

from kedro.io import DataCatalog, MemoryDataSet
from kedro.runner import SequentialRunner
from mlflow.pyfunc import PythonModel

from kedro_mlflow.pipeline.pipeline_ml import PipelineML


class KedroPipelineModel(PythonModel):
    def __init__(self, pipeline_ml: PipelineML, catalog: DataCatalog):

        self.pipeline_ml = pipeline_ml
        self.initial_catalog = pipeline_ml._extract_pipeline_catalog(catalog)
        self.loaded_catalog = DataCatalog()
        # we have the guarantee that there is only one output in inference
        self.output_name = list(pipeline_ml.inference.outputs())[0]

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

        self.loaded_catalog = deepcopy(self.initial_catalog)
        for name, uri in context.artifacts.items():
            self.loaded_catalog._data_sets[name]._filepath = Path(uri)

    def predict(self, context, model_input):
        # TODO : checkout out how to pass extra args in predict
        # for instance, to enable parallelization

        self.loaded_catalog.add(
            data_set_name=self.pipeline_ml.input_name,
            data_set=MemoryDataSet(model_input),
            replace=True,
        )
        runner = SequentialRunner()
        run_outputs = runner.run(
            pipeline=self.pipeline_ml.inference, catalog=self.loaded_catalog
        )
        return run_outputs[
            self.output_name
        ]  # unpack the result to avoid messing the json output
