import codecs
import csv
from .ticket import Ticket

class OrdersReader:
    def __init__(self, input_file):
        self.input_file = input_file

    def get_orders(self):
        """Get all orders in the input file."""
        pass


class HOTReader(OrdersReader):
    def __init__(self, input_file):
        super(HOTReader, self).__init__(input_file)

    def get_orders(self):
        orders = []
        with codecs.open(self.input_file, "r", "iso-8859-1") as f:
            reader = csv.DictReader(f, delimiter=";")
            for row in reader:
                orders.append(Ticket(**(self._normalise(row))))
        return orders

    def _normalise(self, row):
        entry = {}
        entry["first_name"] = row["First Name"].strip()
        entry["last_name"] = row["Last Name"].strip()
        entry["id"] = row["Order #"]
        entry["ticket_type"] = row["Ticket Type"]
        entry["price"] = float(row["Total Paid"])
        entry["email"] = row["Email"].strip()
        return entry


class OSMFReader(OrdersReader):
    prices = {
        ("Community", "Standard Price"): 120,
        ("Community", "Early Bird"): 75,
        ("Regular (Business)", "Standard Price"): 280,
        ("Regular (Business)", "Early Bird"): 180,
        ("Supporter (Business)", "Standard Price"): 700
    }

    def __init__(self, input_file):
        super(OSMFReader, self).__init__(input_file)

    def get_orders(self):
        orders = []
        with codecs.open(self.input_file, "r", "utf-8") as f:
            reader = csv.DictReader(f, delimiter=",")
            for row in reader:
                orders.append(Ticket(**(self._normalise(row))))
        return orders

    def _parse_fee_level(self, level):
        parts = level.split(" - ")
        if len(parts) == 1:
            return parts[0], 0
        ticket_type = parts[0]
        early_bird = parts[1]
        price = 0
        if "Includes applied discount code" in early_bird:
            eb_parts = early_bird.split(" (")
            if "_banktr_" in eb_parts[1]:
                price = self.prices[(ticket_type, eb_parts[0])]
            elif "_sponsor_" in eb_parts[1].lower():
                price = 0
            elif "_Volunteer" in eb_parts[1]:
                price = 0
            elif "_Dorothea" in eb_parts[1]:
                price = 0
            elif "_Scholar" in eb_parts[1]:
                price = 0
            elif "_keynote" in eb_parts[1]:
                price = 0
            elif "_LocalTeam" in eb_parts[1]:
                price = 0
            elif "SotM2019_discount_a4wsD2w" in eb_parts[1]:
                price = 45
            elif "_YouthMapper" in eb_parts[1]:
                price = 0
            elif "_Ministry_of_Transport" in eb_parts[1]:
                price = 0
            elif "_OsmAND" in eb_parts[1]:
                price = 0
            else:
                raise Exception("Unknown voucher type: {}".format(level))
            ticket_name = "{} {}".format(ticket_type, eb_parts[0])
        else:
            price = self.prices[(ticket_type, early_bird)]
            ticket_name = "{} {}".format(ticket_type, early_bird)
        return ticket_name, price


    def _normalise(self, row):
        entry = {}
        #TODO split name
        entry["first_name"] = row["First Name"].strip()
        middle_name = row.get("Middle Name", "").strip()
        if middle_name:
            entry["first_name"] += " {}".format(middle_name)
        entry["last_name"] = row["Last Name"].strip()
        entry["id"] = row["ID"]
        entry["ticket_type"], entry["price"] = self._parse_fee_level(row["Fee level"])
        entry["email"] = row["Email"].strip()
        return entry
