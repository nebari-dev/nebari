import os
import sys
from pathlib import Path

import jinja2


def main(template_path):
    loader = jinja2.FileSystemLoader(searchpath=template_path.parent)
    env = jinja2.Environment(loader=loader)
    template = env.get_template(template_path.name)
    print(template.render(env=os.environ))


if __name__ == "__main__":
    template_path = Path(sys.argv[1])
    main(template_path)
