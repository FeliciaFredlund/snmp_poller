"""
This SNMP poller will load a yaml config file to figure out target SNMP agents and the OIDs to get from them.
It is a CLI tool. The easiest way to run it with default configuration file is to use run.sh
"""

from enum import Enum
from pathlib import Path
from typing import Any
from datetime import date, datetime

import argparse, sys, yaml, logging, ipaddress, json, time, subprocess


class Status(Enum):
    OK = 0
    PARTIAL_SUCCESS = 1     # some data but not all
    FAILED = 2             # no data or invalid config


logger = logging.getLogger()


def main():
    """
    Runs the program step by step.
    """

    # Reading CLI arguments, set up logging and validate arguments
    args = parseArgs()
    setUpLogging(args.log_level)
    logger.info(msg='SNMP poller starting')
    config_string, output_path = validateArgs(args)
    output_channel = str(output_path)

    if str(output_path) == '-' or str(output_path) == '.':
        output_channel = 'stdout'

    # Validate config yaml
    config = parseYaml(config_string)
    valid, error = validateYaml(config)
    if not valid:
        logger.error(msg=error)
        sys.exit(Status.FAILED.value)

    targets = mergeDefaults(config['defaults'], config['targets'])

    # Polling
    message = 'Starting poll run: ' + str(len(targets)) + ' targets, output=' + str(output_channel)
    logger.info(msg=message)
    data = {}
    
    # counts the Status values of the polling of each target
    polling_status_value = 0
    
    data['meta_data'] = {                           # type:ignore
        'time_of_run': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'config_file': args.config
        }

    targets_data = []
    duration = 0.0
    for target in targets:
        result, status = pollTarget(target)

        polling_status_value += status.value

        duration += result['runtime']
        targets_data.append(result)                         # type:ignore

    data['meta_data']['duration'] = duration
    data['targets'] = targets_data

    # if polling_status_value is 0 it means all targets were polled successfully
    # else if it is more than 0 but less than double the number of targets, some polls were successfull
    # else if it is double the number of targets it means every target returned failure (value 2)
    exit_code = -1
    if polling_status_value == 0:
        exit_code = Status.OK.value
    elif polling_status_value < (len(targets) * 2):
        exit_code = Status.PARTIAL_SUCCESS.value
    else:
        exit_code = Status.FAILED.value

    message = 'Finished poll with status=' + Status(exit_code).name + ' in ' + '{:.1f}'.format(duration) + 's'
    logger.info(msg=message)

    # Outputing data as json
    output = json.dumps(data, indent=2)
    if output_channel == 'stdout':
        print('Output:')
        print(output)
    else:
        try:
            with output_path.open('w') as f:
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
    parser.add_argument('--out', default='-', help='specifies the json file the output (data) is written to')
    parser.add_argument('--log-level', choices=['INFO', 'WARNING', 'ERROR'], default='ERROR', help='specifices the log level for stdout')

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
            with output_path.open('a') as f:
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

    return True, ''


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


def pollTarget(target: dict[str, Any]) -> tuple[dict[str, Any], Status]:
    """
    Polls one target using the values in the target dictionary.
    Returns a tuple of a dictionary with the target data and a status reflecting how the pulling went
    """

    name = target['name']
    
    message = 'Polling target ' + name + ' (' + target['ip'] + ')'
    logger.info(msg=message)

    # Setting up target values

    data = {                            # type:ignore
        'name': name,
        'ip': target['ip'],
        'status': Status.OK.name,
        'runtime': 0.0,
        'successful_oids': 0,
        'failed_oids': 0
    }

    cmds = buildSnmpCommands(target)
        
    # polling
    start = time.monotonic()
    end_time = start + target['target_budget_s']        #if we hit end_time while running commands, then our time budget is used up
    remaining_oids = len(cmds)
    
    for command in cmds:
        current = time.monotonic()
        if current > end_time:
            message = 'Target ' + name + "'s time budget exceeded"
            logger.warning(msg=message)
            data['failed_oids'] += remaining_oids
            break
        
        # Run the SNMP command
        result, cmd_status = runSnmpCommand(command, target['timeout_s'], target['retries'])

        remaining_oids -= 1

        if cmd_status == Status.FAILED:
            data['failed_oids'] += 1
            message = 'Failure on ' + command[-1] + ', error=' + result
            logger.warning(msg=message)
            continue
        
        data['successful_oids'] += 1

        # Filter out the useful value from the SNMP command output
        value = filterSnmpOutput(result)
        data[command[-1]] = value

    status = Status.OK
    if data['successful_oids'] != len(cmds):
        status = Status.PARTIAL_SUCCESS
        if data['failed_oids'] == len(cmds):
            status = Status.FAILED

    data['runtime'] = time.monotonic() - start
    data['status'] = status.name

    message = 'Finished target ' + name + ' with status=' + status.name + ' in ' + '{:.1f}'.format(data['runtime']) + 's'
    logger.info(msg=message)

    return data, status                 # type:ignore


def buildSnmpCommands(target: dict[str, Any]) -> list[list[str]]:
    """
    Takes a target with their settings and builds all SNMP commands.
    Returns a list of all commands as strings.
    """

    cmds = []
    cmd_template = ['snmpget', '-' + target['snmp_version'], '-c', target['community'], target['ip']]       # type:ignore

    for oid in target['oids']:
        cmds.append(cmd_template + [oid])         # type:ignore

    return cmds     # type:ignore


def runSnmpCommand(command: list[str], timeout_s: float, retries: int) -> tuple[str, Status]:
    """
    Runs the SNMP command specified in the list via subprocess.
    Returns a string with the returned stdout/stderr from the command and a status for how it went.
    """

    remaining_retries = retries

    while remaining_retries >= 0:
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout_s
            )
            if result.returncode != 0:
                return result.stderr.strip(), Status.FAILED
            
            if 'no such instance' in result.stdout.lower():
                return result.stdout.strip(), Status.FAILED

            return result.stdout, Status.OK
        
        except subprocess.TimeoutExpired:
            if remaining_retries > 0:
                message = 'Timeout on ' + command[-1] + ', remaining retries=' + str(remaining_retries)
                logger.warning(msg=message)
            remaining_retries -= 1

        except Exception as e:
            return str(e), Status.FAILED

    return "out of retries", Status.FAILED


def filterSnmpOutput(output: str) -> str:
    """
    Filters out the value in SNMP output.
    Returns only the value
    """
    value_with_type = output.split("=", 1)[1]
    value = value_with_type.split(":", 1)[1].strip()

    return value


if __name__ == '__main__':
    main()