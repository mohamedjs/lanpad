"""Result type for functional error handling without exceptions."""

from typing import Generic, Optional, TypeVar

T = TypeVar("T")
E = TypeVar("E")


class Result(Generic[T, E]):
    """Represents either success (Ok) with value T, or failure (Err) with error E."""

    def __init__(self, value: Optional[T], error: Optional[E], is_ok: bool):
        self._value = value
        self._error = error
        self._is_ok = is_ok

    @classmethod
    def ok(cls, value: T) -> "Result[T, E]":
        return cls(value, None, True)

    @classmethod
    def err(cls, error: E) -> "Result[T, E]":
        return cls(None, error, False)

    @property
    def is_ok(self) -> bool:
        return self._is_ok

    @property
    def is_err(self) -> bool:
        return not self._is_ok

    def unwrap(self) -> T:
        if not self._is_ok:
            raise ValueError(f"Called unwrap on Err: {self._error}")
        return self._value  # type: ignore

    def unwrap_err(self) -> E:
        if self._is_ok:
            raise ValueError(f"Called unwrap_err on Ok: {self._value}")
        return self._error  # type: ignore
