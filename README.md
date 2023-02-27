us-mayors
=========

Download and parse data about mayors of cities in the United States.

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
