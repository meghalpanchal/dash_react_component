import dash
from dash import dcc, html
from local_dash_local_react_components import load_react_component

app = dash.Dash(
    __name__, external_scripts=["https://cdn.tailwindcss.com", "public/tailwinds.js"]
)

# Load the custom component
CustomComponent = load_react_component(app, "public", "Navbar.js")

# Use the custom component in a layout
app.layout = html.Div([CustomComponent(id="meghamenu")])

if __name__ == "__main__":
    app.run_server(debug=True, port=8054)
