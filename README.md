us-mayors
=========

Download and parse data about mayors of cities in the United States.

# Steps to Run

Example with Alaska and Colorado in csv format to file called output.csv
```
python mayors.py --state AK CO --format csv output.csv

requirements
------------
 * cssselect
 * lxml
 * requests
