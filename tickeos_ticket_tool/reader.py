import codecs
import csv
import logging
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
        self.id_set = set()

    def get_orders(self):
        orders = []
        with codecs.open(self.input_file, "r", "utf-8") as f:
            reader = csv.DictReader(f, delimiter=",")
            for row in reader:
                t = Ticket(**(self._normalise(row)))
                if t.ticket_type != "Donation":
                    orders.append(t)
        return orders

    def _normalise(self, row):
        entry = {}
        entry["first_name"] = row["First Name"].strip()
        entry["last_name"] = row["Last Name"].strip()
        # Ugly hack because the Eventbrite export has order IDs, not ticket IDs.
        order_id = row["Order #"]
        if order_id in self.id_set:
            i = 1
            for i in range(1, 11):
                if i == 10:
                    logging.fatal("More than 10 tickets for order {}, aborting.".format(order_id))
                    exit(1)
                new_order_id = "{}-{}".format(order_id, i)
                if new_order_id not in self.id_set:
                    order_id = new_order_id
                    break
        entry["id"] = order_id
        self.id_set.add(order_id)
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
                price = 75
            elif "_YouthMapper" in eb_parts[1]:
                price = 0
            elif "_Ministry_of_Transport" in eb_parts[1]:
                price = 0
            elif "_OsmAND" in eb_parts[1]:
                price = 0
            elif "nas_cww" in eb_parts[1]:
                price = 120
                eb_parts[0] = "Standard Price"
            elif "_wire_4mg3" in eb_parts[1]:
                price = 180
                eb_parts[0] = "Early Bird"
            else:
                raise Exception("Unknown voucher type: {}".format(level))
            ticket_name = "{} {}".format(ticket_type, eb_parts[0])
        else:
            price = self.prices[(ticket_type, early_bird)]
            ticket_name = "{} {}".format(ticket_type, early_bird)
        return ticket_name, price


    def _normalise_name(self, name):
        """Make the first character uppercase."""
        if not name or len(name) < 2:
            return name
        if name[0].lower() == name[0]:
            return name[0].upper() + name[1:]
        return name


    def _normalise(self, row):
        entry = {}
        entry["first_name"] = self._normalise_name(row["First Name"].strip())
        middle_name = self._normalise_name(row.get("Middle Name", "").strip())
        if middle_name:
            entry["first_name"] += " {}".format(middle_name)
        entry["last_name"] = self._normalise_name(row["Last Name"].strip())
        entry["id"] = row["ID"]
        entry["ticket_type"], entry["price"] = self._parse_fee_level(row["Fee level"])
        entry["email"] = row["Email"].strip()
        return entry
