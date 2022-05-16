## Automatically log an inference after running the training pipeline

For consistency, you may want to log an inference pipeline (including some data preprocessing and prediction post processing) after you ran a training pipeline, with all the artifacts newly generated (the new model, encoders, vectorizers...).

### Getting started

1. Install ``kedro-mlflow`` ``MlflowHook`` (this is done automatically if you have installed ``kedro-mlflow`` in a ``kedro>=0.16.5`` project)
2. Turn your training pipeline in a ``PipelineML`` object  with ``pipeline_ml_factory`` function in your ``pipeline_registry.py``:

    ```python
    # pipeline_registry.py for kedro>=0.17.2 (hooks.py for ``kedro>=0.16.5, <0.17.2)

    from kedro_mlflow_tutorial.pipelines.ml_app.pipeline import create_ml_pipeline


    def register_pipelines(self) -> Dict[str, Pipeline]:

        ml_pipeline = create_ml_pipeline()
        training_pipeline_ml = pipeline_ml_factory(
            training=ml_pipeline.only_nodes_with_tags("training"),
            inference=ml_pipeline.only_nodes_with_tags("inference"),
            input_name="instances",
            log_model_kwargs=dict(
                artifact_path="kedro_mlflow_tutorial",
                conda_env={
                    "python": 3.7,
                    "dependencies": [f"kedro_mlflow_tutorial=={PROJECT_VERSION}"],
                },
                signature="auto",
            ),
        )

        return {"training": training_pipeline_ml}
    ```

3. Persist your artifacts locally in the ``catalog.yml``

    ```yaml
    label_encoder:
    type: pickle.PickleDataSet  # <- This must be any Kedro Dataset other than "MemoryDataSet"
    filepath: data/06_models/label_encoder.pkl  # <- This must be a local path, no matter what is your mlflow storage (S3 or other)
    ```

4. Launch your training pipeline:

    ```bash
    kedro run --pipeline=training
    ```

    **The inference pipeline will _automagically_ be logged as a mlflow model at the end!**

5. Go to the UI, retrieve the run id of your "inference pipeline" model and use it as you want, e.g. in the `catalog.yml`:

    ```yaml
    # catalog.yml

    pipeline_inference_model:
    type: kedro_mlflow.io.models.MlflowModelLoggerDataSet
    flavor: mlflow.pyfunc
    pyfunc_workflow: python_model
    artifact_path: kedro_mlflow_tutorial  # the name of your mlflow folder = the model_name in pipeline_ml_factory
    run_id: <your-run-id>  
    ```

### Complete step by step demo project with code

A step by step tutorial with code is available in the [kedro-mlflow-tutorial repository on github](https://github.com/Galileo-Galilei/kedro-mlflow-tutorial#serve-the-inference-pipeline-to-a-end-user).

You have also other resources to understand the rationale:
- an explanation of the [``PipelineML`` class in the python objects section](../07_python_objects/03_Pipelines.md)
- detailed explanations [on this issue](https://github.com/Galileo-Galilei/kedro-mlflow/issues/16).
- an example of use in a user project [in this repo](https://github.com/laurids-reichardt/kedro-examples/blob/kedro-mlflow-hotfix2/text-classification/src/text_classification/pipelines/pipeline.py).

### Motivation

You can find more about the motivations in <https://kedro-mlflow.readthedocs.io/en/stable/source/05_framework_ml/index.html>.
