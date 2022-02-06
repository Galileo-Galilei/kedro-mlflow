# Opening the UI

## The mlflow user interface

Mlflow offers a user interface (UI) that enable to browse the run history.

## The ``kedro-mlflow`` helper

When you use a local storage for kedro mlflow, you can call a [mlflow cli command](https://www.mlflow.org/docs/latest/quickstart.html#viewing-the-tracking-ui) to launch the UI if you do not have a [mlflow tracking server configured](https://www.mlflow.org/docs/latest/tracking.html#tracking-ui).

To ensure this UI is linked to the tracking uri specified configuration, ``kedro-mlflow`` offers the following command:

```console
kedro mlflow ui
```

which is a wrapper for  ``kedro ui`` command with the tracking uri (as well as the port and host) specified the ``mlflow.yml`` file.

Opens ``http://localhost:5000`` in your browser to see the UI after calling previous command. If your ``mlflow_tracking_uri`` is a ``http[s]`` URL, the command will automatically open it.
