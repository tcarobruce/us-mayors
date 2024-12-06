#!/usr/bin/env python

"""
mayors.py - scrape information about US Mayors from usmayors.org
"""

import argparse
import csv
import json
from datetime import datetime
from os.path import splitext, exists

import requests
from lxml import html

STATES = {
    "AK": "Alaska",
    "AL": "Alabama",
    "AR": "Arkansas",
    "AS": "American Samoa",
    "AZ": "Arizona",
    "CA": "California",
    "CO": "Colorado",
    "CT": "Connecticut",
    "DC": "District of Columbia",
    "DE": "Delaware",
    "FL": "Florida",
    "GA": "Georgia",
    "GU": "Guam",
    "HI": "Hawaii",
    "IA": "Iowa",
    "ID": "Idaho",
    "IL": "Illinois",
    "IN": "Indiana",
    "KS": "Kansas",
    "KY": "Kentucky",
    "LA": "Louisiana",
    "MA": "Massachusetts",
    "MD": "Maryland",
    "ME": "Maine",
    "MI": "Michigan",
    "MN": "Minnesota",
    "MO": "Missouri",
    "MP": "N. Mariana Islands",
    "MS": "Mississippi",
    "MT": "Montana",
    "NC": "North Carolina",
    "ND": "North Dakota",
    "NE": "Nebraska",
    "NH": "New Hampshire",
    "NJ": "New Jersey",
    "NM": "New Mexico",
    "NV": "Nevada",
    "NY": "New York",
    "OH": "Ohio",
    "OK": "Oklahoma",
    "OR": "Oregon",
    "PA": "Pennsylvania",
    "PR": "Puerto Rico",
    "RI": "Rhode Island",
    "SC": "South Carolina",
    "SD": "South Dakota",
    "TN": "Tennessee",
    "TX": "Texas",
    "UT": "Utah",
    "VA": "Virginia",
    "VI": "Virgin Islands",
    "VT": "Vermont",
    "WA": "Washington",
    "WI": "Wisconsin",
    "WV": "West Virginia",
    "WY": "Wyoming",
}
BASE_URL = "http://usmayors.org/"
SEARCH_URL = "https://www.usmayors.org/mayors/meet-the-mayors/"


CSV_FIELDS = '''
    name email phone bio_url img_url city state population
    city_site_url next_election'''.split()


def get_cached(state):
    state_name = STATES[state]
    payload = {'submit': 'Search', 'searchTerm': state_name}
    headers = {"User-Agent": "mayors-scraper/0.0.1"}
    ts = datetime.now().strftime("%Y%m%d")
    cache_file = f"_cache_{state.lower()}_{ts}.txt"
    if exists(cache_file):
        with open(cache_file) as f:
            text = f.read()
    else:
        response = requests.post(SEARCH_URL, data=payload, headers=headers)
        response.raise_for_status()
        text = response.content.decode('latin1')
        with open(cache_file, 'w') as f:
            f.write(text)

    return text


def get_mayors_for_state(state):

    root = html.fromstring(get_cached(state))

    for node in root.cssselect('div.post-content ul'):
        try:
            result = _get_mayor_from_table(node)
            if result and result["state"] == state:
                yield result
        except Exception:
            print("ERROR doing {}".format(state))
            import traceback
            traceback.print_exc()
            continue


def decode_email(encoded):
    prefix = "/cdn-cgi/l/email-protection#"
    if not encoded.startswith(prefix):
        return encoded
    encoded = encoded[len(prefix):]
    as_ints = [int(encoded[i:i+2], 16) for i in range(0, len(encoded), 2)]
    return "".join([chr(as_ints[0] ^ c) for c in as_ints[1:]])


def _get_mayor_from_table(node):
    # Text example:
    # 1 Ethan Berkowitz
    # 2 Anchorage, AK
    # 3 Population: 291,538
    # 4 Web Site
    # 5 Next Election Date: 04/06/2021
    # 6 Bio
    # 7 Phone:
    # 8 907-343-7100
    # 9 Email:
    # 10 mayor@muni.org
    bold = node.cssselect("b")[0]
    if bold is None or not bold.text or not bold.text.strip():
        # empty name, vacant or unknown
        return None

    mayor_data = {}
    text = (s.strip() for s in node.itertext() if s.strip())
    links = (a.attrib["href"] for a in node.cssselect("a"))

    mayor_data["img_url"] = node.cssselect("img")[0].attrib["src"]

    mayor_data["name"] = next(text)
    city_state = next(text)

    mayor_data["city"], mayor_data["state"] = city_state.split(", ")

    mayor_data["population"] = next(text).replace("Population: ", "").replace(",", "")

    mayor_data["city_site_url"] = next(links)
    next(text)  # skip "Web Site" text

    next_election = next(text).replace("Next Election Date: ", "")
    if next_election:
        try:
            parsed_next_election = datetime.strptime(next_election, "%m/%d/%Y")
            mayor_data["next_election"] = parsed_next_election.strftime("%Y-%m-%d")
        except ValueError:
            pass

    mayor_data["bio_url"] = next(links)

    mayor_data["phone"] = next(links).replace("tel:", "")
    mayor_data["email"] = decode_email(next(links).replace("mailto:", ""))

    return mayor_data


def get_mayors(states=STATES):
    for state in states:
        for mayor in get_mayors_for_state(state):
            yield mayor


def write_to_csv(mayors, out):
    w = csv.DictWriter(out, CSV_FIELDS)
    w.writeheader()
    for mayor in mayors:
        w.writerow(mayor)


def write_to_json(mayors, out):
    json.dump(list(mayors), out, indent=4)


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Scrape US mayoral data from usmayors.org")

    parser.add_argument('out', type=argparse.FileType('w', encoding="UTF-8"),
                        default='-')
    parser.add_argument('--format', choices=['csv', 'json'])
    parser.add_argument('--state', nargs='*', default=STATES.keys())

    args = parser.parse_args()

    # guess format from file extension
    if args.format is None:
        fn = args.out.name
        if fn != '<stdout>':
            _, ext = splitext(fn)
            args.format = ext[1:]
        else:
            args.format = 'csv'

    args.writer = {
        'csv': write_to_csv,
        'json': write_to_json,
    }[args.format]  # may KeyError if format is unrecognized

    return args


if __name__ == '__main__':
    args = parse_arguments()
    mayors = get_mayors(states=args.state)
    args.writer(mayors, args.out)
