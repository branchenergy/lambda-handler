"""Defines the `Depends` class"""

import inspect

from typing import Callable, Generic, Iterator, Optional, TypeVar, Union
from typing_extensions import TypeGuard

__all__ = ["Dependency", "DependencyC"]

R = TypeVar("R")


def is_generator(
    func: Union[Callable[[], R], Callable[[], Iterator[R]]]
) -> TypeGuard[Callable[[], Iterator[R]]]:
    """Type guard to assert that `func` returns an `Iterator[R]`

    Parameters
    ----------
    func : Union[Callable[P, R], Callable[P, Iterator[R]]]
        Callable

    Returns
    -------
    TypeGuard[Callable[P, Iterator[R]]]
        `True` if `func` returns an `Iterator[R]`
    """
    return inspect.isgeneratorfunction(func)


def is_not_generator(
    func: Union[Callable[[], R], Callable[[], Iterator[R]]]
) -> TypeGuard[Callable[[], R]]:
    """Type guard to assert that `func` returns an `R`

    Parameters
    ----------
    func : Union[Callable[P, R], Callable[P, Iterator[R]]]
        Callable

    Returns
    -------
    TypeGuard[Callable[P, R]]
        `True` if `func` returns an `R`
    """
    return not inspect.isgeneratorfunction(func)


def get_result(
    func: Union[Callable[[], R], Callable[[], Iterator[R]]],
) -> R:
    """Get the result of calling a function; if necessary with `next`

    Parameters
    ----------
    func : Union[Callable[P, R], Callable[P, Iterator[R]]]
        Callable
    *args : Any
        Arguments of `func`
    **kwargs : Any
        Keyword arguments of `func`

    Returns
    -------
    R
        Return value of `func`

    Raises
    ------
    ValueError
        If we cannot get a result
    """
    if is_generator(func):
        return next(func())
    if is_not_generator(func):
        return func()
    raise ValueError("Cannot get here!")


class DependencyC(Generic[R]):
    """Class for defining dependencies

    Parameters
    ----------
    dependency : Union[Callable[P, R], Callable[P, Iterator[R]]]
        A function or generator dependency
    use_cache : bool, default `True`
        Whether to cache the result of calling `dependency`
    """

    def __init__(
        self,
        dependency: Union[Callable[[], R], Callable[[], Iterator[R]]],
        *,
        use_cache: bool = True,
    ) -> None:
        self.dependency = dependency
        self.use_cache = use_cache
        self.result: Optional[R] = None

    def __call__(self) -> R:
        if self.result:
            return self.result
        result = get_result(self.dependency)
        if self.use_cache:
            self.result = result
        return result


def Dependency(
    dependency: Union[Callable[[], R], Callable[[], Iterator[R]]],
    *,
    use_cache: bool = True,
) -> DependencyC[R]:
    """Create a Dependency instance"""
    return DependencyC(dependency=dependency, use_cache=use_cache)
