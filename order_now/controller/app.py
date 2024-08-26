from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from .. import config

app = FastAPI(
    title=config.app_name,
    version=config.version,
    default_response_class=ORJSONResponse
)
