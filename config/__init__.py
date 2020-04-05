import typing
from collections import defaultdict
import pathlib
import os
from . import base

try:
    # Try from any local changes
    from . import base_local
except ImportError:
    pass


def resolve_path(string_path: str, parent: pathlib.PurePath = None):
    """ """
    if os.path.isabs(string_path):
        return pathlib.Path(string_path)
    elif string_path.startswith("~"):
        return pathlib.Path(os.path.expanduser(string_path))

    if parent is None:
        parent = pathlib.Path(os.getcwd())
    if string_path == ".":
        return parent

    me = parent
    for part in string_path.split(os.sep):
        if not part:
            continue
        if part == ".":
            continue
        elif part == "..":
            me = me.parent
        else:
            me = me / part
    return me


class Configuration(object):
    """Simple Configuration Class"""

    _initialized: bool
    __storage__: typing.DefaultDict[typing.Text, typing.Any]
    __slots__ = ("__storage__", "_initialized")

    def __init__(self):
        """ """
        object.__setattr__(self, "__storage__", defaultdict())
        object.__setattr__(self, "_initialized", False)
        self.init()
        object.__setattr__(self, "_initialized", True)
        self.normalize_paths()

    def init(self):
        """ """
        init_ = object.__getattribute__(self, "_initialized")
        if init_ is True:
            raise ValueError("Instance has already be initialized!")

        members = globals()

        def _add(items):
            """ """
            for key, val in items:
                if key.isupper() is False:
                    continue
                setattr(self, key, val)

        _add(members.get("base").__dict__.items())

        if members.get("base_local", None):
            _add(members.get("base_local").__dict__.items())

    def normalize_paths(self):
        """ """
        init_ = object.__getattribute__(self, "_initialized")
        if init_ is False:
            raise ValueError("Instance has must be initialized!")

        storage = object.__getattribute__(self, "__storage__")
        base_path = storage["BASE_PATH"]
        if not isinstance(base_path, pathlib.PurePath):
            base_path = resolve_path(base_path, None)
            storage["BASE_PATH"] = base_path

        needed_paths = (
            "CACHE_PATH",
            "RESOURCE_TARGET_DIRECTORY",
            "FACTORY_TARGET_NAME",
            "DEPENDENCIES_TARGET_FILE_NAME",
            "UNITTEST_TARGET_DIRECTORY",
            "UNITTEST_COPY_FILES",

        )
        for np in needed_paths:
            val = storage[np]
            if isinstance(val, list):
                new_val = list()
                for p in val:
                    if isinstance(p, pathlib.PurePath):
                        new_val.append(p)
                    else:
                        new_val.append(resolve_path(p, base_path))
                storage[np] = new_val
            else:
                if not isinstance(val, pathlib.PurePath):
                    storage[np] = resolve_path(val, base_path)

        # take care of manual profiles
        new_profiles = list()
        for path, mod_name, values in storage["MANUAL_PROFILES"]:
            if not isinstance(path, pathlib.PurePath):
                path = resolve_path(path, base_path)
            new_profiles.append((path, mod_name, values))

        storage["MANUAL_PROFILES"] = new_profiles

    def __getitem__(self, item):
        """ """
        try:
            return self.__storage__[item]
        except KeyError:
            raise KeyError(f"´item´ is not defined in any configuration.")

    def __getattr__(self, item):
        """ """
        try:
            return self.__storage__[item]
        except KeyError:
            raise AttributeError(f"´item´ is not defined in any configuration.")

    def __setitem__(self, key, value):
        """ """
        storage = object.__getattribute__(self, "__storage__")
        storage[key] = value

    def __setattr__(self, key, value):
        """ """
        self[key] = value
