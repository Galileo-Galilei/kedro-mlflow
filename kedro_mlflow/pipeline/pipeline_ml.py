import logging
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, Optional, Union

from kedro.extras.datasets.pickle import PickleDataSet
from kedro.io import DataCatalog, MemoryDataSet
from kedro.pipeline import Pipeline
from kedro.pipeline.node import Node
from mlflow.models import ModelSignature

MSG_NOT_IMPLEMENTED = (
    "This method is not implemented because it does"
    "not make sense for 'PipelineML'."
    "Manipulate directly the training pipeline and"
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
     in mlflow easily. The goal is to call the ``MLflowPipelineHook`` hook after a PipelineMl is called
     in order to trigger mlflow packaging.

    """

    def __init__(
        self,
        nodes: Iterable[Union[Node, Pipeline]],
        *args,
        tags: Optional[Union[str, Iterable[str]]] = None,
        inference: Pipeline,
        input_name: str,
        conda_env: Optional[Union[str, Path, Dict[str, Any]]] = None,
        model_name: Optional[str] = "model",
        model_signature: Union[ModelSignature, str, None] = "auto",
        **kwargs,
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
            conda_env (Union[str, Path, Dict[str, Any]], optional):
                The minimal conda environment necessary for the
                inference `Pipeline`. It can be either :
                    - a path to a "requirements.txt": In this case
                        the packages are parsed and a conda env with
                        your current python_version and these
                        dependencies is returned.
                    - a path to an "environment.yml" : the file is
                        uploaded "as is".
                    - a Dict : used as the environment
                    - None: a base conda environment with your
                        current python version and your project
                        version at training time.
                Defaults to None.
            model_name (Union[str, None], optional): The name of
                the folder where the model will be stored in
                remote mlflow. Defaults to "model".
            model_signature (Union[ModelSignature, bool]): The mlflow
             signature of the input dataframe common to training
             and inference.
                   - If 'auto', it is infered automatically
                   - If None, no signature is used
                   - if a `ModelSignature` instance, passed
                   to the underlying dataframe
            kwargs:
                extra arguments to be passed to `KedroPipelineModel`
                when the PipelineML object is automatically saved at the end of a run.
                This includes:
                    - `copy_mode`: the copy_mode to be used for underlying dataset
                    when loaded in memory
                    - `runner`: the kedro runner to run the model with
        """

        super().__init__(nodes, *args, tags=tags)

        self.inference = inference
        self.conda_env = conda_env
        self.model_name = model_name
        self.input_name = input_name
        self.model_signature = model_signature
        self.kwargs = kwargs  # its purpose is to be eventually reused when saving the model within a hook
        self._check_consistency()

    @property
    def _logger(self) -> logging.Logger:
        return logging.getLogger(__name__)

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
            raise KedroMlflowPipelineMLInputsError(
                (
                    f"input_name='{name}' but it must be an input of 'inference'"
                    f", i.e. one of: \n    - {pp_allowed_names}"
                )
            )
        self._input_name = name

    @property
    def model_signature(self) -> str:
        return self._model_signature

    @model_signature.setter
    def model_signature(self, model_signature: ModelSignature) -> None:
        if model_signature is not None:
            if not isinstance(model_signature, ModelSignature):
                if model_signature != "auto":
                    raise ValueError(
                        f"model_signature must be one of 'None', 'auto', or a 'ModelSignature' Object, got '{type(model_signature)}'"
                    )
        self._model_signature = model_signature

    def _check_inference(self, inference: Pipeline) -> None:
        nb_outputs = len(inference.outputs())
        outputs_txt = "\n - ".join(inference.outputs())
        if len(inference.outputs()) != 1:
            raise KedroMlflowPipelineMLOutputsError(
                (
                    "The inference pipeline must have one"
                    " and only one output. You are trying"
                    " to set a inference pipeline with"
                    f" '{nb_outputs}' output(s): \n - {outputs_txt}"
                    " "
                )
            )

    def _extract_pipeline_catalog(self, catalog: DataCatalog) -> DataCatalog:

        # check that the pipeline is consistent in case its attributes have been
        # modified manually
        self._check_consistency()

        sub_catalog = DataCatalog()
        for data_set_name in self.inference.inputs():
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
                    self._logger.info(
                        f"The data_set '{data_set_name}' is added to the PipelineML catalog."
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

    def extract_pipeline_artifacts(self, catalog: DataCatalog, temp_folder: Path):
        pipeline_catalog = self._extract_pipeline_catalog(catalog)

        artifacts = {}
        for name, dataset in pipeline_catalog._data_sets.items():
            if name != self.input_name:
                if name.startswith("params:"):
                    # we need to persist it locally for mlflow access
                    absolute_param_path = temp_folder / f"params_{name[7:]}.pkl"
                    persisted_dataset = PickleDataSet(
                        filepath=absolute_param_path.as_posix()
                    )
                    persisted_dataset.save(dataset.load())
                    artifact_path = absolute_param_path.as_uri()
                else:
                    # In this second case, we know it cannot be a MemoryDataSet
                    # weird bug when directly converting PurePosixPath to windows: it is considered as relative
                    artifact_path = (
                        Path(dataset._filepath.as_posix()).resolve().as_uri()
                    )

                artifacts[name] = artifact_path

        return artifacts

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
            raise KedroMlflowPipelineMLInputsError(
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
    """Error raised when the inputs of KedroPipelineModel are invalid"""


class KedroMlflowPipelineMLDatasetsError(Exception):
    """Error raised when the inputs of KedroPipelineMoel are invalid"""


class KedroMlflowPipelineMLOutputsError(Exception):
    """Error raised when the outputs of KedroPipelineModel are invalid"""
