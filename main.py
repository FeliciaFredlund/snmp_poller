"""
This SNMP poller will load a yaml config file to figure out target SNMP agents and the OIDs to get from them.
It is a CLI tool. The easiest way to run it with default configuration file is use run.sh
"""
from enum import Enum
from pathlib import Path
import argparse

class ExitCode(Enum):
    SUCCESS = 0
    PARTIAL_SUCCESS = 1     # some data but not all
    FAILURE = 2             # no data or invalid config

class LogLevel(Enum):
    NONE = 0,
    INFO = 1,
    WARNING = 2,
    ERROR = 3

def main():
    """
    Runs the program by parsing arguments, loading the yaml, and then starting the poller
    """

    args = parseArgs()
    print(args)
    
    #config_file, output_file, log_level = validateArgs(args)

    #print(config_file, output_file, log_level)

    # SET UP LOGGING?!?!

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

def validateArgs(args: argparse.Namespace) -> str, Path, LogLevel:
    """
    Validates the args. Config needs to be an existing file; out if it exists need to be a writeable file; log-level need to parse to LogLevel enum.
    """
    
    pass

"""
    read_path = Path("input.txt")
    write_path = Path("output.txt")

    if not read_path.is_file():    OOOOOOORRRRR Path.read_text
        raise FileNotFoundError(read_path)

    if write_path.is_file():
        try:
            with write_path.open("a"):
                pass
        except OSError as e:
            raise PermissionError(write_path) from e


try:
    content = read_path.read_text()  # can raise FileNotFoundError, PermissionError, UnicodeDecodeError
    data = yaml.safe_load(content)   # can raise yaml.YAMLError for invalid YAML
except FileNotFoundError:
    print("File does not exist")
except PermissionError:
    print("Cannot read file")
except UnicodeDecodeError:
    print("File encoding is invalid")
except yaml.YAMLError as e:
    print("YAML parse error:", e)
"""

if __name__ == '__main__':
    main()