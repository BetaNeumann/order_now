from typing import Callable, Any
from decimal import Decimal
from datetime import datetime
from ipaddress import IPv4Address

from sqlmodel import SQLModel, Field, Relationship
from sqlmodel import select, func

from sqlalchemy import BigInteger
from sqlalchemy.orm import declared_attr
from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import create_async_engine

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from .. import enums
from .. import funcs


hasher = PasswordHasher()

# Commonly used fields
decimal_field = Field(default=0, max_digits=10, decimal_places=2, ge=0)


class Base(SQLModel):
    id: int = Field(primary_key=True, sa_type=BigInteger)


    @declared_attr.directive
    def __tablename__(cls) -> str | Callable[..., str]: # type: ignore
        return funcs.snake_case(cls.__name__)


class User(Base, table=True):
    name: str
    email: str
    password: str = Field(exclude=True, repr=False)
    access_level: enums.UserAccessLevel = Field(default=enums.UserAccessLevel.employee)
    blocked: bool = Field(default=False)

    login_attempts: list['LoginAttempt'] = Relationship(back_populates='user')
    orders: list['Order'] = Relationship(back_populates='user')


    def model_post_init(self, __context: Any):
        if not self.password.startswith('$argon2'):
            self.password = hasher.hash(self.password)


    @property
    def login_attempts_count(self) -> int:
        return funcs.get_session(self).execute(
            select(func.count('*')).where(
                LoginAttempt.user_id == User.id,
                LoginAttempt.date >= datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            )
        ).scalar_one()


    def validate_password(self, password: str) -> bool:
        try:
            hasher.verify(self.password, password)
        except VerifyMismatchError:
            self.login_attempts.append(LoginAttempt())
            
            if self.login_attempts_count > 3:
                self.blocked = True

            return False

        if hasher.check_needs_rehash(self.password):
            self.password = hasher.hash(password)

        return True


class LoginAttempt(Base, table=True):
    date: datetime = Field(default=datetime.now())
    ip: IPv4Address

    user_id: int = Field(foreign_key='user.id', sa_type=BigInteger)
    user: User = Relationship(back_populates='login_attempts')


class Group(Base, table=True):
    description: str

    items: list['Item'] = Relationship(back_populates='group', cascade_delete=True)


class Item(Base, table=True):
    name: str
    description: str
    price: Decimal = decimal_field

    group_id: int | None = Field(foreign_key='group.id', default=None, sa_type=BigInteger)
    group: Group | None = Relationship(back_populates='items')

    flavors: list['Flavor'] = Relationship(back_populates='item', cascade_delete=True)
    extras: list['Extra'] = Relationship(back_populates='item', cascade_delete=True)
    ordered_items: list['OrderItem'] = Relationship(back_populates='item')


class Flavor(Base, table=True):
    description: str
    price: Decimal = decimal_field

    item_id: int = Field(foreign_key='item.id', sa_type=BigInteger)
    item: Item = Relationship(back_populates='flavors')


class Extra(Base, table=True):
    description: str
    price: Decimal = decimal_field

    item_id: int = Field(foreign_key='item.id', sa_type=BigInteger)
    item: Item = Relationship(back_populates='extras')


class Order(Base, table=True):
    created_at: datetime = Field(default=datetime.now())
    closed_at: datetime | None = Field(default=None)
    client_name: str | None = Field(default=None)
    table_number: int | None = Field(default=None)
    total: Decimal = decimal_field

    user_id: int = Field(foreign_key='user.id', sa_type=BigInteger)
    user: User = Relationship(back_populates='orders')

    ordered_items: list['OrderItem'] = Relationship(
        back_populates='order', cascade_delete=True, sa_relationship_kwargs=dict(lazy='selectin')
    )


class OrderItem(Base, table=True):
    ammount: int
    status: enums.OrderItemStatus = Field(default=enums.OrderItemStatus.preparing)

    order_id: int = Field(foreign_key='order.id', sa_type=BigInteger)
    order: Order = Relationship(back_populates='ordered_items')

    item_id: int = Field(foreign_key='item.id', sa_type=BigInteger)
    item: Item = Relationship(back_populates='ordered_items', sa_relationship_kwargs=dict(lazy='selectin'))

    flavor_id: int | None = Field(foreign_key='flavor.id', default=None, sa_type=BigInteger)
    flavor: Flavor | None = Relationship()

    extras: list['OrderItemExtra'] = Relationship(
        back_populates='order_item', cascade_delete=True, sa_relationship_kwargs=dict(lazy='selectin')
    )


class OrderItemExtra(Base, table=True):
    ammount: int

    order_item_id: int = Field(foreign_key='order_item.id', sa_type=BigInteger)
    order_item: OrderItem = Relationship(back_populates='extras')

    extra_id: int = Field(foreign_key='extra.id', sa_type=BigInteger)
    extra: Extra = Relationship(sa_relationship_kwargs=dict(lazy='selectin'))


# Engine declaration
url = URL.create(
    drivername='postgresql+psycopg',
    username='order_now',
    password=funcs.get_envar('ORDER_NOW_PASSWORD'),
    host='localhost',
    port=5432,
    database='order_now_v1'
)

engine = create_async_engine(url)
model_mapping = {mapper.class_.__tablename__: mapper.class_ for mapper in Base._sa_registry.mappers}
