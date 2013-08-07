#!/usr/bin/env python

"""
mayors.py - scrape information about US Mayors from usmayors.org
"""

import sys
from datetime import datetime
from lxml import html

error_message = "There are no cities or mayors with that last name"
base_domain = "http://usmayors.org"
base_template = "http://usmayors.org/database_searchID.asp?idnumber=%d" 

field_map = {
    "next general election": "next_election",
    "mayor's e-mail address": "email",
    "city's web site": "city_site_url",
}

def get_mayor(id, uri_template=base_template):
    url = uri_template % id 
    doc = html.parse(url)
    root = doc.getroot()

    try: 
        if error_message in root.text_content():
            return None
    except Exception, e:
        return None
    
    mayor_data = {'id': id}

    main_table = root.cssselect('table.pagesSectionBodyTightBorder')[0]
    main_row = main_table.getchildren()[0]
    first_cell = main_row.getchildren()[0]
    
    name_and_city_state = first_cell.cssselect('strong')[0]
    [name, city_state] = name_and_city_state.xpath('text()')
    mayor_data['name'] = name
    [city, state] = city_state.split(', ')
    mayor_data['city'] = city
    mayor_data['state'] = state

    bio_url = first_cell.cssselect('div a')
    if bio_url:
        mayor_data['bio_url'] = bio_url[0].attrib['href'] 

    for data_cell in first_cell.cssselect('table tr td'):
        key = data_cell.text.strip().replace(':','').lower()
        key = field_map.get(key, key)
        value_cell = data_cell.cssselect('b')
        if value_cell:
            val = value_cell[0].text_content().strip()
            mayor_data[key] = val

    mayor_data['population'] = mayor_data.get('population', '').replace(',', '')

    next_election = mayor_data.get('next_election')
    if next_election:
        parsed_next_election = datetime.strptime(next_election, "%m/%d/%Y") 
        mayor_data['next_election'] = parsed_next_election.strftime("%Y-%m-%d") 

    img_path = main_row.getchildren()[2].cssselect('img')[0].attrib['src']    
    mayor_data['img_url'] = base_domain + img_path

    for k, v in mayor_data.items():
        if hasattr(v, 'encode'):
            mayor_data[k] = v.encode('utf-8')

    return mayor_data

def all_mayors(ids=range(1,4000), uri_template=base_template):
    for i in ids:
        data = None
        try: 
            data = get_mayor(i, uri_template)
        except Exception, e:
            sys.stderr.write("Error on %d %s\n" % (i, str(e)))

        if data:
            yield data

def write_all_to_csv(out=None, ids=range(1,4000), uri_template=base_template):
    import csv 
    if out is None:
        out = sys.stdout
    
    fields = 'id,name,email,phone,bio_url,img_url,city,state,population,city_site_url,next_election'.split(',')

    w = csv.DictWriter(out, fields)
    for mayor in all_mayors(ids=ids, uri_template=uri_template):
        w.writerow(mayor)

def write_all_to_json(out=None, ids=range(1,4000), uri_template=base_template):
    import json 
    if out is None:
        out = sys.stdout
    mayors = []
    for mayor in all_mayors(ids=ids, uri_template=uri_template):
        mayors.append(mayor)
    json.dump(mayors, out, indent=4)

if __name__ == '__main__':
    write_all_to_csv()

