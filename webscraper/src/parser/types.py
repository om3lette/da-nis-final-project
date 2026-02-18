from typing import TypeVar, NamedTuple, Generic

T = TypeVar('T')

class UpdateResult(NamedTuple, Generic[T]):
    value: T
    should_update: bool
