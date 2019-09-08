#! /usr/bin/env python3

import argparse
import configparser
import csv
import jinja2
import os.path
import re
import sys
#import zeep
from tickeos_ticket_tool.ticket import Ticket
from tickeos_ticket_tool.reader import OSMFReader, HOTReader

def setup_soap(wsdl_url):
    return zeep.Client(wsdl_url)

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
#api_params = {
#    "auth_token": config["tickeos"]["authToken"],
#    "system_id": config["tickeos"]["systemID"],
#    "organiser_id": config["tickeos"]["organizerID"],
#    "event_id": config["tickeos"]["eventID"],
#    # date format: 2002-10-10T12:00:00+02:00
#    "start_date": config["tickeos"]["startDate"],
#    "end_date": config["tickeos"]["endDate"]
#}
#sys.stderr.write("retrieving tickets\n")
#templates_directory = os.path.dirname(os.path.abspath(config["output"]["template"]))
#env = jinja2.Environment(
#    loader=jinja2.FileSystemLoader(templates_directory),
#    #autoescape=False,
#    block_start_string='((%',
#    block_end_string='%))',
#    variable_start_string='(((',
#    variable_end_string=')))',
#    comment_start_string='((#',
#    comment_end_string='#))',
#    undefined=jinja2.StrictUndefined
#)
#env.filters['e'] = escape_tex
#tex_template = os.path.basename(config["output"]["template"])
#template = env.get_template(tex_template)
#png_directory = config["temp"]["png_directory"]
#soap_client = setup_soap(config["tickeos"]["wsdl_url"]
#out_writer = csv.DictWriter(args.csv_output_file, fieldnames=["first_name", "last_name", "email", "attachment", "internalTicketId"], delimiter=";", extrasaction="ignore")
#for t in ticket_orders:
#    t.get_and_save_ticket(soap_client, png_directory, api_params)
#    t.render_template(png_directory, env, template, args.output_directory)
#    out_writer.writerow(t.dict_for_csv())
