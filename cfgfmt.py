#! /usr/bin/env python3

import sys
from configparser import ConfigParser
from argparse import ArgumentParser, FileType

parser = ArgumentParser()

parser.add_argument("file", type=FileType("r"), help="config file")
parser.add_argument("section", nargs="?", help="section of config file")
parser.add_argument("item", nargs="?", help="item to print")
parser.add_argument("--format", default="{key}={value}", help="format for printing")
parser.add_argument("--eol", help="end-of-line character")

if __name__ == "__main__":
    args = parser.parse_args()
    cfg = ConfigParser()
    cfg.read_file(args.file)
    if args.item:
        if not cfg.has_option(args.section, args.item):
            print("{section}/{item}: no such value".format(**vars(args)))
            sys.exit(1)
        print(cfg.get(args.section, args.item))
    elif args.section:
        section = dict(cfg.items(args.section))
        for key, value in section.items():
            print(args.format.format(key=key, value=value), end=args.eol)
        if args.eol is not None:
            print()
    else:
        for section in cfg.sections():
            print(section)
