"""CLI for tidy_nb."""
from __future__ import annotations

import argparse
from typing import TYPE_CHECKING

from . import __doc__ as pkg_description
from . import __version__

if TYPE_CHECKING:
    from typing import Sequence


PROG = __package__

def main(argv: Sequence[str] | None = None) -> int:
    """Main entry point for the tidy_nb CLI."""

    parser = argparse.ArgumentParser(prog=PROG, description=pkg_description)
    parser.add_argument('notebooks', nargs='*', help='Notebooks to tidy.')  
    parser.add_argument(
        '--version',
        action='version',
        version=f'%(prog)s {__version__}',
        help='Show the version and exit.',
    )

    args = parser.parse_args(argv)


    nb_processed = None

    for nb in args.notebooks:
        print(f'Tidying notebook: {nb}')

    if nb_processed:
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())