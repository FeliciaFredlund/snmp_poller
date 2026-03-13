# SNMP Poller
An ops grade, small scale, SNMP poller made as part of a university course.

## About the Application
SNMP poller does a single polling of the targets and OIDs specified in the configuration yaml. It needs to be manually run (or added as a cron job). Only SNMPv2c is supported.

It saves all logging (whether printed to stdout or not) in a log file in the logs directory (currently not configurable).

A couple of example config yamls are available in the config directory.

## Installation
Required: Linux, snmpget command installed (apt package: snmp), python3, and venv installed.

Set up venv:
```
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:
```
pip install --upgrade pip
pip install -r requirements.txt
```

## Running
Run the application with `python3 main.py --config "path to your config file"`. There are additional options described below. Alternatively you can update `run.sh` and add execution permission to easily run the program.

Options:
* **--config (required):** path to the yaml configuration file
* **--out:** path to file to save output, if not specified output is instead printed to stdout
* **--log-level:** specifies log level for stdout. Options are INFO, WARNING, and ERROR. Defaults to ERROR if not specified.

Run example:
```
python3 main.py --config "configs/example_config.yaml" --out "output/out.json" --log-level INFO
```

## Future Improvements
Since there were time constraints for the assignment. Here are some things I noticed could be improved in the future:

* Add support for SNMPv3.
* Currently most functions are dependent on having access to the logger, Status enum and a few other things. Breaking out the code into multiple files as the project grew larger would require some rewriting to make it less spaghetti.
* Write a short helper function for the validateYaml function to reduce repeated code.
* Should the program error out if a single target is missing OIDs? Currently the answer in the code is yes, but I'm not sure that's the right option
* I tried using strict typing with pylance in vscode and yet didn't fully commit to typing. Question is how far typing is useful in Python and if the code is littered with "# type:ignore" is typing even worth it?
* Make logging path configurable.
* Only the validateYaml function has logging messages that isn't handled as logging within the function itself. It returns its logging messages. This felt like the best way so I could support unit testing for this one function. Should most functions be written this way if possible? Perhaps. But it is an outlier that does things differently than the rest of the code and either the rest of the code should be rewritten the same way or this function should be changed.
* Build out a more full featured testing suite to make sure the program actually works as intended even as code gets updated.

## Files

### Main directory:
* main.py: the code base
* test_config.py: unit tests for testing validateYaml function in main.py
* README.md: info about the program
* .gitignore: stops directory/files from being committed to git
* requirements.txt: used with pip to install the necessary libraries outside Python's standard library
* run.sh: used to easily run the program with a standard command
* test.sh: runs all unit tests

### configs directory:
* config.yaml: config with real examples used for demonstration to uni teacher
* example_config.yaml: simple example yaml to build a config yaml from

## Functions

What each function does and what the parameters and return values are can be found in the code.

In general all functions are written to be independent of each other with one big exception. This was done to have more modularity and to make further development of this program easier. The one exception is logging. Almost all functions need the setUpLogging function and the global logger variable. The only exceptions are: parseArgs, validateYaml, buildSnmpCommands, and filterSnmpOutput; they do no logging (validateYaml returns messages to be logged).

Outside that, several functions are meant to be chained so the output from one is used for the input of another function, however as long as each function gets the input they expect, they aren't directly dependent on the function that outputs that kind of data.

The obvious exception to all this is main, which depends on all functions, but that is kind of its job. If a function wasn't in some way used by main, then it probably shouldn't be in the code base.

The other dependency for several functions is the Status enum which is used by several functions.