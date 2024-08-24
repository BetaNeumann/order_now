from typing import Literal, Any, overload

from marshmallow import fields
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema

from . import models as m
from .. import funcs, json_encoder


class Schema[M](SQLAlchemyAutoSchema):
    class Meta(SQLAlchemyAutoSchema.Meta):
        model: type[m.Base]
        render_module = json_encoder
        load_instance = True


    def on_bind_field(self, field_name: str, field_obj: fields.Field) -> None:
        if field_obj.data_key is None:
            field_obj.data_key = funcs.camel_case(field_name)


    @overload # type: ignore
    def load(self, data: json_encoder.JsonObject) -> M: ...
    @overload
    def load(self, data: json_encoder.JsonObject, *, many: Literal[False], **kwargs: Any) -> M: ...
    @overload
    def load(self, data: json_encoder.JsonList, *, many: Literal[True], **kwargs: Any) -> list[M]: ...
    @overload
    def load(self, data: bytes, *, many: Literal[False], **kwargs: Any) -> M: ...
    @overload
    def load(self, data: bytes, *, many: Literal[True], **kwargs: Any) -> list[M]: ...
    def load(
        self,
        data: json_encoder.JsonObject | json_encoder.JsonList | bytes,
        *,
        many: bool = False,
        **kwargs: Any
    ) -> M | list[M]:
        if isinstance(data, bytes):
            return super().loads(data, many=many, **kwargs) # type: ignore
        return super().load(data, many=many, **kwargs) # type: ignore


    @overload # type: ignore
    def dump(self, obj: M) -> json_encoder.JsonObject: ...
    @overload
    def dump(self, obj: M, *, many: Literal[False]) -> json_encoder.JsonObject: ...
    @overload
    def dump(self, obj: M, *, as_bytes: Literal[True]) -> bytes: ...
    @overload
    def dump(self, obj: M, *, many: Literal[False], as_bytes: Literal[False]) -> json_encoder.JsonObject: ...
    @overload
    def dump(self, obj: M, *, many: Literal[False], as_bytes: Literal[True]) -> bytes: ...

    @overload
    def dump(self, obj: list[M], *, many: Literal[True]) -> json_encoder.JsonList: ...
    @overload
    def dump(self, obj: list[M], *, many: Literal[True], as_bytes: Literal[False]) -> json_encoder.JsonList: ...
    @overload
    def dump(self, obj: list[M], *, many: Literal[True], as_bytes: Literal[True]) -> bytes: ...
    def dump(
        self,
        obj: M | list[M],
        *,
        many: bool = False,
        as_bytes: bool = False,
    ) -> json_encoder.JsonObject | json_encoder.JsonList | bytes:
        if as_bytes:
            return super().dumps(obj, many=many) # type: ignore
        return super().dump(obj, many=many) # type: ignore


    def __init_subclass__(cls) -> None:
        if not hasattr(cls.Meta, 'model'):
            raise NotImplementedError(f'Class "{cls}" has no model attached.')
        cls.Meta.model.__schema__ = cls # type: ignore
