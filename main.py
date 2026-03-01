"""
This SNMP poller will load a yaml config file to figure out target SNMP agents and the OIDs to get from them.
It is a CLI tool. The easiest way to run it with default configuration file is use run.sh
"""

from enum import Enum
from pathlib import Path
from typing import Any

import argparse, sys, yaml, logging, datetime


class Status(Enum):
    OK = 0
    PARTIAL_SUCCESS = 1     # some data but not all
    FAILED = 2             # no data or invalid config


logger = logging.getLogger(__name__)


def main():
    """
    Runs the program by parsing arguments, loading the yaml, and then starting the poller
    """

    # Reading CLI arguments, set up logging and validate arguments
    args = parseArgs()
    setUpLogging(args.log_level)
    logger.info(msg='SNMP poller starting')
    config_string, output_filepath = validateArgs(args)

    # Validate config yaml
    config = parseYaml(config_string)
    validateYaml(config)

    # Merge defaults with targets


    # build snmpget commands


    # run snmpget commands


    # output json

    
    logger.info('SNMP poller closing')
    #sys.exit(Status.OK.value)   <---- should depend on if any target only returned partial data or if all were fully successful


def setUpLogging(log_level: str):
    """
    Sets up logging to file (all log levels) and stdout to the specified log level
    """
    logger.setLevel(logging.DEBUG)

    logger.handlers.clear()

    fmt = logging.Formatter(fmt='%(asctime)s : %(levelname)s : %(message)s', datefmt='%Y-%m-%d %I:%M:%S')

    file_handler = logging.FileHandler('logs/snmp_poller.log')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(fmt)

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(log_level)
    stdout_handler.setFormatter(fmt)

    logger.addHandler(file_handler)
    logger.addHandler(stdout_handler)


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
    parser.add_argument("--log-level", choices=['INFO', 'WARNING', 'ERROR'], default='ERROR', help='specifices the log level for stdout')

    return parser.parse_args()


def validateArgs(args: argparse.Namespace) -> tuple[str, Path]:
    """
    Validates the args. Config needs to be a readable file and out has to be a write-able file if it exists.
    """
    
    # validating config file path and reading the file
    config_path = Path(args.config)
    try:
        config_string = config_path.read_text()
    except Exception as e:
        logger.error(msg='config file problem : ' + str(e))
        
        sys.exit(Status.FAILED.value)

    # validating that output path is a write-able file if it exists
    output_path = Path(args.out)

    if output_path.is_file():
        try:
            with output_path.open("a") as f:
                f.close()
        except OSError as e:
            logger.error(msg='output file problem : ' + str(e))
        
            sys.exit(Status.FAILED.value)
        except Exception as e:
            logger.error(msg='when validating output file path : ' + str(e))
        
            sys.exit(Status.FAILED.value)

    return config_string, output_path


def parseYaml(yaml_string: str) -> Any:
    """
    Parses a string that is a yaml
    """

    try:
        data = yaml.safe_load(yaml_string)
    except yaml.YAMLError as e:
        logger.error(msg='yaml file problem : ' + str(e))
        
        sys.exit(Status.FAILED.value)

    return data


def validateYaml(yaml: Any):
    """
    Validates the yaml data to fulfill this programs needs
    """

    '''
    Write test_config.py that tests config parsing/validation without SNMP calls. Pick one test:
        • Missing targets key must raise a validation error.
        • Target missing ip must be rejected.
        • Non-numeric timeout_s must be rejected.
    '''
    pass


if __name__ == '__main__':
    main()