from typing import TypedDict, Unpack, Callable, Literal, Any, overload

from sqlalchemy import BigInteger
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column, relationship as sa_relationship


class DataclassKwargs(TypedDict, total=False):
    init: bool
    repr: bool
    default: Any
    default_factory: Callable[[], Any]


class ColumnKwargs(DataclassKwargs, total=False):
    primary_key: bool
    index: bool
    unique: bool
    sort_order: int


class RelationshipKwargs(DataclassKwargs, total=False):
    back_populates: str
    cascade: str
    remote_side: list[Any] | Callable[[], Mapped[Any]]
    primaryjoin: str
    foreign_keys: str | Mapped[int] | list[Mapped[int]] | Callable[[], Mapped[int]] | Callable[[], list[Mapped[int]]]
    lazy: bool | Literal['select', 'joined', 'selectin', 'subquery', 'raise', 'raise_on_sql', 'noload', 'immediate', 'write_only', 'dynamic'] | None


def column(type: Any = None, *args: Any, **kwargs: Unpack[ColumnKwargs]) -> Mapped[Any]:
    if 'default_factory' not in kwargs:
        kwargs.setdefault('default', None)
    return mapped_column(type, *args, **kwargs)


def relationship(argument: Any = None, secondary: Any = None, **kwargs: Unpack[RelationshipKwargs]) -> Mapped[Any]:
    kwargs.setdefault('repr', False)
    kwargs.setdefault('lazy', True)
    if 'default_factory' not in kwargs:
        kwargs.setdefault('default', None)
    return sa_relationship(argument, secondary, **kwargs)


@overload
def standard_fk(tablename: str, nullable: Literal[True]) -> Mapped[int | None]: ...
@overload
def standard_fk(tablename: str, nullable: Literal[False]) -> Mapped[int]: ...
@overload
def standard_fk(tablename: str) -> Mapped[int]: ...
def standard_fk(tablename: str, nullable: bool = False) -> Mapped[int] | Mapped[int | None]:
    return mapped_column(
        BigInteger,
        ForeignKey(f"{tablename}.id"),
        nullable=nullable,
        sort_order=-1,
        init=False
    )
