# Add JupyterLabPioneer

def my_custom_exporter(args):
    # write your own exporter logic here
    import json
    print(json.dumps(args.get("data")))
    return {
        "exporter":  "MyCustomExporter",
        "message": ""
    }


c.JupyterLabPioneerApp.exporters = [
    {
        # sends telemetry data to the browser console
        "type": "console_exporter",
    },
    # {
    #     # sends telemetry data to the python console jupyter is running on
    #     "type": "command_line_exporter",
    # },
    # sends telemetry data (json) to the python console jupyter is running on
    {
        "type": "custom_exporter",
        "args": {
            "id": "MyCustomExporter"
            # add additional args for your exporter function here
        },
    }
]

c.JupyterLabPioneerApp.custom_exporter = {
    'MyCustomExporter': my_custom_exporter,
}

c.JupyterLabPioneerApp.activeEvents = [
    {"name": "ActiveCellChangeEvent", "logWholeNotebook": False},
    {"name": "CellAddEvent", "logWholeNotebook": False},
    {"name": "CellEditEvent", "logWholeNotebook": False},
    {"name": "CellExecuteEvent", "logWholeNotebook": False},
    {"name": "CellRemoveEvent", "logWholeNotebook": False},
    {"name": "ClipboardCopyEvent", "logWholeNotebook": False},
    {"name": "ClipboardCutEvent", "logWholeNotebook": False},
    {"name": "ClipboardPasteEvent", "logWholeNotebook": False},
    {"name": "NotebookHiddenEvent", "logWholeNotebook": False},
    {"name": "NotebookOpenEvent", "logWholeNotebook": False},
    {"name": "NotebookSaveEvent", "logWholeNotebook": False},
    {"name": "NotebookScrollEvent", "logWholeNotebook": False},
    {"name": "NotebookVisibleEvent", "logWholeNotebook": False},
]
