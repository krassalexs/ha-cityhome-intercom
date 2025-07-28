import logging
import aiohttp
import asyncio
from datetime import datetime, timezone

_LOGGER = logging.getLogger(__name__)


class IntercomAPI:
    def __init__(self, base_url="https://dawson.farm.cpx2.ru/mobile/"):
        self.base_url = base_url
        self.access_token = None
        self.device_token = None

        self.headers = {
            "Content-Type": "application/json",
            "user-agent": "SmartYard/1.0.0 (com.cityhome.smartyard.oem; build:3; iOS 18.5.0) Alamofire/5.10.1",
        }
        self.token_update_callback = None

    def set_tokens(self, access_token, device_token):
        self.access_token = access_token
        self.device_token = device_token
        self.headers["Authorization"] = f"Bearer {self.access_token}"

    async def request_code(self, phone_number):
        url = f"{self.base_url}user/requestCode"
        payload = {
            "userPhone": phone_number
        }

        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.post(url, json=payload, ssl=False) as response:
                if response.status == 200:
                    return True
                else:
                    return {"error": f"Authorization failed with status code {response.status}"}

    async def confirm_code(self, phone_number, code, device_token):
        url = f"{self.base_url}user/confirmCode"
        payload = {
            "userPhone": phone_number,
            "smsCode": code,
            "deviceToken": device_token
        }

        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.post(url, json=payload, ssl=False) as response:
                if response.status == 200:
                    data = await response.json()
                    self.set_tokens(
                        data["data"]["accessToken"],
                        device_token
                    )
                    if self.token_update_callback:
                        self.token_update_callback(
                            data["data"]["accessToken"],
                            device_token
                        )
                return await response.json()

    async def get_address_list(self):
        if not self.access_token:
            return {"error": "No access token available"}
        url = f"{self.base_url}address/getAddressList"
        payload = {}
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.post(url, json=payload, ssl=False) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("data", [])
                else:
                    _LOGGER.error(f"Ошибка получения дверей {response.status}")
                    return []

    async def open_door(self, domophone_id, door_id):
        if not self.access_token:
            return {"error": "No access token available"}
        url = f"{self.base_url}address/openDoor"
        payload = {
            "domophoneId": domophone_id,
            "doorId": door_id
        }
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.post(url, json=payload, ssl=False) as response:
                if response.status == 204:
                    return True
                else:
                    _LOGGER.error(f"Ошибка открытия двери {response.status}")
                    return False

