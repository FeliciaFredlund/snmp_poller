"""
This SNMP poller will load a yaml config file to figure out target SNMP agents and the OIDs to get from them.
It is a CLI tool. The easiest way to run it with default configuration file is use run.sh
"""
from enum import Enum
import argparse

class ExitCode(Enum):
    SUCCESS = 0
    PARTIAL_SUCCESS = 1     # some data but not all
    FAILURE = 2             # no data or invalid config

class LogLevel(Enum):
    INFO = 0,
    WARNING = 1,
    ERROR = 2

def main():
    """
    Runs the program by parsing arguments, loading the yaml, and then starting the poller
    """

    # Parsing command line arguments
    parser = argparse.ArgumentParser(
        prog='SNMP Poller',
        description='Gathers SNMP data from targets in specified config file.'
    )
    parser.add_argument('--config', required=True, help='specifies the configuration yaml file')
    parser.add_argument('--out', required=True, help='specifies the json file the output (data) is written to')
    parser.add_argument('--log-level', choices=['INFO', 'WARNING', 'ERROR'], required=False, help='specifices the log level for stdout')
    
    args = parser.parse_args()
    
    config_file = args.config
    output_file = args.out
    log_level = LogLevel[args.log_level]
    
    print(config_file, output_file, log_level)

if __name__ == '__main__':
    main()

'''
Typing example for Python:

def summarize(names: list[str], scores: dict[str, int], bonus: int) -> str:
    """
    Takes a list of names, a dictionary of scores, and an integer multiplier.
    Returns a formatted string summarizing the processed scores.
    """
    return "; ".join(f"{name}: {scores.get(name, 0) + bonus}" for name in names)

'''
