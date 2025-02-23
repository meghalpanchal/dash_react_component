from typing import Dict, Type
from dash import Dash  # type: ignore
from dash.development.base_component import Component  # type: ignore
from ._common import import_namespace
from ._types import ComponentKey
from ._config import config


def _generate_component_import_file(public_path: str, file_path: str, export_name: str, component_name: str) -> str:
    relative_import_levels = config.import_files_root_path.count('/') - 1
    relative_public_path = '../' * relative_import_levels + public_path

    return f'''
        import {{{export_name} as {component_name}}} from "./{relative_public_path}/{file_path}";
        {import_namespace}["{component_name}"] = {component_name}
    '''


def generate_import_file(app: Dash, components: Dict[ComponentKey, Type[Component]]) -> str:
    header = f'''
        const {import_namespace} = {{}};
    '''

    footer = f'''
        window.{import_namespace} = {import_namespace};

        if (window.__start_dash_app__)
            window.__start_dash_app__();
    '''

    component_imports = [
        _generate_component_import_file(public_path, file_path, export_name, component.unique_name)
        for (component_app, public_path, file_path, export_name), component in components.items()
        if component_app is app
    ]

    return header + '\n'.join(component_imports) + footer


def generate_react_file():
    return '''
        React = window.React;
        export default React;
    '''
