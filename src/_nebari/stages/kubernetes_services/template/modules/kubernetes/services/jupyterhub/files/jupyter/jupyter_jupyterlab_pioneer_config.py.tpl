import logging
import json


default_log_format = "%(asctime)s %(levelname)9s %(lineno)4s %(module)s: %(message)s"
log_format = "${log_format}"

logging.basicConfig(
    level=logging.INFO,
    format=log_format if log_format else default_log_format
)

logger = logging.getLogger(__name__)

CUSTOM_EXPORTER_NAME = "MyCustomExporter"


def my_custom_exporter(args):
    """Custom exporter to log JupyterLab events to command line."""
    logger.info(json.dumps(args.get("data")))
    return {
        "exporter": CUSTOM_EXPORTER_NAME,
        "message": ""
    }


c.JupyterLabPioneerApp.exporters = [
    {
        # sends telemetry data to the browser console
        "type": "console_exporter",
    },
    {
        # sends telemetry data (json) to the python console jupyter is running on
        "type": "custom_exporter",
        "args": {
            "id": CUSTOM_EXPORTER_NAME
            # add additional args for your exporter function here
        },
    }
]

c.JupyterLabPioneerApp.custom_exporter = {
    CUSTOM_EXPORTER_NAME: my_custom_exporter,
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
