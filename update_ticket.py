#! /usr/bin/env python3

import argparse
import configparser
import jinja2
import logging
import os.path
import re
import requests
import sys
import zeep
import zeep.cache
from tickeos_ticket_tool.ticket import Ticket

def setup_soap(**kwargs):
    session = requests.Session()
    session.auth = requests.auth.HTTPBasicAuth(kwargs["username"], kwargs["password"])
    sys.stderr.write("using username {}\n".format(kwargs["username"]))
    session.headers = {"user-agent": "state-of-the-map-tickeos-ticket-tool/0.1"}
    transport = zeep.Transport(session=session, cache=zeep.cache.SqliteCache())
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

parser = argparse.ArgumentParser(description="Fetch a single, already existing ticket from the TICKeos API")
parser.add_argument("-a", "--action", type=str, required=True, help="action to do: update, revokeByInternalID, generate")
parser.add_argument("-c", "--config", type=argparse.FileType("r"), help="configuration file path", required=True)
parser.add_argument("-e", "--email", type=str, required=True, help="email address")
parser.add_argument("-f", "--first-name", type=str, required=True, help="first name")
parser.add_argument("-i", "--id", type=str, required=True, help="our ticket ID")
parser.add_argument("-I", "--internal-id", type=str, required=False, help="internal ticket ID of TICKeos")
parser.add_argument("-l", "--log-level", help="log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)", default="INFO", type=str)
parser.add_argument("-L", "--last-name", type=str, required=True, help="last name")
parser.add_argument("-p", "--price", type=float, required=True, help="price")
parser.add_argument("-t", "--ticket-type", type=str, required=True, help="ticket type")
parser.add_argument("png_directory", type=str, help="path to temporary PNG directory")
parser.add_argument("output_directory", type=str, help="path to output directory")
args = parser.parse_args()

# log level
numeric_log_level = getattr(logging, args.log_level.upper())
if not isinstance(numeric_log_level, int):
    raise ValueError("Invalid log level {}".format(args.log_level.upper()))
logging.basicConfig(level=numeric_log_level)

if args.action.startswith("revoke") and not args.internal_id:
    logging.fatal("Revoke request without internal ID. This has not been not implemented yet.")
    exit(1)
if args.action.startswith("generate") and args.internal_id:
    logging.fatal("Generate request with internal ID provided. Please note that the internal ID is assigned by the issuer of the public transport ticket!")
    exit(1)

config = configparser.ConfigParser()
config.read_file(args.config)

ticket_kwargs = {"first_name": args.first_name,
        "last_name": args.last_name,
        "ticket_type": args.ticket_type,
        "price": args.price,
        "email": args.email,
        "id": args.id,
        "internal_ticket_id": args.internal_id
}
ticket = Ticket(**ticket_kwargs)

api_params = {
    "authToken": config["tickeos"]["authToken"],
    "systemId": config["tickeos"]["systemID"],
    "organiserId": config["tickeos"]["organizerID"],
    "eventId": config["tickeos"]["eventID"],
    # date format: 2002-10-10T12:00:00+02:00
    "startDate": config["tickeos"]["startDate"],
    "endDate": config["tickeos"]["endDate"]
}
logging.info("Retrieving tickets")
templates_directory = os.path.dirname(os.path.abspath(config["output"]["template"]))
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
png_directory = args.png_directory 
soap_client = setup_soap(**(config["tickeos"]))
if args.action == "generate":
    ticket.get_and_save_ticket(soap_client, png_directory, False, **config)
    ticket.render_ticket_pdf(png_directory, env, template, args.output_directory, config["output"]["path_from_tex_to_png"])
elif args.action == "update":
    ticket.get_and_save_ticket(soap_client, png_directory, True, **config)
    ticket.render_ticket_pdf(png_directory, env, template, args.output_directory, config["output"]["path_from_tex_to_png"])
elif args.action == "revokeByInternalID":
    ticket.revoke(soap_client, **config)
