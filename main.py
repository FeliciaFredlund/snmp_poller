"""
This SNMP poller will load a yaml config file to figure out target SNMP agents and the OIDs to get from them.
It is a CLI tool. The easiest way to run it with default configuration file is use run.sh
"""

from enum import Enum
from pathlib import Path
from typing import Any

import argparse, sys, yaml, logging, ipaddress


class Status(Enum):
    OK = 0
    PARTIAL_SUCCESS = 1     # some data but not all
    FAILED = 2             # no data or invalid config


logger = logging.getLogger()


def main():
    """
    Runs the program by parsing arguments, loading the yaml, and then starting the poller. OBS: only SNMPv2c is supported currently
    """

    # Reading CLI arguments, set up logging and validate arguments
    args = parseArgs()
    setUpLogging(args.log_level)
    logger.info(msg='SNMP poller starting')
    config_string, output_filepath = validateArgs(args)

    # Validate config yaml
    config = parseYaml(config_string)
    valid, error = validateYaml(config)
    if not valid:
        logger.error(msg=error)
        sys.exit(Status.FAILED.value)

    # Merge defaults with targets


    # build snmpget commands


    # run snmpget commands


    # output json
    if str(output_filepath) == "-":
        print("OUTPUT PRINT OF JSON")
    else:
        print("save the data to file")
    
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
    Returns a tuple with the config yaml as a string and a Path object to the output file.
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
    Parses a string that is a yaml. Returns the python object that represents the yaml.
    """

    try:
        data = yaml.safe_load(yaml_string)
    except yaml.YAMLError as e:
        logger.error(msg='yaml file problem : ' + str(e))
        
        sys.exit(Status.FAILED.value)

    return data


def validateYaml(yaml: Any) -> tuple[bool, str]:
    """
    Validates the yaml data to fulfill this programs needs.
    Returns a bool telling if validation was valid or not, if not valid (aka false), the string holds the error.
    """
    see_example = ', see example_config.yaml or README.md for correct yaml'

    if not isinstance(yaml, dict):
        return False, 'config needs to convert to a dictionary' + see_example
    
    # checking defaults
    if 'defaults' not in yaml:
        return False, 'config needs defaults' + see_example
    
    defaults = yaml.get('defaults')     # type: ignore
    if not isinstance(defaults, dict):
        return False, 'defaults needs to convert to a dictionary' + see_example
    if 'snmp_version' not in defaults or not isinstance(defaults['snmp_version'], str):
        return False, 'defaults needs snmp_version that converts to a string' + see_example
    if 'timeout_s' not in defaults or not isinstance(defaults['timeout_s'], (int, float)):
        return False, 'defaults needs timeout_s that converts to a number' + see_example
    if 'retries' not in defaults or not isinstance(defaults['retries'], int):
        return False, 'defaults needs retries that converts to an integer' + see_example
    if 'target_budget_s' not in defaults or not isinstance(defaults['target_budget_s'], (int, float)):
        return False, 'defaults needs target_budget_s that converts to a number' + see_example

    # if oids key doesn't exist, oids will be None
    # no oids is fine    
    oids = defaults.get('oids')     # type: ignore
    if oids is not None:
        if not isinstance(oids, list):
            return False, 'oids needs to be a list' + see_example
        
        for oid in oids:            # type: ignore
            if not isinstance(oid, str):
                return False, 'every oid in defaults need to be a string' + see_example
    
    
    # checking targets
    if 'targets' not in yaml:
        return False, 'config needs targets' + see_example
    
    targets = yaml.get('targets')       # type: ignore
    if not isinstance(targets, list):
        return False, 'targets needs to convert to a list' + see_example

    for i, target in enumerate(targets):    # type: ignore
        target_number = i + 1

        if not isinstance(target, dict):
            return False, f'target number {target_number} needs to convert to a dictionary' + see_example

        if 'name' not in target or not isinstance(target['name'], str):
            return False, f'target number {target_number} needs a name that converts to a string' + see_example

        if 'ip' not in target:
            return False, f'target number {target_number} needs an ip' + see_example
        try:
            ipaddress.ip_address(target['ip'])      # type:ignore
        except (ValueError, TypeError):
            return False, f'target number {target_number} has an invalid IP address' + see_example

        # community is optional for v3
        if 'community' in target and not isinstance(target['community'], str):
            return False, f'target number {target_number} has a community that converts to a string' + see_example

        # if oids key doesn't exist, oids will be None
        # no oids is fine  
        oids = target.get('oids')       # type: ignore
        if oids is not None:
            if not isinstance(oids, list):
                return False, f"target number {target_number}'s oids needs to converts to a list" + see_example

            for oid in oids:        # type: ignore
                if not isinstance(oid, str):
                    return False, f"target number {target_number}'s oids need to be a string" + see_example

    return True, ""


def mergeDefaults(defaults: dict[str, Any], targets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Merges defaults with targets, where target values supersede defaults.
    Removes duplicate OIDs if they exist.
    Returns a list of merged targets.
    """
    '''
    merged_targets = []

    for target in targets:
        # Merge target into defaults
        merged = {**defaults, **target}

        # Merge 'oids' specifically, removing duplicates
        if 'oids' in defaults and 'oids' in target:
            merged['oids'] = list(set(defaults['oids'] + target['oids']))

        if merged['snmp_version'] == 'v2c' and 'community' not in target:
            # write error log and exit
        if not merged['oids']:
            # write error log and exit

        merged_targets.append(merged)

    # Now merged_targets is ready to use for SNMP commands
    '''

    return []

if __name__ == '__main__':
    main()