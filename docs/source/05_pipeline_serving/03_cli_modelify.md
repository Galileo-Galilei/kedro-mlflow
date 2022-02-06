## Register a pipeline to mlflow with ``KedroPipelineModel`` custom mlflow model

You can log a Kedro ``Pipeline`` to mlflow as a custom model through the CLI with ``modelify`` command:

```bash
kedro mlflow modelify --pipeline=<your-pipeline> --input-name <name-in-catalog-of-input-data>
```

This command will create a new run with an artifact named ``model``. Open the user interface with ``kedro mlflow ui`` to check the result. You can also:
- specify the run id in which you want to log the pipeline with the ``--run-id`` argument
- pass almost all arguments accepted by [``mlflow.pyfunc.log_model``](https://www.mlflow.org/docs/latest/python_api/mlflow.pyfunc.html#mlflow.pyfunc.log_model), see the list of all accepted arguments in the [API documentation](https://kedro-mlflow.readthedocs.io/en/stable/source/08_API/kedro_mlflow.framework.cli.html#modelify)
