from typing import Dict, Iterable, Optional, Union

from kedro.pipeline import Pipeline
from kedro.pipeline.node import Node

MSG_NOT_IMPLEMENTED = (
    "This method is not implemented because it does "
    "not make sense for 'PipelineML'. "
    "Manipulate directly the training pipeline and "
    "recreate the 'PipelineML' with 'pipeline_ml_factory' factory."
)


class PipelineML(Pipeline):
    """
    IMPORTANT NOTE : THIS CLASS IS NOT INTENDED TO BE USED DIRECTLY IN A KEDRO PROJECT. YOU SHOULD USE
    ``pipeline_ml_factory`` FUNCTION FOR MODULAR PIPELINE WHICH IS MORE FLEXIBLE AND USER FRIENDLY.
    SEE INSERT_DOC_URL

    A ``PipelineML`` is a kedro ``Pipeline`` which we assume is a "training" (in the machine learning way)
    pipeline. Basically, "training" is a higher order function (it generates another function). It implies that:
    -  the outputs of this pipeline are considered as "fitted models", i.e. inputs
    of another inference pipeline (it is very likely that there are several outputs because we need to store any
    object that depends on the train data (e.g encoders, binarizers, vectorizer, machine learning models...)
    - These outputs will feed another "inference" pipeline (to be used for prediction purpose) whose inputs
     are the outputs of the "training" pipeline, except for one of them (the new data to predict).

     This class enables to "link" a training pipeline and an inference pipeline in order to package them
     in mlflow easily. The goal is to call the ``MlflowHook`` hook after a PipelineMl is called
     in order to trigger mlflow packaging.

    """

    KPM_KWARGS_DEFAULT = {}
    LOG_MODEL_KWARGS_DEFAULT = {"signature": "auto", "artifact_path": "model"}

    def __init__(
        self,
        nodes: Iterable[Union[Node, Pipeline]],
        *args,
        tags: Optional[Union[str, Iterable[str]]] = None,
        inference: Pipeline,
        input_name: str,
        kpm_kwargs: Optional[Dict[str, str]] = None,
        log_model_kwargs: Optional[Dict[str, str]] = None,
    ):

        """Store all necessary information for calling mlflow.log_model in the pipeline.

        Args:
            nodes (Iterable[Union[Node, Pipeline]]): The `node`s
                of the training pipeline.
            tags (Union[str, Iterable[str]], optional): Optional
                set of tags to be applied to all the pipeline
                nodes. Defaults to None.
            inference (Pipeline): A `Pipeline` object which will be
                stored in mlflow and use the output(s)
                of the training pipeline (namely, the model)
                to predict the outcome.
            input_name (str, optional): The name of the dataset in
                the catalog.yml which the model's user must provide
                for prediction (i.e. the data). Defaults to None.
            kpm_kwargs:
                extra arguments to be passed to `KedroPipelineModel`
                when the PipelineML object is automatically saved at the end of a run.
                This includes:
                    - `copy_mode`: the copy_mode to be used for underlying dataset
                    when loaded in memory
                    - `runner`: the kedro runner to run the model with
            log_model_kwargs:
                extra arguments to be passed to `mlflow.pyfunc.log_model`, e.g.:
                    - "signature" accepts an extra "auto" which automatically infer the signature
                    based on "input_name" dataset

        """

        super().__init__(nodes, *args, tags=tags)

        self.inference = inference
        self.input_name = input_name
        # they will be passed to KedroPipelineModel to enable flexibility

        kpm_kwargs = kpm_kwargs or {}
        self.kpm_kwargs = {**self.KPM_KWARGS_DEFAULT, **kpm_kwargs}

        log_model_kwargs = log_model_kwargs or {}
        self.log_model_kwargs = {**self.LOG_MODEL_KWARGS_DEFAULT, **log_model_kwargs}
        self._check_consistency()

    @property
    def training(self) -> Pipeline:
        return Pipeline(self.nodes)

    @property
    def inference(self) -> str:
        return self._inference

    @inference.setter
    def inference(self, inference: Pipeline) -> None:
        self._check_inference(inference)
        self._inference = inference

    @property
    def input_name(self) -> str:
        return self._input_name

    @input_name.setter
    def input_name(self, name: str) -> None:
        allowed_names = self.inference.inputs()
        pp_allowed_names = "\n    - ".join(allowed_names)
        if name not in allowed_names:
            raise KedroMlflowPipelineMLError(
                (
                    f"input_name='{name}' but it must be an input of 'inference'"
                    f", i.e. one of: \n    - {pp_allowed_names}"
                )
            )
        self._input_name = name

    def _check_inference(self, inference: Pipeline) -> None:
        nb_outputs = len(inference.outputs())
        outputs_txt = "\n - ".join(inference.outputs())
        if len(inference.outputs()) != 1:
            raise KedroMlflowPipelineMLError(
                (
                    "The inference pipeline must have one"
                    " and only one output. You are trying"
                    " to set a inference pipeline with"
                    f" '{nb_outputs}' output(s): \n - {outputs_txt}"
                    " "
                )
            )

    def _check_consistency(self) -> None:

        inference_parameters = {
            input for input in self.inference.inputs() if input.startswith("params:")
        }

        free_inputs_set = (
            self.inference.inputs()
            - {self.input_name}
            - self.all_outputs()
            - self.inputs()
            - inference_parameters  # it is allowed to pass parameters: they will be automatically persisted by the hook
        )

        if len(free_inputs_set) > 0:
            input_set_txt = "\n     - ".join(free_inputs_set)
            raise KedroMlflowPipelineMLError(
                (
                    "The following inputs are free for the inference pipeline:\n"
                    f"    - {input_set_txt}."
                    " \nNo free input is allowed."
                    " Please make sure that 'inference.inputs()' are all"
                    " in 'training.all_outputs() + training.inputs()'"
                    "except 'input_name' and parameters which starts with 'params:'."
                )
            )

        return None

    def _turn_pipeline_to_ml(self, pipeline: Pipeline):
        return PipelineML(
            nodes=pipeline.nodes,
            inference=self.inference,
            input_name=self.input_name,
            kpm_kwargs=self.kpm_kwargs,
            log_model_kwargs=self.log_model_kwargs,
        )

    def only_nodes(self, *node_names: str) -> "Pipeline":  # pragma: no cover
        raise NotImplementedError(MSG_NOT_IMPLEMENTED)

    def only_nodes_with_namespace(
        self, node_namespace: str
    ) -> "Pipeline":  # pragma: no cover
        raise NotImplementedError(MSG_NOT_IMPLEMENTED)

    def only_nodes_with_inputs(self, *inputs: str) -> "PipelineML":  # pragma: no cover
        raise NotImplementedError(MSG_NOT_IMPLEMENTED)

    def from_inputs(self, *inputs: str) -> "PipelineML":  # pragma: no cover
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
        # see from_inputs for an explanation of why we don't call super()
        pipeline = self.training.from_nodes(*outputs)
        return self._turn_pipeline_to_ml(pipeline)

    def from_nodes(self, *node_names: str) -> "PipelineML":  # pragma: no cover
        # see from_inputs for an explanation of why we don't call super()
        pipeline = self.training.from_nodes(*node_names)
        return self._turn_pipeline_to_ml(pipeline)

    def to_nodes(self, *node_names: str) -> "PipelineML":  # pragma: no cover
        # see from_inputs for an explanation of why we don't call super()
        pipeline = self.training.to_nodes(*node_names)
        return self._turn_pipeline_to_ml(pipeline)

    def only_nodes_with_tags(self, *tags: str) -> "PipelineML":  # pragma: no cover
        # see from_inputs for an explanation of why we don't call super()
        pipeline = self.training.only_nodes_with_tags(*tags)
        return self._turn_pipeline_to_ml(pipeline)

    def tag(self, tags: Union[str, Iterable[str]]) -> "PipelineML":
        pipeline = super().tag(*tags)
        return self._turn_pipeline_to_ml(pipeline)

    def filter(
        self,
        tags: Iterable[str] = None,
        from_nodes: Iterable[str] = None,
        to_nodes: Iterable[str] = None,
        node_names: Iterable[str] = None,
        from_inputs: Iterable[str] = None,
        to_outputs: Iterable[str] = None,
        node_namespace: str = None,
    ) -> "Pipeline":
        # see from_inputs for an explanation of why we don't call super()
        pipeline = self.training.filter(
            tags=tags,
            from_nodes=from_nodes,
            to_nodes=to_nodes,
            node_names=node_names,
            from_inputs=from_inputs,
            to_outputs=to_outputs,
            node_namespace=node_namespace,
        )
        return self._turn_pipeline_to_ml(pipeline)

    def __add__(self, other):  # pragma: no cover
        raise NotImplementedError(MSG_NOT_IMPLEMENTED)

    def __sub__(self, other):  # pragma: no cover
        raise NotImplementedError(MSG_NOT_IMPLEMENTED)

    def __and__(self, other):  # pragma: no cover
        # kept for compatibility with KedroContext _filter_pipelinefunction
        new_pipeline = super().__and__(other)
        return self._turn_pipeline_to_ml(new_pipeline)

    def __or__(self, other):  # pragma: no cover
        raise NotImplementedError(MSG_NOT_IMPLEMENTED)


class KedroMlflowPipelineMLError(Exception):
    """Error raised when the KedroPipelineModel construction fails"""
