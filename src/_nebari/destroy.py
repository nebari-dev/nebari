import contextlib
import logging
import pathlib
from typing import List

from _nebari.utils import timer
from nebari import hookspecs, schema

logger = logging.getLogger(__name__)


def destroy_configuration(config: schema.Main, stages: List[hookspecs.NebariStage]):
    logger.info(
        """Removing all infrastructure, your local files will still remain,
    you can use 'nebari deploy' to re-install infrastructure using same config file\n"""
    )

    stage_outputs = {}
    status = {}

    with timer(logger, "destroying Nebari"):
        with contextlib.ExitStack() as stack:
            for stage in stages:
                try:
                    s: hookspecs.NebariStage = stage(
                        output_directory=pathlib.Path.cwd(), config=config
                    )
                    stack.enter_context(s.destroy(stage_outputs, status))
                except Exception as e:
                    status[s.name] = False
                    print(
                        f"ERROR: stage={s.name} failed due to {e}. Due to stages depending on each other we can only destroy stages that occur before this stage"
                    )
                    break

    for stage_name, success in status.items():
        if not success:
            logger.error(f"Stage={stage_name} failed to fully destroy")

    if not all(status.values()):
        logger.error(
            "ERROR: not all nebari stages were destroyed properly. For cloud deployments of Nebari typically only stages 01 and 02 need to succeed to properly destroy everything"
        )
    else:
        print("Nebari properly destroyed all resources without error")
