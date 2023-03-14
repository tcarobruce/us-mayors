us-mayors
=========

Download and parse data about mayors of cities in the United States.


# Data Source
[US Conference of Mayors (Meet the Mayor)[https://www.usmayors.org/mayors/meet-the-mayors/]
- Type in state name to get list of mayor in the state.

# Steps to Run
Example to run all states to output.csv
```
python mayors.py --format csv output.csv
```

Example with Alaska and Colorado in csv format to file called output.csv
```
python mayors.py --state AK CO --format csv output.csv
```

requirements
------------
 * cssselect
 * lxml
 * requests
