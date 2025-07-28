import logging
from homeassistant.components.button import ButtonEntity
from .const import DOMAIN, API

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    entities = []
    api = hass.data[DOMAIN][API]
    response = await api.get_address_list()

    for address in response:
        for door in address.get("doors", {}):
            address_name = address["address"]
            house_id = address["houseId"]
            domophone_id = door["domophoneId"]
            door_id = door["doorId"]
            door_type = door["icon"]
            door_name = door["name"]
            entities.append(IntercomDoor(api, address_name, house_id, domophone_id, door_id, door_type, door_name))

    async_add_entities(entities, True)


class IntercomDoor(ButtonEntity):
    _attr_has_entity_name = True

    def __init__(self, api, address_name: str, house_id: str,
                 domophone_id: str, door_id: int, door_type: str, door_name: str):
        self._api = api
        self._address_name = address_name
        self._house_id = house_id
        self._domophone_id = domophone_id
        self._door_id = door_id
        self._name = door_name
        self._attr_icon = f"mdi:{'door' if door_type == "entrance" else "gate"}"

    @property
    def unique_id(self):
        return f"{self._house_id}_{self._domophone_id}_{self._door_id}"

    @property
    def name(self):
        return f"Открыть {self._name}"

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.unique_id)},
            "name": self._address_name + "," + self._name,
            "manufacturer": "Город Телеком",
            "model": "CityHome Intercom",
            "via_device": (DOMAIN, self.unique_id),
        }

    async def async_press(self):
        try:
            response = await self._api.open_door(self._domophone_id, self._door_id)
            if not response:
                _LOGGER.error(f"Failed to open the door {self._name}. Response: {response}")
        except Exception as e:
            _LOGGER.error(f"Error opening the door {self._name}: {e}")