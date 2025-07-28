import aiohttp
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

    @property
    def unique_id(self):
        return self._id

    @property
    def name(self):
        return f"Камера {self._name}"

    
    async def async_camera_image(self, width=None, height=None):
        """Return a still image from the MP4 stream using FFmpeg."""
        ffmpeg = self.hass.data["ffmpeg"]
        ffmpeg_input = self._preview_url

        extra_cmd = "-frames:v 1"  # Получить один кадр

        image = await ffmpeg.async_get_image(
            ffmpeg_input,
            output_format="mjpeg",
            extra_cmd=extra_cmd,
        )
        self._last_image = image
        return image
        
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
