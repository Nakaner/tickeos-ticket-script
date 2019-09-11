import base64
import io
import os
import os.path
import sys

class Ticket:
    def __init__(self, **kwargs):
        self.first_name = kwargs.get("first_name")
        self.last_name = kwargs.get("last_name")
        self.ticket_type = kwargs.get("ticket_type")
        self.price = kwargs.get("price")
        self.shirt = kwargs.get("shirt")
        self.ticket_id = kwargs.get("id")
        self.email = kwargs.get("email")
        self.internal_ticket_id = None

    def clean(self, filename):
        for i in range(0, len(filename)):
            if filename[i] not in "abcdefghijklmnopqrstuvwxyz@ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@_-":
                filename[i] = "_"
        return filename


    def get_file_name(self, suffix):
        return "{}_{}.{}".format(clean(self.ticket_id), clean(self.email), suffix)


    def get_and_save_ticket(self, soap_client, png_directory, **kwargs):
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
        s = soap_client.service
        if alternative_address:
            soap_client._default_service._binding_options["address"] = alternative_address
        service_proxy = soap_client.service
        result = service_proxy.generate(**params)
        if result.returnCode != 0:
            sys.stderr.write("ERROR: API response not ok!\n{} {}\n".format(result.returnCode, result.returnValue))
            exit(1)
        sys.stderr.write("{}\n".format(result))
        png_data = base64.b64decode(result.ticketData)
        self.internalTicketId = result.internalTicketId
        filename = self.get_file_name("png")
        output_filename = os.path.join(output_directory, filename)
        with open(output_filename, "wb") as pngfile:
            pngfile.write(png_data)

    def render_ticket_pdf(self, png_directory, env, template, output_directory):
        png_path = os.path.join(png_directory, get_file_name("png"))
        tex_path = os.path.join(output_directory, get_file_name("tex"))
        with open(tex_path, "w") as texfile:
            texfile.write(template.render(png_path=png_path, **self))
        repl_stderrout = io.StringIO()
        args = ["lualatex", "--halt-on-error", tex_path]
        sys.stderr.write("{}\n".format(args))
        result = subprocess.call(args, stdout=repl_stderrout, stderr=repl_stderrout)
        if result.returncode == 0:
            os.remove(tex_path)
            return
        else:
            sys.stderr.write("Failed subprocess for ticket {}: {}\n".format(self, args))
            sys.stderr.write(repl_stderrout.getvalue())
            exit(1)

    def dict_for_csv(self, output_directory):
        return {
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "attachment": os.path.join(output_directory, self.get_file_name("pdf")),
            "internalTicketId": self.internalTicketId
        }

    def __repr__(self):
        return "{}".format(self.__dict__)
