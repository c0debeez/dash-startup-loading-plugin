from dash import Dash, html

from dash_startup_loading_plugin import setup

setup(
    loader="analyzing-image"
)  # Initialize the startup loading plugin. Not necessary to import it only if you want to customize the loader.


app = Dash(__name__)


app.layout = html.Main(
    [
        html.H1("My Dash App"),
        html.P("The startup loading plugin will automatically hide once the layout is fully loaded."),
    ]
)

if __name__ == "__main__":
    app.run(debug=True)
