import aiohttp
import logging
from homeassistant.components.camera import (
    Camera,
    CameraEntityFeature,
    CameraEntityDescription,
    StreamType,
)
from homeassistant.components.ffmpeg import FFmpegFrameManager
from .const import DOMAIN, API
from .api import CAMERA_STREAM_PATH, CAMERA_PREVIEW_PATH

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    entities = []
    api = hass.data[DOMAIN][API]
    ffmpeg_manager = FFmpegFrameManager(hass)
    response = await api.get_cameras_list()
    cameras = response.get("cameras", [])

    for camera in cameras:
        camera_id = camera["id"]
        if camera["url"] is not None:
            entities.append(IntercomCamera(ffmpeg_manager, api, camera_id, camera["name"], camera["url"]))

    async_add_entities(entities, True)


class IntercomCamera(Camera):
    _attr_supported_features = CameraEntityFeature.STREAM
    _attr_frontend_stream_type = StreamType.HLS
    _attr_motion_detection_enabled = False

    def __init__(self, ffmpeg_manager, api, camera_id: int, name: str, camera_url: str):
        super().__init__()
        self._api = api
        self._id = camera_id
        self._name = name
        self._ffmpeg_manager = ffmpeg_manager
        self._stream_url = camera_url + CAMERA_STREAM_PATH
        self._preview_url = camera_url + CAMERA_PREVIEW_PATH

    @property
    def unique_id(self):
        return self._id

    @property
    def name(self):
        return f"Камера {self._name}"

    async def async_camera_image(self, width=None, height=None):
        """Получаем кадр из MP4-потока через FFmpeg."""
        try:
            image = await self._ffmpeg.get_image(
                self._preview_url,
                output_format="mjpeg",
                extra_cmd="-frames:v 1 -update 1",
            )
            return image
        except Exception as e:
            _LOGGER.error(f"Ошибка получения изображения: {e}")
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
