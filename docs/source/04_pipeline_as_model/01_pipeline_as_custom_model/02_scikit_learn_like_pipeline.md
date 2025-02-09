# Scikit-learn like Kedro pipelines - Automatically log the inference pipeline after training

For consistency, you may want to **log an inference pipeline** (including some data preprocessing and prediction post processing) **automatically after you ran a training pipeline**, with all the artifacts generated during training (the new model, encoders, vectorizers...).

```{hint}
You can think of ``pipeline_ml_factory`` as "**scikit-learn like pipeline in kedro**". Running ``kedro run -p training`` performs the scikit-learn's ``pipeline.fit()`` operation, storing all components (e.g. a model) we need to reuse further as mlflow artifacts and the inference pipeline as code. Hence, you can later use this mlflow model which will perform the scikit-learn's ``pipeline.predict(new_data)`` operation by running the entire kedro inference pipeline.
```

## Getting started with pipeline_ml_factory

```{note}
Below code assume that for inference, you want to skip some nodes that are training specific, e.g. you don't want to train the model, you just want to predict with it ; you don't want to fit and transform with you encoder, but only transform. Make sure these 2 steps ("train" and "predict", or "fit and "transform") are separated in  2 differnt nodes in your pipeline, so  you can skip the train / transform step at inference time.
```

You can configure your project as follows:

1. Install ``kedro-mlflow`` ``MlflowHook`` (this is done automatically if you have installed ``kedro-mlflow`` in a ``kedro>=0.16.5`` project)
2. Turn your training pipeline in a ``PipelineML`` object  with ``pipeline_ml_factory`` function in your ``pipeline_registry.py``:

    ```python
    # pipeline_registry.py for kedro>=0.17.2 (hooks.py for ``kedro>=0.16.5, <0.17.2)

    from kedro_mlflow_tutorial.pipelines.ml_app.pipeline import create_ml_pipeline


    def register_pipelines(self) -> Dict[str, Pipeline]:
        ml_pipeline = create_ml_pipeline()
        training_pipeline_ml = pipeline_ml_factory(
            training=ml_pipeline.only_nodes_with_tags(
                "training"
            ),  # nodes : encode_labels + preprocess + train_model + predict + postprocess + evaluate
            inference=ml_pipeline.only_nodes_with_tags(
                "inference"
            ),  # nodes : preprocess + predict + postprocess
            input_name="instances",
            log_model_kwargs=dict(
                artifact_path="kedro_mlflow_tutorial",
                conda_env={
                    "python": 3.10,
                    "dependencies": [f"kedro_mlflow_tutorial=={PROJECT_VERSION}"],
                },
                signature="auto",
            ),
        )

        return {"training": training_pipeline_ml}
    ```

3. Persist all your artifacts locally in the ``catalog.yml``

    ```yaml
    label_encoder:
    type: pickle.PickleDataset  # <- This must be any Kedro Dataset other than "MemoryDataset"
    filepath: data/06_models/label_encoder.pkl  # <- This must be a local path, no matter what is your mlflow storage (S3 or other)
    ```

    and as well for your model if necessary.

4. Launch your training pipeline:

    ```bash
    kedro run --pipeline=training
    ```

    **The inference pipeline will _automagically_ be logged as a custom mlflow model** (a ``KedroPipelineModel``) **at the end of the training pipeline!**.

5. Go to the UI, retrieve the run id of your "inference pipeline" model and use it as you want, e.g. in the `catalog.yml`:

    ```yaml
    # catalog.yml

    pipeline_inference_model:
    type: kedro_mlflow.io.models.MlflowModelTrackingDataset
    flavor: mlflow.pyfunc
    pyfunc_workflow: python_model
    artifact_path: kedro_mlflow_tutorial  # the name of your mlflow folder = the model_name in pipeline_ml_factory
    run_id: <your-run-id>  
    ```

    Now you can run the entire inference pipeline inside a node as part of another pipeline.

## Advanced configuration for pipeline_ml_factory

### Register the model as a new version in the mlflow registry

The ``log_model_kwargs`` argument is passed to the underlying [mlflow.pyfunc.log_model](https://mlflow.org/docs/latest/python_api/mlflow.pyfunc.html#mlflow.pyfunc.log_model). Specifically, it accepts a ``registered_model_name`` argument :

```python
pipeline_ml_factory(
    training=ml_pipeline.only_nodes_with_tags("training"),
    inference=ml_pipeline.only_nodes_with_tags("inference"),
    input_name="instances",
    log_model_kwargs=dict(
        artifact_path="kedro_mlflow_tutorial",
        registered_model_name="my_inference_pipeline",  # a new version of "my_infernce_pipeline" model will be registered each time you run the "training" pipeline
        conda_env={
            "python": 3.10,
            "dependencies": [f"kedro_mlflow_tutorial=={PROJECT_VERSION}"],
        },
        signature="auto",
    ),
)
```

## Complete step by step demo project with code

A step by step tutorial with code is available in the [kedro-mlflow-tutorial repository on github](https://github.com/Galileo-Galilei/kedro-mlflow-tutorial#serve-the-inference-pipeline-to-a-end-user).

You have also other resources to understand the rationale:

- an explanation of the [``PipelineML`` class in the python objects section](https://kedro-mlflow.readthedocs.io/en/latest/source/05_API/01_python_objects/03_Pipelines.html)
- detailed explanations [on this issue](https://github.com/Galileo-Galilei/kedro-mlflow/issues/16) and [this discussion](https://github.com/Galileo-Galilei/kedro-mlflow/discussions/229).
- an example of use in a user project [in this repo](https://github.com/laurids-reichardt/kedro-examples/blob/kedro-mlflow-hotfix2/text-classification/src/text_classification/pipelines/pipeline.py).
