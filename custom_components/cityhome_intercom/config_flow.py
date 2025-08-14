from homeassistant import config_entries
import voluptuous as vol
import re
from .const import DOMAIN, CONF_PHONE_NUMBER, CONF_CONFIRM_CODE, PARAM_DEVICE_TOKEN, PARAM_ACCESS_TOKEN
from .api import IntercomAPI
from uuid import uuid4


class IntercomFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self):
        self._phone_number = None
        self._confirm_code = None
        self._device_token = str(uuid4())
        self._api = IntercomAPI()

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            self._phone_number = self._sanitize_number(user_input[CONF_PHONE_NUMBER])

            response = await self._api.request_code(self._phone_number)
            if response.get("code", 0) != 200:
                errors["base"] = "authorization_failed"
            else:
                return await self.async_step_confirm()

        data_schema = vol.Schema({
            vol.Required(CONF_PHONE_NUMBER): str,
        })

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )

    async def async_step_confirm(self, user_input=None):
        errors = {}
        if user_input is not None:
            self._confirm_code = user_input[CONF_CONFIRM_CODE]

            response = await self._api.confirm_code(
                self._phone_number, self._confirm_code, self._device_token
            )
            if 'errorText' in response:
                errors["base"] = "confirmation_failed"
            else:
                return self.async_create_entry(
                    title=self._phone_number,
                    data={
                        PARAM_ACCESS_TOKEN: self._api.access_token,
                        PARAM_DEVICE_TOKEN: self._device_token,
                    }
                )

        data_schema = vol.Schema({
            vol.Required(CONF_CONFIRM_CODE): str,
        })

        return self.async_show_form(
            step_id="confirm", data_schema=data_schema, errors=errors
        )

    def _sanitize_number(self, input_string):
        sanitized = re.sub(r'\D', '', input_string)
        return sanitized