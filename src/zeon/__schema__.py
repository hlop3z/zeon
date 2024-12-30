# Core
ENGINE = {
    "action": {
        "getter": {  # query (Read)
            "http": "GET",
            "docs": "Retrieve zero-or-one row based on a unique identifier.",
        },
        "finder": {  # query (Read)
            "http": "GET",
            "docs": "Retrieve zero-or-multiple rows based on search criteria.",
        },
        "create": {  # mutation (Edit)
            "http": "POST",
            "docs": "Create one-or-multiple new rows in the database.",
        },
        "update": {  # mutation (Edit)
            "http": "PUT",
            "docs": "Modify one-or-multiple existing rows.",
        },
        "delete": {  # mutation (Edit)
            "http": "DELETE",
            "docs": "Mark one-or-multiple rows as deleted (soft delete).",
        },
    },
    "method": {
        "POST": "Create a new resource on the server.",
        "GET": "Retrieve a resource or collection of resources from the server.",
        "PUT": "Update an existing resource on the server (idempotent).",
        "DELETE": "Delete a resource from the server (soft delete).",
        "PATCH": "Obliterate a resource (hard delete).",
    },
    "ignore": ["null", "undefined"],  # Values to be excluded during processing
    "basics": ["int", "float", "string", "bool", "null"],
    "native": {  # Supported primitive types in various languages (e.g., Python, GoLang, JavaScript)
        # Primitive Types
        "int": "A signed 32-bit integer, commonly used for whole numbers.",
        "float": "A double-precision, signed floating-point number, used for representing decimals.",
        "string": "A sequence of characters encoded in UTF-8, representing text.",
        "bool": "A boolean type with two possible values: true or false.",
        # Complex Types
        "dict": "A collection of `key-value` pairs, where keys are strings and values can be of `any` type.",
        "list": "An ordered collection of elements, each element being of `any` type.",
        "null": "Represents the intentional absence of any value or object (non-usable).",
        "date_time": "A date and time representation in ISO-8601 format (e.g., '2024-12-26T12:34:56').",
    },
    "scalar": {  # GraphQL-like internal scalar types
        # Database Types
        "id": "A unique identifier, typically used for distinguishing individual entities.",
        "text": "A special type of `string`.",
        "model": "A `dict` with a namespace for the object type.",
        "array": "A `list` of a specified type.",
        # Numeric Types
        "big_int": "A signed 64-bit integer, used for large whole numbers.",
        "decimal": "A high-precision numeric value serialized as a string for accuracy.",
        # Date-Time Types
        "date": "A date in ISO-8601 format, without a time component (e.g., '2024-12-26').",
        "time": "A time representation in ISO-8601 format, without a date component (e.g., '12:34:56').",
        # Other Types
        "enum": "Enums are a special kind of scalar that is restricted to a particular set of allowed values.",
        "any": "A special type of `union`.",
        "union": "A type that allows a variable to hold values of multiple specified types.",
        "undefined": "Indicates a variable has been declared but not initialized (non-usable).",
        # Function Types
        "computed": "A dynamically calculated value, derived from other variables or inputs.",
        # Files/Directories Types
        "file": "Stores metadata about file in a filesystem.",
    },
    "reference": {
        "model": "one-to-one",  # $Ref
        "array": "one-to-many",  # [$Ref]
        "many": "many-to-many",
        "poly": "polymorphic",
    },
}

# Schema
SCHEMA = {
    "engine": {
        "name": "python",
        "version": "3.13",
        "serialization": {"loads": {}, "dumps": {}},
    },
    "info": {
        "name": "sample_api",
        "docs": "This is a sample API to demonstrate ToyQL.",
        "version": "1.0.0",
    },
    "servers": [
        {"url": "http://localhost:8000"},
    ],
    "utils": {
        "rules",  #  Form Validators
        "clean",  #  Type/Form Filters
    },
    "component": {
        "scalar": {},  # Like GraphQL (Internal-Types)
        "action": {"read": {}, "edit": {}},  # APIs/APPs Actions
        "object": {"type": {}, "form": {}},  # Compound-Types
    },
}
