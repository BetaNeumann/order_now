from typing import TYPE_CHECKING, Self
from types import new_class
from decimal import Decimal
from datetime import datetime
from ipaddress import IPv4Address
from dataclasses import field

from sqlalchemy import MetaData
from sqlalchemy import BigInteger, Numeric
from sqlalchemy import select, func
from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass, Mapped
from sqlalchemy.orm import declared_attr
from sqlalchemy.schema import Identity
from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.dialects.postgresql import INET

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from .columns import column, relationship, standard_fk
from . import enums
from .. import funcs

from . import __version__

if TYPE_CHECKING:
    from . import schemas


hasher = PasswordHasher()

type_annotation_map = {
    Decimal: Numeric(12,2),
    IPv4Address: INET
}


class Base(DeclarativeBase, MappedAsDataclass):
    metadata = MetaData(schema=__version__)
    type_annotation_map = type_annotation_map

    __schema__: type['schemas.Schema[Self]'] | None = field(init=False, repr=False, default=None)

    id: Mapped[int] = column(BigInteger, Identity(), primary_key=True, sort_order=-99, init=False)


    @declared_attr.directive
    def __tablename__(cls) -> str:
        return funcs.snake_case(cls.__name__)


    @classmethod
    def schema(cls, *, only: tuple[str, ...] | None = None, exclude: tuple[str, ...] = ()) -> 'schemas.Schema[Self]':
        if cls.__schema__ is None:
            from .schemas import Schema
            
            class Meta(Schema.Meta):
                model = cls
            
            cls.__schema__ = new_class(f'{cls.__name__}Schema', (Schema,), {'Meta': Meta})

        return cls.__schema__(only=only, exclude=exclude)


class User(Base):
    name: Mapped[str] = column()
    email: Mapped[str] = column()
    _password: Mapped[str] = column('password')
    access_level: Mapped[enums.UserAccessLevel] = column()
    blocked: Mapped[bool] = column(default=False)

    login_attempts: Mapped[list['LoginAttempt']] = relationship(back_populates='user', default_factory=list)
    orders: Mapped[list['Order']] = relationship(back_populates='user', default_factory=list)


    @property
    def password(self) -> str:
        return self._password


    @property
    def login_attempts_count(self) -> int:
        return funcs.get_session(self).execute(
            select(func.count(LoginAttempt.id)).where(
                LoginAttempt.user_id == User.id,
                LoginAttempt.date >= datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            )
        ).scalar_one()


    def set_new_password(self, new_password: str) -> None:
        self._password = hasher.hash(new_password)


    def validate_password(self, password: str) -> bool:
        try:
            hasher.verify(self.password, password)
        except VerifyMismatchError:
            self.login_attempts.append(LoginAttempt())
            
            if self.login_attempts_count > 3:
                self.blocked = True

            return False

        if hasher.check_needs_rehash(self.password):
            self.set_new_password(password)

        return True


class LoginAttempt(Base):
    date: Mapped[datetime] = column(default=datetime.now())
    ip: Mapped[IPv4Address] = column()

    user_id: Mapped[int] = standard_fk('user')
    user: Mapped[User] = relationship(back_populates='login_attempts')


class Group(Base):
    description: Mapped[str] = column()
    
    items: Mapped[list['Item']] = relationship('group', default_factory=list, lazy='immediate')


class Item(Base):
    name: Mapped[str] = column()
    description: Mapped[str] = column()
    price: Mapped[Decimal] = column()

    group_id: Mapped[int] = standard_fk('group')
    group: Mapped[Group] = relationship(back_populates='items')

    flavors: Mapped[list['Flavor']] = relationship(back_populates='item', default_factory=list)
    extras: Mapped[list['Extra']] = relationship(back_populates='item', default_factory=list)
    ordered_items: Mapped[list['OrderItem']] = relationship(back_populates='item', default_factory=list)


class Flavor(Base):
    description: Mapped[str] = column()
    price: Mapped[Decimal] = column(default=Decimal(0))
    
    item_id: Mapped[int] = standard_fk('item')
    item: Mapped[Item] = relationship(back_populates='flavors')


class Extra(Base):
    description: Mapped[str] = column()
    price: Mapped[Decimal] = column()

    item_id: Mapped[int] = standard_fk('item')
    item: Mapped[Item] = relationship(back_populates='extras')


class Order(Base):
    created_at: Mapped[datetime] = column(default=datetime.now())
    client_name: Mapped[str | None] = column()
    table_number: Mapped[int | None] = column()
    total: Mapped[Decimal] = column()

    user_id: Mapped[int] = standard_fk('user')
    user: Mapped[User] = relationship(back_populates='orders')

    ordered_items: Mapped[list['OrderItem']] = relationship(back_populates='order', default_factory=list)


class OrderItem(Base):
    ammount: Mapped[int] = column()

    order_id: Mapped[int] = standard_fk('order')
    order: Mapped[Order] = relationship(back_populates='ordered_items')

    item_id: Mapped[int] = standard_fk('item')
    item: Mapped[Item] = relationship(back_populates='ordered_items', lazy='dynamic')
    
    flavor_id: Mapped[int | None] = standard_fk('flavor', nullable=True)
    flavor: Mapped[Flavor | None] = relationship(back_populates='ordered_items')

    extras: Mapped[list['OrderItemExtra']] = relationship(back_populates='order_item', default_factory=list)


class OrderItemExtra(Base):
    ammount: Mapped[int] = column()

    order_item_id: Mapped[int] = standard_fk('order_item')
    order_item: Mapped[OrderItem] = relationship(back_populates='extras')

    extra_id: Mapped[int] = standard_fk('extra')
    extra: Mapped[Extra] = relationship(lazy='immediate')


# Engine declaration
engine = create_async_engine(
    URL.create(
        drivername='postgresql+psycopg',
        username='order_now',
        password=funcs.get_envar('ORDER_NOW_PASSWORD'),
        host='localhost',
        port=5432,
        database='service_now'
    ),
    echo=True
)

session = AsyncSession(engine)
