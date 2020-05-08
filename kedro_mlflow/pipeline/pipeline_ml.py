from typing import Callable, Iterable, Union

from kedro.io import DataCatalog, MemoryDataSet
from kedro.pipeline import Pipeline
from kedro.pipeline.node import Node

MSG_NOT_IMPLEMENTED = "This method is not implemented because it does not make sens for 'PipelineML'. Manipulate directly the training pipeline and recreate the 'PipelineML' with 'pipeline_ml' factory"


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
        inference: Pipeline,
        input_name: str,
    ):

        super().__init__(nodes, *args, tags=tags)

        self.inference = inference

        self._check_input_name(input_name)
        self.input_name = input_name

    def extract_pipeline_catalog(self, catalog: DataCatalog) -> DataCatalog:
        sub_catalog = DataCatalog()
        for data_set_name in self.inference.inputs():
            if data_set_name == self.input_name:
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

    @property
    def training(self):
        return Pipeline(self.nodes)

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

    def _check_input_name(self, input_name: str) -> str:
        free_input = self._check_degrees_of_freedom()
        if input_name != free_input:
            raise KedroMlflowPipelineMLInputsError(
                f"input_name='{input_name}' but the only unconstrained input is {{'{free_input}'}}"
            )

    def _turn_pipeline_to_ml(self, pipeline):
        return PipelineML(
            nodes=pipeline.nodes, inference=self.inference, input_name=self.input_name
        )

    def only_nodes_with_inputs(self, *inputs: str) -> "PipelineML":  # pragma: no cover
        raise NotImplementedError(MSG_NOT_IMPLEMENTED)

    def from_inputs(self, *inputs: str) -> "PipelineML":
        # exceptionnally, we don't call super() because it raises
        # a self._check_degrees_of_freedom() error even if valid cases
        # this is because the pipeline is reconstructed node by node
        # (only the first node may lead to invalid pipeline (e.g.
        # with not all artifacts)), even if the whole pipeline is ok
        # we want the call to self._check_degrees_of_freedom() only call at the end.
        pipeline = self.training.from_inputs(*inputs)
        return self._turn_pipeline_to_ml(pipeline)

    def only_nodes_with_outputs(
        self, *outputs: str
    ) -> "PipelineML":  # pragma: no cover
        raise NotImplementedError(MSG_NOT_IMPLEMENTED)

    def to_outputs(self, *outputs: str) -> "PipelineML":  # pragma: no cover
        raise NotImplementedError(MSG_NOT_IMPLEMENTED)

    def from_nodes(self, *node_names: str) -> "PipelineML":
        # see from_inputs for an explanation of why we don't call super()
        pipeline = self.training.from_nodes(*node_names)
        return self._turn_pipeline_to_ml(pipeline)

    def to_nodes(self, *node_names: str) -> "PipelineML":
        # see from_inputs for an explanation of why we don't call super()
        pipeline = self.training.to_nodes(*node_names)
        return self._turn_pipeline_to_ml(pipeline)

    def only_nodes_with_tags(self, *tags: str) -> "PipelineML":
        # see from_inputs for an explanation of why we don't call super()
        pipeline = self.training.only_nodes_with_tags(*tags)
        return self._turn_pipeline_to_ml(pipeline)

    def decorate(self, *decorators: Callable) -> "PipelineML":
        pipeline = super().decorate(*decorators)
        return self._turn_pipeline_to_ml(pipeline)

    def tag(self, tags: Union[str, Iterable[str]]) -> "PipelineML":
        pipeline = super().tag(*tags)
        return self._turn_pipeline_to_ml(pipeline)

    def __add__(self, other):  # pragma: no cover
        raise NotImplementedError(MSG_NOT_IMPLEMENTED)

    def __sub__(self, other):  # pragma: no cover
        raise NotImplementedError(MSG_NOT_IMPLEMENTED)

    def __and__(self, other):
        # kept for compatibility with KedroContext _filter_pipelinefunction
        new_pipeline = super().__and__(other)
        return self._turn_pipeline_to_ml(new_pipeline)

    def __or__(self, other):  # pragma: no cover
        raise NotImplementedError(MSG_NOT_IMPLEMENTED)


class KedroMlflowPipelineMLInputsError(Exception):
    """Error raised when the inputs of KedroPipelineMoel are invalid
    """


class KedroMlflowPipelineMLDatasetsError(Exception):
    """Error raised when the inputs of KedroPipelineMoel are invalid
    """
