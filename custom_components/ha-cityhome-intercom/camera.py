import asyncio
import logging
from homeassistant.components.camera import (
    Camera,
    CameraEntityFeature,
    CameraEntityDescription,
    StreamType,
)
from .const import DOMAIN, API
from .api import CAMERA_STREAM_PATH, CAMERA_PREVIEW_PATH

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    entities = []
    api = hass.data[DOMAIN][API]
    response = await api.get_cameras_list()
    cameras = response.get("cameras", [])

    for camera in cameras:
        camera_id = camera["id"]
        if camera["url"] is not None:
            entities.append(IntercomCamera(api, camera_id, camera["name"], camera["url"]))

    async_add_entities(entities, True)


class IntercomCamera(Camera):
    _attr_supported_features = CameraEntityFeature.STREAM
    _attr_frontend_stream_type = StreamType.HLS
    _attr_motion_detection_enabled = False

    def __init__(self, api, camera_id: int, name: str, camera_url: str):
        super().__init__()
        self._api = api
        self._id = camera_id
        self._name = name
        self._stream_url = camera_url + CAMERA_STREAM_PATH
        self._preview_url = camera_url + CAMERA_PREVIEW_PATH
        self._last_preview_image = None  # Последнее удачное изображение

    @property
    def unique_id(self):
        return self._id

    @property
    def name(self):
        return f"Камера {self._name}"

    async def async_camera_image(self, width=None, height=None):
        new_image = await self._get_ffmpeg_frame()
        if new_image:
            self._last_preview_image = new_image
        return self._last_preview_image

    async def _get_ffmpeg_frame(self):
        """Получаем кадр из MP4 с помощью FFmpeg через subprocess."""
        ffmpeg_cmd = [
            "ffmpeg",
            "-i", self._preview_url,
            "-frames:v", "1",  # 1 кадр
            "-f", "image2",  # Формат вывода
            "-update", "1",  # Обновление
            "-vf", "scale=640:-1",  # Масштабирование (уменьшает нагрузку)
            "-q:v", "2",  # Качество JPEG (1-31, где 2 — лучшее)
            "-",
        ]

        try:
            proc = await asyncio.wait_for(
                asyncio.create_subprocess_exec(
                    *ffmpeg_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                ),
                timeout=10.0,  # Ждём не больше 10 секунд
            )
            stdout, _ = await proc.communicate()
            return stdout if proc.returncode == 0 else None
        except asyncio.TimeoutError:
            _LOGGER.warning("FFmpeg таймаут: поток не отвечает")
            return None

    async def stream_source(self):
        return self._stream_url

    @property
    def supported_features(self):
        return self._attr_supported_features

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, str(self.unique_id))},
            "name": self._name,
            "manufacturer": "Город Телеком",
            "model": "CityHome Intercom",
            "via_device": (DOMAIN, str(self.unique_id)),
        }

    async def async_update(self):
        _LOGGER.debug(f"Updating camera: {self._name}")
