def switch_catalog_logging(catalog, logging_flag=True):
    for name, dataset in catalog._datasets.items():
        if type(dataset).__name__.startswith("Mlflow"):
            catalog._datasets[name]._logging_activated = logging_flag
