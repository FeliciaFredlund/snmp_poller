"""
This SNMP poller will load a yaml config file to figure out target SNMP agents and the OIDs to get from them.
It is a CLI tool. The easiest way to run it with default configuration file is use run.sh
"""

from enum import Enum
from pathlib import Path
import argparse, sys

class ExitCode(Enum):
    SUCCESS = 0
    PARTIAL_SUCCESS = 1     # some data but not all
    FAILURE = 2             # no data or invalid config

class LogLevel(Enum):
    NONE = 0
    INFO = 1
    WARNING = 2
    ERROR = 3

def main():
    """
    Runs the program by parsing arguments, loading the yaml, and then starting the poller
    """

    args = parseArgs()

    log_level = LogLevel[args.log_level]

    # Set up logging!!!!
    
    config_string, output_filepath = validateArgs(args)

    print(config_string, output_filepath, log_level)


def parseArgs() -> argparse.Namespace:
    """
    Sets up args and returns the parsed args
    """
    parser = argparse.ArgumentParser(
        prog='SNMP Poller',
        description='Gathers SNMP data from targets in specified config file.'
    )
    parser.add_argument('--config', required=True, help='specifies the configuration yaml file')
    parser.add_argument('--out', required=True, help='specifies the json file the output (data) is written to')
    parser.add_argument("--log-level", choices=['INFO', 'WARNING', 'ERROR'], default='NONE', help='specifices the log level for stdout')

    return parser.parse_args()

def validateArgs(args: argparse.Namespace) -> tuple[str, Path]:
    """
    Validates the args. Config needs to be an existing file; out if it exists need to be a writeable file; log-level need to parse to LogLevel enum.
    """
    
    # validating config file path and reading the file
    config_path = Path(args.config)
    try:
        config_string = config_path.read_text()
    except Exception as e:
        print("ERROR:", e)
        sys.exit(2)

    # validating that output path is a write-able file if it exists
    output_path = Path(args.out)

    if output_path.is_file():
        try:
            with output_path.open("a") as f:
                f.close()
        except OSError as e:
            print("ERROR: output file does not have write permission")
        except Exception as e:
            print("ERROR:", e)

    return config_string, output_path

"""
try:
    data = yaml.safe_load(content)   # can raise yaml.YAMLError for invalid YAML

except yaml.YAMLError as e:
    print("YAML parse error:", e)
"""

if __name__ == '__main__':
    main()