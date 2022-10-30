from datetime import datetime

import requests

from ..const.const import _LOGGER, SENSOR_COLLECTORS_OPZET


class OpzetCollector(object):
    def __init__(
        self,
        provider,
        postal_code,
        street_number,
        suffix,
        exclude_pickup_today,
        exclude_list,
        default_label,
    ):
        self.provider = provider
        self.postal_code = postal_code
        self.street_number = street_number
        self.suffix = suffix
        self.exclude_pickup_today = exclude_pickup_today
        self.exclude_list = exclude_list.strip().lower()
        self.default_label = default_label

        if self.provider not in SENSOR_COLLECTORS_OPZET.keys():
            raise ValueError(f"Invalid provider: {self.provider}, please verify")

        self._get_waste_data_provider()

    def __waste_type_rename(self, item_name):
        if item_name == "snoeiafval":
            item_name = "takken"
        if item_name == "sloop":
            item_name = "grofvuil"
        if item_name == "glas":
            item_name = "glas"
        if item_name == "duobak":
            item_name = "duobak"
        if item_name == "groente":
            item_name = "gft"
        if item_name == "groente-, fruit en tuinafval":
            item_name = "gft"
        if item_name == "groente, fruit- en tuinafval":
            item_name = "gft"
        if item_name == "gft":
            item_name = "gft"
        if item_name == "chemisch":
            item_name = "chemisch"
        if item_name == "kca":
            item_name = "chemisch"
        if item_name == "tariefzak restafval":
            item_name = "restafvalzakken"
        if item_name == "restafvalzakken":
            item_name = "restafvalzakken"
        if item_name == "rest":
            item_name = "restafval"
        if item_name == "plastic":
            item_name = "plastic"
        if item_name == "plastic, blik & drinkpakken overbetuwe":
            item_name = "pmd"
        if item_name == "papier":
            item_name = "papier"
        if item_name == "papier en karton":
            item_name = "papier"
        if item_name == "pmd":
            item_name = "pmd"
        if item_name == "textiel":
            item_name = "textiel"
        if item_name == "kerstb":
            item_name = "kerstboom"
        return item_name

    def _get_waste_data_provider(self):
        try:
            self.bag_id = None
            self._verify = self.provider != "suez"
            url = f"{SENSOR_COLLECTORS_OPZET[self.provider]}/rest/adressen/{self.postal_code}-{self.street_number}"

            raw_response = requests.get(url, verify=self._verify)
        except requests.exceptions.RequestException as err:
            raise ValueError(err) from err

        try:
            response = raw_response.json()
        except ValueError as e:
            raise ValueError(f"Invalid and/or no data received from {url}") from e

        if not response:
            _LOGGER.error("No waste data found!")
            return

        try:
            if len(response) > 1 and self.suffix:
                for item in response:
                    if (
                        item["huisletter"] == self.suffix
                        or item["huisnummerToevoeging"] == self.suffix
                    ):
                        self.bag_id = item["bagId"]
                        break
            else:
                self.bag_id = response[0]["bagId"]

            url = f"{SENSOR_COLLECTORS_OPZET[self.provider]}/rest/adressen/{self.bag_id}/afvalstromen"
            waste_data_raw_temp = requests.get(url, verify=self._verify).json()

            self.waste_data_raw = []

            for item in waste_data_raw_temp:
                if not item["ophaaldatum"]:
                    continue

                waste_type = item["menu_title"]
                if not waste_type:
                    continue

                temp = {
                    "type": self.__waste_type_rename(item["menu_title"].strip().lower())
                }
                temp["date"] = datetime.strptime(
                    item["ophaaldatum"], "%Y-%m-%d"
                ).strftime("%Y-%m-%d")
                self.waste_data_raw.append(temp)

        except ValueError as exc:
            raise ValueError(f"Invalid and/or no data received from {url}") from exc
