import logging
import aiohttp

_LOGGER = logging.getLogger(__name__)

CAMERA_STREAM_PATH = "/index.fmp4.m3u8?token="
CAMERA_PREVIEW_PATH = "/preview.mp4?token="


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

    async def _make_request(self, endpoint, payload=None, method="POST"):
        if not self.access_token and endpoint not in ("user/requestCode", "user/confirmCode"):
            return {"error": "No access token available"}

        url = f"{self.base_url}{endpoint}"

        async with aiohttp.ClientSession(headers=self.headers) as session:
            try:
                if method == "POST":
                    async with session.post(url, json=payload, ssl=False) as response:
                        return await self._handle_response(response)
                elif method == "GET":
                    async with session.get(url, ssl=False) as response:
                        return await self._handle_response(response)
            except aiohttp.ClientError as e:
                _LOGGER.error(f"Request failed: {e}")
                return {"error": str(e)}

    @staticmethod
    async def _handle_response(response):
        if response.status == 200:
            return await response.json()
        elif response.status == 204:  # No Content (например, при открытии двери)
            return True
        else:
            _LOGGER.error(f"Request failed with status {response.status}")
            return {"error": f"HTTP {response.status}"}

    def set_tokens(self, access_token, device_token):
        self.access_token = access_token
        self.device_token = device_token
        self.headers["Authorization"] = f"Bearer {self.access_token}"

    async def request_code(self, phone_number):
        """Запрос кода подтверждения"""
        return await self._make_request(
            "user/requestCode",
            {"userPhone": phone_number}
        )

    async def confirm_code(self, phone_number, code, device_token):
        """Подтверждение кода и получение токенов"""
        result = await self._make_request(
            "user/confirmCode",
            {
                "userPhone": phone_number,
                "smsCode": code,
                "deviceToken": device_token
            }
        )
        if "data" in result:
            self.set_tokens(result["data"]["accessToken"], device_token)
        return result

    async def get_address_list(self):
        """Получение списка адресов"""
        result = await self._make_request("address/getAddressList")
        return result.get("data", []) if isinstance(result, dict) else []

    async def get_cameras_list(self):
        """Получение списка камер"""
        result = await self._make_request("cctv/allTree")
        return result.get("data", []) if isinstance(result, dict) else []

    async def open_door(self, domophone_id, door_id):
        """Открытие двери"""
        result = await self._make_request(
            "address/openDoor",
            {"domophoneId": domophone_id, "doorId": door_id}
        )
        return result is True
