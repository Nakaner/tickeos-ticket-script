import io
import logging
import os
import os.path
import subprocess
import sys

class Ticket:
    def __init__(self, **kwargs):
        self.first_name = kwargs.get("first_name")
        self.last_name = kwargs.get("last_name")
        self.ticket_type = kwargs.get("ticket_type")
        self.price = "{0:.2f}".format(kwargs.get("price"))
        self.shirt = kwargs.get("shirt")
        self.ticket_id = kwargs.get("id")
        self.email = kwargs.get("email")
        self.internal_ticket_id = kwargs.get("internal_ticket_id")

    def clean(self, filename):
        cleaned = ""
        for i in range(0, len(filename)):
            if filename[i] not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-":
                cleaned += "_"
            else:
                cleaned += filename[i]
        return cleaned


    def get_file_name(self, suffix):
        return "{}_{}.{}".format(self.clean(self.ticket_id), self.clean(self.email), suffix)


    def revoke(self, soap_client, **kwargs):
        config = kwargs["tickeos"]
        params = {"internalTicketID": self.internal_ticket_id}
        for key in ["authToken", "systemID"]:
            params[key] = config[key]
        alternative_address = config.get("alternative_address")
        soap_client = self._update_service_address(soap_client, alternative_address)
        service_proxy = soap_client.service
        response = service_proxy.revokeByInternalTicketID(**params)
        if response.returnCode == 0:
            logging.info("Ticket with internal ID {} successfully revoked".format(self.internal_ticket_id))
        else:
            logging.error("Ticket with internal ID {} could not be revoked. API said: {}".format(self.internal_ticket_id, response.returnValue))

    def _update_service_address(self, soap_client, alternative_address):
        s = soap_client.service
        if alternative_address:
            soap_client._default_service._binding_options["address"] = alternative_address
        return soap_client

    def get_and_save_ticket(self, soap_client, png_directory, re_request_only, **kwargs):
        config = kwargs["tickeos"]
        params = {
            "outputFormat": "PNG",
            "passengerSurname": self.last_name,
            "passengerName": self.first_name,
            "eventDate": config["startDate"],
            "eventDateUntil": config["endDate"]
        }
        for key in ["authToken", "systemID", "organizerID", "eventID"]:
            params[key] = config[key]
        params["ticketID"] = self.ticket_id
        # The development instance of the API does not contain the right addresses in the WSDL document.
        alternative_address = config.get("alternative_address")
        soap_client = self._update_service_address(soap_client, alternative_address)
        service_proxy = soap_client.service
        if not re_request_only:
            logging.info("requesting ticket for {} {} from the API".format(self.first_name, self.last_name))
            result = service_proxy.generate(**params)
            if result.returnCode == 405:
                logging.info("The ticket with ID {} for {} {} was already requested. Resending the generate request with the 'reRequest' parameter instead".format(self.ticket_id, self.first_name, self.last_name))
        else:
            logging.info("re-requesting ticket for {} {} from the API".format(self.first_name, self.last_name))
        if re_request_only or result.returnCode == 405:
            params["reRequest"] = True
            result = service_proxy.generate(**params)
        if result.returnCode != 0:
            sys.stderr.write("ERROR: API response not ok!\n{} {}\n".format(result.returnCode, result.returnValue))
            exit(1)
        png_data = result.ticketData
        self.internalTicketId = result.internalTicketID
        filename = self.get_file_name("png")
        output_filename = os.path.join(png_directory, filename)
        with open(output_filename, "wb") as pngfile:
            pngfile.write(png_data)

    def render_ticket_pdf(self, png_directory, env, template, output_directory, path_from_tex_to_png):
        png_path = os.path.join(path_from_tex_to_png, self.get_file_name("png"))
        tex_filename = self.get_file_name("tex")
        tex_path = os.path.join(output_directory, tex_filename)
        with open(tex_path, "w") as texfile:
            texfile.write(template.render(png_path=png_path, data=self))
        repl_stderrout = io.StringIO()
        args = ["lualatex", "--halt-on-error", tex_filename]
        args_for_log = "'{}'".format("' '".join(args))
        logging.info("running {}".format(args_for_log))
        proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=output_directory)
        output_buf = proc.communicate()
        if proc.returncode == 0:
            os.remove(tex_path)
            os.remove("{}.aux".format(os.path.splitext(tex_path)[0]))
            os.remove("{}.log".format(os.path.splitext(tex_path)[0]))
            return
        else:
            logging.critical("Failed subprocess for ticket {}: {}\n".format(self, args_for_log))
            sys.stderr.write(output_buf[0].decode("utf-8"))
            sys.stderr.write(output_buf[1].decode("utf-8"))
            exit(1)

    def dict_for_csv(self, output_directory):
        return {
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "attachment": os.path.join(output_directory, self.get_file_name("pdf")),
            "ticket_id": self.ticket_id,
            "internalTicketId": self.internalTicketId
        }

    def __repr__(self):
        return "{}".format(self.__dict__)
