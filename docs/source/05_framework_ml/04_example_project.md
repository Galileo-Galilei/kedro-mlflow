# Project example

## 5 mn summary

If you don't want to read the entire explanations, here is a summary:

1. Install ``kedro-mlflow`` ``MlflowPipelineHook`` (this is done automatically if you have installed ``kedro-mlflow`` in a ``kedro>=0.16.5`` project)
2. Turn your training pipeline in a ``PipelineML`` object  with ``pipeline_ml_factory`` function in your ``hooks.py``:

    ```python
    # hooks.py
    from kedro_mlflow_tutorial.pipelines.ml_app.pipeline import create_ml_pipeline

    ...

    class ProjectHooks:
        @hook_impl
        def register_pipelines(self) -> Dict[str, Pipeline]:

            ...

            ml_pipeline = create_ml_pipeline()
            training_pipeline_ml = pipeline_ml_factory(
                training=ml_pipeline.only_nodes_with_tags("training"),
                inference=ml_pipeline.only_nodes_with_tags("inference"),
                input_name="instances",
                model_name="kedro_mlflow_tutorial",
                conda_env={
                    "python": 3.7,
                    "pip": [f"kedro_mlflow_tutorial=={PROJECT_VERSION}"],
                },
                model_signature="auto",
            )

            ...

            return {
                "training": training_pipeline_ml,
                ...
            }
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

## Complete step by step demo project with code

A step by step tutorial with code is available in the [kedro-mlflow-tutorial repository on github](https://github.com/Galileo-Galilei/kedro-mlflow-tutorial#serve-the-inference-pipeline-to-a-end-user).
