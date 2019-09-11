#! /usr/bin/env python3

import argparse
import configparser
import csv
import jinja2
import logging
import os.path
import re
import requests
import sys
import zeep
from tickeos_ticket_tool.ticket import Ticket
from tickeos_ticket_tool.reader import OSMFReader, HOTReader

def setup_soap(**kwargs):
    session = requests.Session()
    session.auth = requests.auth.HTTPBasicAuth(kwargs["username"], kwargs["password"])
    session.verify = False
    sys.stderr.write("using username {}\n".format(kwargs["username"]))
    session.headers = {"user-agent": "state-of-the-map-tickeos-ticket-tool/0.1"}
    #session.max_redirects = 0
    transport = zeep.Transport(session=session)
    return zeep.Client(kwargs["wsdl_url"], None, transport)

def escape_tex(value, linebreaks=False):
    """Define Jinja2 Environment with LaTeX escaping"""
    latex_subs = [
        (re.compile(r'\\'), r'\\textbackslash'),
        (re.compile(r'([{}_#%&$])'), r'\\\1'),
        (re.compile(r'~'), r'\~{}'),
        (re.compile(r'\^'), r'\^{}'),
        (re.compile(r'"'), r"''"),
    ]
    if linebreaks:
        latex_subs.append((re.compile(r'\n'), r'\\\\'))

    result = str(value)
    for pattern, replacement in latex_subs:
        result = pattern.sub(replacement, result)
    return result

parser = argparse.ArgumentParser(description="Retrieve combotickets from the TICKeos API")
parser.add_argument("-c", "--config", type=argparse.FileType("r"), help="configuration file path", required=True)
parser.add_argument("-i", "--input-type", type=str, help="input file structure ('hot' or 'osmf')", required=True)
parser.add_argument("input_file", type=argparse.FileType("r"), help="input CSV file")
parser.add_argument("output_directory", type=str, help="path to output directory")
parser.add_argument("csv_output_file", type=argparse.FileType("w"), help="output CSV file for email script")
args = parser.parse_args()

logging.basicConfig(level=logging.DEBUG)

config = configparser.ConfigParser()
config.read_file(args.config)

reader = None
if args.input_type == "hot":
    reader = HOTReader(args.input_file)
elif args.input_type == "osmf":
    reader = OSMFReader(args.input_file)
if not reader:
    sys.stderr.write("Input type {} not supported.\n".format(args.input_type))
    exit(1)

ticket_orders = reader.get_orders()
api_params = {
    "authToken": config["tickeos"]["authToken"],
    "systemId": config["tickeos"]["systemID"],
    "organiserId": config["tickeos"]["organizerID"],
    "eventId": config["tickeos"]["eventID"],
    # date format: 2002-10-10T12:00:00+02:00
    "startDate": config["tickeos"]["startDate"],
    "endDate": config["tickeos"]["endDate"]
}
sys.stderr.write("retrieving tickets\n")
templates_directory = os.path.dirname(os.path.abspath(config["output"]["template"]))
sys.stderr.write("using template directory {}\n".format(templates_directory))
env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(templates_directory),
    #autoescape=False,
    block_start_string='((%',
    block_end_string='%))',
    variable_start_string='(((',
    variable_end_string=')))',
    comment_start_string='((#',
    comment_end_string='#))',
    undefined=jinja2.StrictUndefined
)
env.filters['e'] = escape_tex
tex_template = os.path.basename(config["output"]["template"])
template = env.get_template(tex_template)
png_directory = config["temp"]["png_directory"]
soap_client = setup_soap(**(config["tickeos"]))
out_writer = csv.DictWriter(args.csv_output_file, fieldnames=["first_name", "last_name", "email", "attachment", "internalTicketId"], delimiter=";", extrasaction="ignore")
for t in ticket_orders:
    t.get_and_save_ticket(soap_client, png_directory, **config)
    t.render_template(png_directory, env, template, args.output_directory)
    out_writer.writerow(t.dict_for_csv())
