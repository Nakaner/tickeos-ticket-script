import base64
import io
import os
import os.path

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


    def get_sand_save_ticket(self, soap_client, png_directory, **kwargs):
        params = kwargs
        params["output_format"] = "PNG"
        params["passengerSurname"] = self.last_name
        params["passengerName"] = self.first_name
        params["eventDate"] = kwargs["start_date"]
        params["eventDateUntil"] = kwargs["end_date"]
        params["authToken"] = kwargs["auth_token"]
        params["ticketID"] = self.ticket_id
        #TODO implement retrieval
        soap_client.generate(**params)
        png_data = base64.b64decode(soap_client.ticketData)
        self.internalTicketId = soap_client.internalTicketId
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
