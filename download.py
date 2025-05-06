#!/bin/env python
import sys
import argparse
from aau_ubiss import aau_ubiss

if __name__ == "__main__":
	parser = argparse.ArgumentParser(prog="AAU Ubiss Downloader")
	parser.add_argument("--group", metavar="<id>", type=str,
					 	help="Group id for which to download datafile" \
						" (default: \"group\")",
						default="group")
	parser.add_argument("--server", metavar="<ip>", type=str,
					 	help="Server IP (default: \"172.20.0.22\")",
						default="172.20.0.22")
	parser.add_argument("--localhost", metavar="", type=bool,
					 	help="Use if running locally on RPI",
						default=False)

	args = parser.parse_args()

	if len(sys.argv) == 1:
		parser.print_help()
		exit()

	ubiss = aau_ubiss(args.server, args.group)
	if args.localhost:
		ubiss.download(True)
	else:
		ubiss.download()
