"""CLI entry point for nrich."""

import argparse
import sys
from pathlib import Path

from nrich.pipeline import run_pipeline
from nrich.config import ConfigError
from nrich.io import find_latest_leads


def main() -> None:
    parser = argparse.ArgumentParser(
        description="nrich — Enrich ks-scout leads with contact information",
    )
    parser.add_argument(
        "--input", "-i",
        type=str,
        default=None,
        help="Path to leads YAML file (default: auto-discover latest in ks-scout/output/)",
    )
    parser.add_argument(
        "--version", "-V",
        action="store_true",
        help="Show version and exit",
    )

    args = parser.parse_args()

    if args.version:
        from nrich import __version__
        print(f"nrich v{__version__}")
        sys.exit(0)

    try:
        exit_code = run_pipeline(
            input_path=Path(args.input) if args.input else None,
        )
        sys.exit(exit_code)
    except ConfigError as e:
        print(f"❌ Configuration error: {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"❌ File error: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"❌ Data error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
