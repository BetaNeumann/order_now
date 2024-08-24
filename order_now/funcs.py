from typing import TYPE_CHECKING
import re
import os

from sqlalchemy.orm import Session
from sqlalchemy.orm import object_session

from . import errors

if TYPE_CHECKING:
    from .models.models import Base


def snake_case(string: str) -> str:
    return re.sub(r'([a-z])([A-Z])', r'\1_\2', string).lower()


def camel_case(string: str, upper: bool = False) -> str:
    if upper:
        string = string[0].upper() + string[1:]
    return re.sub(r'_([a-z])', lambda s: s.group(1).upper(), string)


def get_session(instance: 'Base') -> Session:
    if (session := object_session(instance)) is None:
        raise errors.ObjectOutOfSession
    return session


def get_envar(envar_name: str) -> str:
    if (envar := os.getenv(envar_name)) is None:
        raise ValueError('Envar not found')
    return envar
