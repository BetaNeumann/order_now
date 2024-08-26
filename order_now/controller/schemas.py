from decimal import Decimal
from datetime import datetime

from pydantic import BaseModel, Field

from .. import models, enums


class Schema(BaseModel):
    pass


# User related schemas
class UserSchema(Schema):
    name: str
    email: str
    

class UserSchemaGet(UserSchema):
    access_level: enums.UserAccessLevel = Field(default=enums.UserAccessLevel.employee)
    blocked: bool = Field(default=False)


class UserSchemaPost(UserSchema):
    password: str


# Order related schemas
class OrderSchema(Schema):
    created_at: datetime
    closed_at: datetime | None = Field(default=None)
    client_name: str | None = Field(default=None)
    table_number: int | None = Field(default=None)
    total: Decimal = Field(default=0.0, max_digits=10, decimal_places=2)
    ordered_items: list['OrderItemSchema']


class OrderItemSchema(Schema):
    ammount: int
    status: enums.OrderItemStatus = Field(default=enums.OrderItemStatus.preparing)
    item_id: int
    flavor_id: int | None = Field(default=None)
    extras: list['OrderItemExtraSchema']


class OrderItemExtraSchema(Schema):
    ammount: int
    extra_id: int
