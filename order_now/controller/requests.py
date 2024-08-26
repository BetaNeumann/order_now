from fastapi.responses import ORJSONResponse

from .app import app
from . import schemas
from .. import models


# User related requests
@app.post('/user')
async def create_user(new_user: schemas.UserSchema):
    async with models.get_session() as session:
        user = models.User.model_validate(new_user)
        session.add(user)
        await session.commit()


# Order related requests
@app.post('/order')
async def create_order(new_order: schemas.OrderSchema):
    async with models.get_session() as session:
        order = models.Order.model_validate(new_order)
        session.add(order)
        await session.commit()
