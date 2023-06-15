from typing import List, Dict
import functools
import logging
import os
import contextlib
import pathlib

from _nebari.provider import terraform
from _nebari.stages.base import get_available_stages
from _nebari.utils import timer
from nebari import schema

logger = logging.getLogger(__name__)


def destroy_stages(config: schema.Main):
    stage_outputs = {}
    status = {}
    with contextlib.ExitStack() as stack:
        for stage in get_available_stages():
            s = stage(output_directory=pathlib.Path("."), config=config)
            stack.enter_context(s.destroy(stage_outputs, status))
    return status


def destroy_configuration(config: schema.Main):
    logger.info(
        """Removing all infrastructure, your local files will still remain,
    you can use 'nebari deploy' to re-install infrastructure using same config file\n"""
    )
    with timer(logger, "destroying Nebari"):
        status = destroy_stages(config)

    for stage_name, success in status.items():
        if not success:
            logger.error(f"Stage={stage_name} failed to fully destroy")

    if not all(status.values()):
        logger.error(
            "ERROR: not all nebari stages were destroyed properly. For cloud deployments of Nebari typically only stages 01 and 02 need to succeed to properly destroy everything"
        )
    else:
        print("Nebari properly destroyed all resources without error")
