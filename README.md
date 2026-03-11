# SNMP Poller
An ops grade, small scale, SNMP poller made as part of a university course.

## About the Application
SNMP poller does a single polling of the targets and OIDs specified in the configuration yaml. It needs to be manually run (or added as a cron job). Only SNMPv2c is supported.

It saves all logging (whether printed to stdout or not) in a log file in the logs directory (currently not configurable).

A couple of example config yamls are available in the config directory.

## Installation
Required: Linux, python3 and venv installed.

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

* Add support for SNMPv3
* Currently most functions are dependent on having access to the logger, Status enum and a few other things. Breaking out the code into multiple files as the project grew larger would require some rewriting to make it less spaghetti
* Write a short helper function for the validateYaml function to reduce repeated code
* Should the program error out if a single target is missing OIDs? Currently the answer in the code is yes, but I'm not sure that's the right option
* I tried using strict typing with pylance in vscode and yet didn't fully commit to typing. Question is how far typing is useful in Python and if the code is littered with "# type:ignore" is typing even worth it?
* Make logging path configurable
* Build out a more full featured testing suite to make sure the program actually works as intended even as code gets updated


## Files

Beskriv vilka filer som ingår och vilken funktion de har.

## Methods

Beskriv vilka metoder som används: namn, input, output och vad metoden gör.

Beskriv även beroenden mellan metoderna.