import ast
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
    subparser.add_argument(
        "-d",
        "--dashboard",
        default="True",
        help="Enable the cost dashboard",
        required=False,
    )
    subparser.add_argument(
        "-f",
        "--file",
        help="Specify the path of the file to store the cost report",
        required=False,
    )
    subparser.add_argument(
        "-c",
        "--currency",
        help="Specify the currency code to use in the cost report",
        required=False,
        default="USD",
    )
    subparser.add_argument(
        "-cc",
        "--compare",
        help="Compare the cost report to a previously generated report",
        required=False,
    )
    subparser.set_defaults(func=handle_cost_report)


def handle_cost_report(args):
    infracost_report(
        args.path,
        ast.literal_eval(args.dashboard),
        args.file,
        args.currency,
        args.compare,
    )
