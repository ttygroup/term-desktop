"""Module for the DataWidgets classes."""

# python imports
from __future__ import annotations
from typing import (
    Any,
    Generic,
    TypeVar,
    List,
    Dict,
    Iterator,
    ItemsView,
    KeysView,
    ValuesView,
)

# Textual imports
from textual.widget import Widget
from textual.message import Message
import rich.repr


T = TypeVar("T")


class ListDataWidget(Widget, Generic[T]):
    """
    ListDataWidget is a simple list-like widget for Textual.

    The reason this exists is because it can be queried using Textual's query system.
    This is a better way to store data on the main app class than simply doing something
    like `self.app.my_list_foo`. Type checkers do not like self.app.my_list_foo. (It is
    only determined at runtime). If you've ever tried to do this with your type
    checker in strict mode, you know what I mean.

    By making a ListDataWidget and mounting it to the app class (hidden), we can use the
    query system (self.app.query_one(MyListDataFoo) instead of using self.app.my_list_foo.
    This provides much better type checking and it makes Pyright and MyPy happy without
    needing to use any '#type: ignore' comments.
    """

    class Updated(Message):

        def __init__(self, widget: ListDataWidget[T]) -> None:
            super().__init__()
            self.widget = widget
            "The ListDataWidget that was updated."

    items: List[T] = []

    def __init__(self) -> None:
        """Initialize the ListDataWidget.
        There are no arguments to pass in.
        TODO: This should take a list of items to start with to be more versatile."""

        super().__init__()
        self.display = False
        self.items = []

    def __rich_repr__(self) -> rich.repr.Result:
        yield "Items in ListDataWidget:"
        for item in self.items:
            try:
                yield str(item)
            except Exception:
                yield repr(item)

    def __getitem__(self, index: int) -> T:
        return self.items[index]

    def __setitem__(self, index: int, value: T) -> None:
        self.items[index] = value

    def __delitem__(self, index: int) -> None:
        del self.items[index]

    def __len__(self) -> int:
        return len(self.items)

    def __iter__(self) -> Iterator[T]:
        return iter(self.items)

    def append(self, item: T) -> None:
        self.items.append(item)
        self.post_message(self.Updated(self))

    def extend(self, other: List[T]) -> None:
        self.items.extend(other)
        self.post_message(self.Updated(self))

    def insert(self, index: int, item: T) -> None:
        self.items.insert(index, item)
        self.post_message(self.Updated(self))

    def remove_item(self, item: T) -> None:
        self.items.remove(item)
        self.post_message(self.Updated(self))

    def pop(self, index: int = -1) -> T:
        self.post_message(self.Updated(self))
        return self.items.pop(index)

    def clear(self) -> None:
        self.items.clear()
        self.post_message(self.Updated(self))

    def index(self, item: T, *args: Any) -> int:
        return self.items.index(item, *args)

    def count(self, item: T) -> int:
        return self.items.count(item)

    def copy(self) -> List[T]:
        return self.items.copy()


K = TypeVar("K")
V = TypeVar("V")


class DictDataWidget(Widget, Generic[K, V]):
    """
    DictDataWidget is a simple dict-like widget for Textual.

    The reason this exists is because it can be queried using Textual's query system.
    This is a better way to store data on the main app class than simply doing something
    like `self.app.my_dict_foo`. Type checkers do not like self.app.my_dict_foo. (It is
    only determined at runtime). If you've ever tried to do this with your type
    checker in strict mode, you know what I mean.

    By making a DictDataWidget and mounting it to the app class (hidden), we can use the
    query system (self.app.query_one(MyDictDataFoo) instead of using self.app.my_dict_foo.
    This provides much better type checking and it makes Pyright and MyPy happy without
    needing to use any '#type: ignore' comments.
    """

    store: Dict[K, V] = {}

    def __init__(self) -> None:
        super().__init__()
        self.display = False  # <-- This keeps it hidden in the DOM
        self.store = {}  #      <-- Initialize a fresh dictionary for each instance

    def __getitem__(self, key: K) -> V:
        return self.store[key]

    def __setitem__(self, key: K, value: V) -> None:
        self.store[key] = value

    def __delitem__(self, key: K) -> None:
        del self.store[key]

    def __contains__(self, key: object) -> bool:
        return key in self.store

    def __len__(self) -> int:
        return len(self.store)

    def __iter__(self) -> Iterator[K]:
        return iter(self.store)

    def keys(self) -> KeysView[K]:
        return self.store.keys()

    def values(self) -> ValuesView[V]:
        return self.store.values()

    def items(self) -> ItemsView[K, V]:
        return self.store.items()

    def update(self, other_dict: Dict[K, V]) -> None:
        self.store.update(other_dict)

    def get(self, key: K, default: Any = None) -> V | Any:
        return self.store.get(key, default)
