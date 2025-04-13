import dash
from dash import html

app = dash.Dash(__name__)
server = app.server

app.layout = html.Div([
    html.H1("Hello from Bologna Airport App 🚀")
])

if __name__ == "__main__":
    app.run_server(debug=True)
