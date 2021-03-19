def switch_catalog_logging(catalog, logging_flag=True):
    for name, data_set in catalog._data_sets.items():
        if type(data_set).__name__.startswith("Mlflow"):
            catalog._data_sets[name]._logging_activated = logging_flag
