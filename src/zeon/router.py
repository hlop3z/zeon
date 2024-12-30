import dataclasses as dc
import functools
import inspect
import typing as t
from collections import OrderedDict as ODict


@dc.dataclass
class Input:
    """Represents a function input parameter."""

    name: str
    type: t.Any
    default: t.Any = None


@dc.dataclass
class Operation:
    """Represents an HTTP operation."""

    call: t.Callable
    name: str
    docs: str
    path: str
    http: str | list[str]
    type: t.Any
    form: dict[str, Input]


def route(url_string: str, method: str | list[str] = "GET", prefix: str | None = None):
    """Decorator for defining HTTP routes."""

    def the_wrapper(f: t.Callable):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            print("# Before")
            result = f(*args, **kwargs)
            print("# After")
            return result

        # Extract function signature
        sign = inspect.signature(f)
        args = {
            param.name: Input(
                name=param.name,
                type=param.annotation,
                default=(
                    None if param.default is inspect.Parameter.empty else param.default
                ),
            )
            for param in sign.parameters.values()
        }

        # Create operation metadata
        __prefix = f"{prefix}_" if prefix else ""
        info = Operation(
            call=f,
            name=__prefix + f.__name__,
            docs=f.__doc__ or "",
            path=url_string,
            http=method,
            type=sign.return_annotation,
            form=args,
        )
        print(f"Operation Registered: {info}")
        return wrapper

    return the_wrapper


def get_class_bases(cls: t.Type, ignored: list | None = None) -> list[t.Type]:
    """
    Retrieve all base classes of a given class in its Method Resolution Order (MRO),
    excluding the class itself, `object`, and any classes in the ignored list.
    """
    ignored_classes = ignored or []
    return [base for base in cls.__mro__ if base not in {cls, object, *ignored_classes}]


def get_class_properties(cls: t.Type) -> dict[str, property]:
    """
    Retrieve all properties defined in a class.
    """
    return {
        name: attr for name, attr in cls.__dict__.items() if isinstance(attr, property)
    }


def get_class_info(cls: t.Type, ignored: list | None = None) -> ODict[str, t.Any]:
    """
    Retrieve all fields and properties from a class, excluding ignored bases.
    """
    annotations = ODict(cls.__annotations__)
    properties = get_class_properties(cls)

    # Include properties from bases.
    for base in get_class_bases(cls, ignored):
        annotations.update(base.__annotations__)
        properties.update(get_class_properties(base))

    # Combine annotations and properties.
    annotations.update(properties)
    return annotations
