from __future__ import annotations

from dataclasses import dataclass
from typing import Any, overload, Literal


class OutputError(Exception): ...


@dataclass
class UserConfig:
    show_enum_stubs: bool = False

@dataclass
class UserOutputDict:
    data: dict
    parent: str | None = None

    @overload
    def get(self, key: str, *, allow_other: Literal[True] = True) -> Any: ...

    @overload
    def get(self, key: str, *, allow_other: Literal[False] = False) -> UserOutputDict | list[UserOutputDict]: ...

    def get(self, key: str, *, allow_other: bool = True) -> UserOutputDict | list[UserOutputDict] | Any:
        try:
            result = self.data[key]
        except KeyError:
            if self.parent is not None:
                raise OutputError(
                    f"{self.parent} does not have key {key}\navailable keys:{self.data.keys()}"
                )
            else:
                raise OutputError(
                    f"no key {key} found\navailable keys:{self.data.keys()}"
                )
        else:
            match result:
                case dict():
                    return UserOutputDict(result, key)
                case list():
                    list_result: list[UserOutputDict] = []

                    for entry in result:
                        if isinstance(entry, dict):
                            list_result.append(UserOutputDict(entry, key))
                        else:
                            if not allow_other:
                                if self.parent:
                                    raise OutputError(
                                        f"{self.parent}.{key}'s entries were not objects when they where expected"
                                    )
                                else:
                                    raise OutputError(
                                        f"{key} entries were not objects when they where expected"
                                    )
                            list_result.append(entry)

                    return list_result
                case _:
                    if allow_other:
                        return result
                    else:
                        if self.parent:
                            raise OutputError(
                                f"{self.parent}.{key} was not an object when one was expected"
                            )
                        else:
                            raise OutputError(
                                f"{key} was not an object when one was expected"
                            )


@dataclass
class Processor:
    type_data: dict
    config: UserConfig

    def get_enum_data(self, property_definition: UserOutputDict, value: int) -> str | None:
        type_name: str = property_definition.get("type")

        if not type_name.startswith("enum"):
            return None

        if self.config.show_enum_stubs:
            enum_stub = type_name.split(" ")[1] + "::"
        else:
            enum_stub = ""

        for key, enum_value in property_definition.get("enum_options").items():
            if enum_value == value:
                return enum_stub + key

        raise OutputError(f"could not find enum name for value {value} of type {type_name}")

    def decend_tree(self, data: UserOutputDict, decent_tree: list[str]) -> UserOutputDict | list[UserOutputDict]:
        result = data
        for decention in decent_tree:
            result = data.get(decention, allow_other=False)

        return result

    def process_property(self, object_data: UserOutputDict, property_name: str):
        object_hash = object_data.get("$__type")

        property_definition = self.type_data["classes"][str(object_hash)]["properties"][property_name]

        data_value = object_data.get(property_name)
        maybe_converted_value = self.get_enum_data(
            property_definition,
            data_value,
        )

        if maybe_converted_value is not None:
            #print(f"{property_name}: {data_value} -> {maybe_converted_value}")
            object_data.data[property_name] = maybe_converted_value

    def process_object(self, data: UserOutputDict):
        for property_name in data.data.keys():
            if property_name != "$__type":
                self.process_property(object_data=data, property_name=property_name)

    def _process_subobject(self, subobject: UserOutputDict):
        for property, value in subobject.data.items():
            match value:
                case dict():
                    self.process_object(UserOutputDict(value))
                    self._process_subobject(UserOutputDict(value))
                case list():
                    for entry in value:
                        if isinstance(entry, dict):
                            as_user_output = UserOutputDict(entry)
                            self.process_object(as_user_output)
                            self._process_subobject(as_user_output)
                case _:
                    pass

    def _process(self, data: UserOutputDict, decent_tree: list[str], *, recurse_into: bool = False):
        decended_data: UserOutputDict | list[UserOutputDict] = self.decend_tree(data, decent_tree)

        match decended_data:
            case UserOutputDict():
                self.process_object(decended_data)
            case list():
                for object in decended_data:
                    self.process_object(object)
            case _:
                raise RuntimeError("unexpected type")

        if recurse_into:
            if isinstance(decended_data, list):
                for entry in decended_data:
                    if isinstance(entry, dict):
                        self._process_subobject(UserOutputDict(entry))
            else:
                self._process_subobject(decended_data)

    def process(self, data: dict, decent_tree: list[str], *, recurse_into: bool = False):
        try:
            self._process(UserOutputDict(data), decent_tree, recurse_into=recurse_into)
        except OutputError as error:
            print(error)
        except Exception as error:
            print(f"Unexpected error while processing: {type(error)!r}({error})")

        return data
