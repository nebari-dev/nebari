

def create_support_subcommand(subparser):
    subparser = subparser.add_parser("support")


    subparser.set_defaults(func=handle_support)


def handle_support(args):
    pass