#!/usr/bin/env python3
"""Generate an agetty issue file for an explicitly selected assembly."""

import argparse
import re


def identity(value):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9 ._-]{0,79}", value):
        raise ValueError("identity must be short, printable ASCII without escapes")
    return value


def render(cultivar=None, version=None):
    if (cultivar is None) != (version is None):
        raise ValueError("cultivar and version must be supplied together")
    selected = "" if cultivar is None else f"     Cultivar:  {identity(cultivar)} {identity(version)}\n"
    tree = "       /\\\n      /\\/\\\n     ///\\\\\\       Welcome to Tamlinux!\n       ||\n"
    return (
        "\n" + tree.replace("\\", "\\\\") + "\n"
        + selected
        + "     Rootstock: \\S{PRETTY_NAME}\n"
        + "     Build:     \\S{BUILD_ID}\n"
        + "     Kernel:    \\r\n"
        + "     Console:   \\l\n\n"
        + "     After login, type hi for help or tam-desktop for the graphical desktop.\n\n"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cultivar")
    parser.add_argument("--version")
    args = parser.parse_args()
    try:
        print(render(args.cultivar, args.version), end="")
    except ValueError as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
