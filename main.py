"""
This SNMP poller will load a yaml config file to figure out target SNMP agents and the OIDs to get from them.
It is a CLI tool. The easiest way to run it with default configuration file is use run.sh
"""

from enum import Enum
from pathlib import Path
from typing import Any
from datetime import date

import argparse, sys, yaml, logging, ipaddress, json


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
    targets = mergeDefaults(config['defaults'], config['targets'])

    data = []
    exit_code = Status.OK.value

    for target in targets:
        # build snmpget commands
        cmds = buildSnmpCommands(target)
        
        # run snmpget commands


    '''
      timeout_s: 2.5         # per request
      retries: 1             # retry only on timeouts
      target_budget_s: 10 



    snmpget -v2c -c public 192.168.1.10 1.3.6.1.2.1.1.3.0
    DISMAN-EVENT-MIB::sysUpTimeInstance = Timeticks: (123456789) 14 days, 6:56:07.89

    snmpget -v2c -c public 192.168.1.10 1.3.6.1.2.1.1.5.0
    SNMPv2-MIB::sysName.0 = STRING: router01

    snmpget -v2c -c public 192.168.1.10 1.3.6.1.2.1.2.2.1.8.1
    IF-MIB::ifOperStatus.1 = INTEGER: up(1)

    snmpget -v2c -c public 192.168.1.10 1.3.6.1.2.1.1.4.0
    SNMPv2-MIB::sysContact.0 = STRING: admin@example.com

    snmpget -v2c -c public 192.168.1.10 1.3.6.1.2.1.2.1.0
    IF-MIB::ifNumber.0 = INTEGER: 8

    line = "SNMPv2-MIB::sysName.0 = STRING: router01"

    # Split on '=' first
    _, value_part = line.split('=', 1)
    # value_part = " STRING: router01"

    # Split on ':' to separate type and value
    value_type, value = value_part.split(':', 1)
    value = value.strip()

    print(value_type.strip())  # "STRING"
    print(value)               # "router01"

    '''

    # output data as json
    output = json.dumps(data, indent=2)
    if str(output_filepath) == "-" or str(output_filepath) == ".":
        print('Output:')
        print(output)
    else:
        try:
            with output_filepath.open("w") as f:
                f.write(output)
        except Exception as e:
            logger.error(msg='writing to output file failed : ' + str(e))
            print('writing to stdout instead:')
            print(output)
    
    logger.info('SNMP poller closing\n')
    
    sys.exit(exit_code)


def setUpLogging(log_level: str):
    """
    Sets up logging to file (all log levels) and stdout to the specified log level
    """
    logger.setLevel(logging.DEBUG)

    logger.handlers.clear()

    fmt = logging.Formatter(fmt='%(asctime)s : %(levelname)s : %(message)s', datefmt='%Y-%m-%d %I:%M:%S')

    Path('logs').mkdir(exist_ok=True)
    file_handler = logging.FileHandler(f'logs/{date.today():%Y-%m-%d}_snmp_poller.log')
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
    parser.add_argument('--out', default="-", help='specifies the json file the output (data) is written to')
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
    
    merged_targets = []

    for target in targets:
        # Merge target into defaults
        merged = {**defaults, **target}

        # Target oids list overwrites defaults, but we want to combine them and remove duplicates
        if 'oids' in defaults and 'oids' in target:
            merged['oids'] = list(set(defaults['oids'] + target['oids']))

        if merged['snmp_version'] == 'v2c' and 'community' not in target:
            error = 'Target ' + merged['name'] + ' needs an SNMP community'
            logger.error(msg=error)
            sys.exit(Status.FAILED.value)
        if not merged['oids']:
            error = 'Target ' + merged['name'] + ' needs oids, none are in defaults'
            sys.exit(Status.FAILED.value)
        
        merged_targets.append(merged)           # type:ignore

    return merged_targets       # type:ignore


def buildSnmpCommands(target: dict[str, Any]) -> list[list[str]]:
    """
    Takes a target with their settings and builds all SNMP commands.
    Returns a list of all commands as strings.
    """

    cmds = []
    cmd_template = ['snmpget', '-' + target['snmp_version'], "-c", target['community'], target['ip']]       # type:ignore

    for oid in target['oids']:
        cmds.append(cmd_template + [oid])         # type:ignore

    return cmds     # type:ignore


if __name__ == '__main__':
    main()