from pathlib import Path
from typing import Any, Callable, Dict, Iterable, Union

from kedro.io import DataCatalog, MemoryDataSet
from kedro.pipeline import Pipeline
from kedro.pipeline.node import Node


class PipelineML(Pipeline):
    """
    IMPORTANT NOTE : THIS CLASS IS NOT INTENDED TO BE USED DIRECTLY IN A KEDRO PROJECT. YOU SHOULD USE
    ``pipeline_ml`` FUNCTION FOR MODULAR PIPELINE WHICH IS MORE FLEXIBLE AND USER FRIENDLY.
    SEE INSERT_DOC_URL
    A ``PipelineML`` is a kedro ``Pipeline`` which we assume is a "training" (in the machine learning way)
    pipeline. Basically, training is a higher order function (it generates another function). It implies that:
    -  the outputs of this pipeline are considered as "fitted models", i.e. inputs
    of another inference pipeline (it is very likely that tere are several outputs because we any object
    that depends on the train data (e.g encoders, binarizers, vectorizer, machine learning models...)
    - These outputs will feed another "inference" pipeline (to be used for prediction purpose) whose inputs
     are the outpust of the "training" pipeline, except for one of them (the data to predict).

     This class enables to "link" a training pipeline and an inference pipeline in order to package them
     in mlflow easily. The goal is to call the ``MLflowPipelineHook`` hook after a PipelineMl is called
     in order to trigger mlflow packaging.


    Arguments:
        Pipeline {[type]} -- [description]
    """

    def __init__(
        self,
        nodes: Iterable[Union[Node, "Pipeline"]],
        *args,
        tags: Union[str, Iterable[str]] = None,
        inference: Pipeline
    ):

        super().__init__(nodes, *args, tags=tags)

        self.inference = inference

        free_input = self._check_degrees_of_freedom()
        self._check_model_input_name(free_input)
        self.model_input_name = free_input

    def extract_pipeline_catalog(self, catalog: DataCatalog) -> DataCatalog:
        sub_catalog = DataCatalog()
        for data_set_name in self.inference.inputs():
            if data_set_name == self.model_input_name:
                # there is no obligation that this dataset is persisted
                # thus it is allowed to be an empty memory dataset
                data_set = catalog._data_sets.get(data_set_name) or MemoryDataSet()
                sub_catalog.add(data_set_name=data_set_name, data_set=MemoryDataSet())
            else:
                try:
                    data_set = catalog._data_sets[data_set_name]
                    if isinstance(data_set, MemoryDataSet):
                        raise KedroMlflowPipelineMLDatasetsError(
                            """
                                The datasets of the training pipeline must be persisted locally
                                to be used by the inference pipeline. You must enforce them as
                                non 'MemoryDataSet' in the 'catalog.yml'.
                                Dataset '{data_set_name}' is not persisted currently.
                                """.format(
                                data_set_name=data_set_name
                            )
                        )
                    sub_catalog.add(data_set_name=data_set_name, data_set=data_set)
                except KeyError:
                    raise KedroMlflowPipelineMLDatasetsError(
                        """
                                The provided catalog must contains '{data_set_name}' data_set
                                since it is an input for inference pipeline.
                                """.format(
                            data_set_name=data_set_name
                        )
                    )

        return sub_catalog

    def _check_degrees_of_freedom(self) -> str:
        # check 1 : verify there is only one free
        free_inputs_set = set(self.inference.inputs()) - set(self.outputs())
        if len(free_inputs_set) == 1:
            free_input = list(free_inputs_set)[0]
        else:
            raise KedroMlflowPipelineMLInputsError(
                """
        The following inputs are free for the inference pipeline:
        - {inputs}.
        Only one free input is allowed.
        Please make sure that 'inference' pipeline inputs are 'training' pipeline outputs,
        except one.""".format(
                    inputs="\n     - ".join(free_inputs_set)
                )
            )
        return free_input

    def _check_model_input_name(self, model_input_name: str) -> str:
        flag = (model_input_name is None) or (
            model_input_name in self.inference.inputs()
        )
        if not flag:
            raise KedroMlflowPipelineMLInputsError(
                "model_input_name='{name}' must be in inference.inputs()".format(
                    name=model_input_name
                )
            )

        return flag

    def _turn_pipeline_to_ml(self, pipeline):
        return PipelineML(nodes=pipeline.nodes, inference=self.inference)

    def only_nodes_with_inputs(self, *inputs: str) -> "PipelineML":
        pipeline = super().only_nodes_with_inputs(*inputs)
        return self._turn_pipeline_to_ml(pipeline)

    def from_inputs(self, *inputs: str) -> "PipelineML":
        pipeline = super().from_inputs(*inputs)
        return self._turn_pipeline_to_ml(pipeline)

    def only_nodes_with_outputs(self, *outputs: str) -> "PipelineML":
        pipeline = super().only_nodes_with_outputs(*outputs)
        return self._turn_pipeline_to_ml(pipeline)

    def to_outputs(self, *outputs: str) -> "PipelineML":
        pipeline = super().to_outputs(*outputs)
        return self._turn_pipeline_to_ml(pipeline)

    def from_nodes(self, *node_names: str) -> "PipelineML":
        pipeline = super().from_nodes(*node_names)
        return self._turn_pipeline_to_ml(pipeline)

    def to_nodes(self, *node_names: str) -> "PipelineML":
        pipeline = super().to_nodes(*node_names)
        return self._turn_pipeline_to_ml(pipeline)

    def only_nodes_with_tags(self, *tags: str) -> "PipelineML":
        pipeline = super().only_nodes_with_tags(*tags)
        return self._turn_pipeline_to_ml(pipeline)

    def decorate(self, *decorators: Callable) -> "PipelineML":
        pipeline = super().decorate(*decorators)
        return self._turn_pipeline_to_ml(pipeline)

    def tag(self, tags: Union[str, Iterable[str]]) -> "PipelineML":
        pipeline = super().tag(*tags)
        return self._turn_pipeline_to_ml(pipeline)


class KedroMlflowPipelineMLInputsError(Exception):
    """Error raised when the inputs of KedroPipelineMoel are invalid
    """


class KedroMlflowPipelineMLDatasetsError(Exception):
    """Error raised when the inputs of KedroPipelineMoel are invalid
    """
