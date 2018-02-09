#!/usr/bin/env python

"""
mayors.py - scrape information about US Mayors from usmayors.org
"""

import argparse
import csv
import json
from datetime import datetime
from os.path import splitext

import requests
from lxml import html

ALL_STATES = """
    AL AK AZ AR CA CO CT DC DE FL GA GU HI ID IL IN IA KS KY LA ME MD MA MI
    MN MO MP MS MT NE NV NH NJ NM NY NC ND OH OK OR PA PR RI SC SD TN TX UT
    VT VA WA WV WI WY""".split()

BASE_URL = "http://legacy.usmayors.org/"
SEARCH_URL = "http://legacy.usmayors.org/meetmayors/mayorsatglance.asp"

FIELD_MAP = {
    "next mayoral election": "next_election",
    "mayor's e-mail address": "email",
    "city's web site": "city_site_url",
}

CSV_FIELDS = '''
    name email phone bio_url img_url city state population
    city_site_url next_election'''.split()


def get_mayors_for_state(state):
    payload = {'mode': 'search_db', 'State': state}
    response = requests.post(SEARCH_URL, data=payload)
    response.raise_for_status()
    root = html.fromstring(response.content)

    for node in root.cssselect('table.pagesSectionBodyTightBorder'):
        try:
            yield _get_mayor_from_table(node)
        except Exception:
            print("ERROR doing {}".format(state))
            import traceback
            traceback.print_exc()
            continue


def _get_mayor_from_table(table):
    mayor_data = {}
    main_row = table.getchildren()[0]
    first_cell = main_row.getchildren()[0]

    name_and_city_state = first_cell.cssselect('strong')[0]
    [name, city_state] = name_and_city_state.xpath('text()')
    mayor_data['name'] = name
    [city, state] = city_state.split(', ')
    mayor_data['city'] = city
    mayor_data['state'] = state

    bio_url = first_cell.cssselect('a')
    if bio_url:
        mayor_data['bio_url'] = bio_url[0].attrib['href']

    for data_cell in first_cell.cssselect('table tr td'):
        key, value = data_cell.text_content().split(':', 1)
        key = key.strip().lower()
        key = FIELD_MAP.get(key, key)
        mayor_data[key] = value.strip()

    mayor_data['population'] = mayor_data.get('population', '').replace(',', '')

    mayor_data['email'] = mayor_data.get('email', '').replace('mailto:', '')

    next_election = mayor_data.get('next_election')
    if next_election:
        try:
            parsed_next_election = datetime.strptime(next_election, "%m/%d/%Y")
            mayor_data['next_election'] = parsed_next_election.strftime("%Y-%m-%d")
        except ValueError:
            pass

    img_path = main_row.getchildren()[2].cssselect('img')[0].attrib['src']
    mayor_data['img_url'] = BASE_URL + img_path.lstrip('/')

    return mayor_data


def get_mayors(states=ALL_STATES):
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
    parser.add_argument('--state', nargs='*', default=ALL_STATES)

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
