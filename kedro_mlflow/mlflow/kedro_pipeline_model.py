from copy import deepcopy
from typing import Any, Callable, Dict, Union

from kedro.io import DataCatalog, MemoryDataSet
from kedro.pipeline import Pipeline
from kedro.runner import SequentialRunner
from mlflow.pyfunc import PythonModel

from kedro_mlflow.pipeline import PipelineML


class KedroPipelineModel(PythonModel):
    def __init__(self, pipeline_ml: PipelineML, catalog: DataCatalog):

        self.pipeline_ml = pipeline_ml
        self.initial_catalog = pipeline_ml.extract_pipeline_catalog(catalog)
        self.loaded_catalog = DataCatalog()

    def load_context(self, context):
        self.loaded_catalog = deepcopy(self.initial_catalog)
        for name, uri in context.artifacts.items():
            if name == self.pipeline_ml.model_input_name:
                self.loaded_catalog._data_sets[name] = MemoryDataSet()
            else:
                self.loaded_catalog._data_sets[name]._filepath = uri

    def predict(self, context, model_input):
        # TODO : checkout out how to pass extra args in predict
        # for instance, to enable parallelization

        self.loaded_catalog.add(
            data_set_name=self.pipeline_ml.model_input_name,
            data_set=MemoryDataSet(model_input),
            replace=True,
        )
        runner = SequentialRunner()
        run_outputs = runner.run(
            pipeline=self.pipeline_ml.inference, catalog=self.loaded_catalog
        )
        return run_outputs
