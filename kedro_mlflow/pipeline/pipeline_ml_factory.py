from kedro.pipeline import Pipeline

from kedro_mlflow.pipeline.pipeline_ml import PipelineML


def pipeline_ml_factory(
    training: Pipeline,
    inference: Pipeline,
    input_name: str = None,
    kpm_kwargs=None,
    log_model_kwargs=None,
) -> PipelineML:
    """This function is a helper to create `PipelineML`
    object directly from two Kedro `Pipelines` (one of
    training and one of inference) .

    Args:
        training (Pipeline): The `Pipeline` object that creates
            all mlflow artifacts for prediction (the model,
            but also encoders, binarizers, tokenizers...).
            These artifacts must be persisted in the catalog.yml.
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
        logging_kwargs:
            extra arguments to be passed to `mlflow.pyfunc.log_model`
            when the PipelineML object is automatically saved at the end of a run.
            See mlflow documentation to see all available options: https://www.mlflow.org/docs/latest/python_api/mlflow.pyfunc.html#mlflow.pyfunc.log_model

    Returns:
        PipelineML: A `PipelineML` which is automatically
            discovered by the `MlflowHook` and
            contains all the information for logging the
            inference pipeline as a Mlflow Model.
    """

    pipeline = PipelineML(
        nodes=training.nodes,
        inference=inference,
        input_name=input_name,
        kpm_kwargs=kpm_kwargs,
        log_model_kwargs=log_model_kwargs,
    )
    return pipeline
