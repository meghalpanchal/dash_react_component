from typing import Any, Dict, Set, Type
from dash import Dash  # type: ignore
from dash.development.base_component import Component  # type: ignore
from urllib import parse
from flask import send_from_directory
from ._config import config
from ._common import import_file_name, import_namespace, react_file_name
from ._file_generator import generate_import_file, generate_react_file
from ._types import AppKey, ComponentKey, LibraryKey
from ._utils import change_function_name

_initialized_apps: Set[AppKey] = set()
_initialized_libraries: Set[LibraryKey] = set()
_initialized_components: Dict[ComponentKey, Type[Component]] = dict()


def _initialize_app(app: Dash) -> None:
    import_file_path = f'{config.import_files_root_path}{import_file_name}'
    react_file_path = f'{config.import_files_root_path}{react_file_name}'

    app.renderer = f'''
        window.__start_dash_app__ = () => new DashRenderer();

        if (window.{import_namespace})
            window.__start_dash_app__();
    '''

    app.config.external_scripts += [f'''
        "></script>
        <script type="importmap">{{ "imports": {{ "react": "{react_file_path}" }} }}</script>
        <script src="
    ''']

    @app.server.route(import_file_path)
    def get_import_file() -> Any:
        return app.server.response_class(
            response=generate_import_file(app, _initialized_components),
            status=200,
            mimetype='application/javascript')

    @app.server.route(react_file_path)
    def get_react_file() -> Any:
        return app.server.response_class(
            response=generate_react_file(),
            status=200,
            mimetype='application/javascript')

    app.config.external_scripts += [{'src': import_file_path, 'type': 'module', 'async': 'false', 'defer': 'false'}]


def _initialize_library(app: Dash, public_path: str) -> None:
    public_path_template = parse.urljoin(f'/{public_path}/', '<path:path>')

    @app.server.route(public_path_template)
    @change_function_name
    def get_public_files(path: str) -> Any:
        return send_from_directory(
            public_path,
            path,
            mimetype='application/javascript' if path.endswith('.js') else None)


def _create_component(component_key) -> Type[Component]:
    class LocalReactComponent(Component):
        unique_name = f'f_{component_key.public_path}_{component_key.file_path}_{component_key.export_name}'
        unique_name = ''.join(c if c.isalnum() else '_' for c in unique_name)

        def __init__(self, **kwargs: Any) -> None:
            self._prop_names = kwargs.keys()
            self._type = LocalReactComponent.unique_name
            self._namespace = import_namespace
            self._valid_wildcard_attributes: list = []

            super(LocalReactComponent, self).__init__(**kwargs)

    return LocalReactComponent


def load_react_component(app: Dash, public_path: str, file_path: str, export_name: str = 'default') -> Type[Component]:
    app_key = app
    library_key = LibraryKey(app, public_path)
    component_key = ComponentKey(app, public_path, file_path, export_name)

    if app_key not in _initialized_apps:
        _initialize_app(app)
        _initialized_apps.add(app_key)

    if library_key not in _initialized_libraries:
        _initialize_library(app, public_path)
        _initialized_libraries.add(library_key)

    if component_key not in _initialized_components:
        component = _create_component(component_key)
        _initialized_components[component_key] = component

    return _initialized_components[component_key]
