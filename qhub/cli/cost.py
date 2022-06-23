import logging

from qhub.cost import infracost_report

logger = logging.getLogger(__name__)


def create_cost_subcommand(subparser):
    subparser = subparser.add_parser("cost-estimate")
    subparser.add_argument(
        "-p",
        "--path",
        help="Pass the path of your stages directory generated after rendering QHub configurations before deployment",
        required=False,
    )
    subparser.set_defaults(func=handle_cost_report)


def handle_cost_report(args):
    infracost_report(args.path)
