import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
import dash_bootstrap_components as dbc

# Carregue o arquivo Excel em um DataFrame do pandas
df = pd.read_excel("C:\\Users\\baptista.leonardo\\Downloads\\DadosFipe.xlsx")

# Inicialize o aplicativo Dash
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)

# Layout do aplicativo
app.layout = html.Div([
    html.H1("Análises de Veículos", style={'text-align': 'center', 'margin-bottom': '20px'}),

    # Links para as páginas
    dcc.Link('Dashboard de Preços', href='/',
             style={'margin-right': '10px', 'color': 'blue', 'text-decoration': 'none'}),
    dcc.Link('Top N Veículos', href='/topn',
             style={'margin-right': '10px', 'color': 'blue', 'text-decoration': 'none'}),
    dcc.Link('Evolução de Preços', href='/evolucao',
             style={'margin-right': '10px', 'color': 'blue', 'text-decoration': 'none'}),

    # Conteúdo da página atual
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content', style={'margin-top': '20px'})
])

# Função para renderizar páginas diferentes com base no URL
@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/topn':
        return render_dashboard_topn()
    elif pathname == '/evolucao':
        return render_dashboard_evolucao()
    else:
        return render_dashboard_precos()

# Função para renderizar dashboards específicos
def render_dashboard_precos():
    return html.Div([
        html.H2("Dashboard de Preços", style={'text-align': 'center'}),
        dcc.Dropdown(
            id='dropdown-marca',
            options=[{'label': marca, 'value': marca} for marca in df['marca'].unique()],
            value=[df['marca'].unique()[0]],
            multi=True,
            placeholder="Selecione a(s) marca(s)"
        ),
        dcc.Graph(id='scatter-plot'),
    ])

def render_dashboard_topn():
    return dbc.Container([
        html.H1("Top N Vehicles Dashboard", style={'text-align': 'center', 'margin-bottom': '20px'}),

        # Dropdown for selecting brand
        dcc.Dropdown(
            id='dropdown-marca-topn',
            options=[{'label': marca, 'value': marca} for marca in df['marca'].unique()],
            value=[df['marca'].unique()[0]],
            multi=True,
            placeholder="Select a brand"
        ),

        # Input for selecting top N vehicles
        dcc.Input(
            id='input-topn',
            type='number',
            value=5,
            min=1,
            max=len(df),
            step=1,
            placeholder="Enter top N"
        ),

        # Display information about top N vehicles
        html.Div(id='topn-vehicles-info')
    ])

def render_dashboard_evolucao():
    return dbc.Container([
        html.H1("Evolução de Preços por Mês", style={'text-align': 'center', 'margin-bottom': '20px'}),

        # Dropdown for selecting brand
        dcc.Dropdown(
            id='dropdown-marca-evolucao',
            options=[{'label': marca, 'value': marca} for marca in df['marca'].unique()],
            value=df['marca'].unique()[0],
            multi=True,
            placeholder="Select a brand"
        ),

        # Dropdown for selecting models within the chosen brand
        dcc.Dropdown(
            id='dropdown-modelo-evolucao',
            multi=True,
            placeholder="Select model(s)"
        ),

        # Dropdown for selecting the year of the model
        dcc.Dropdown(
            id='dropdown-ano-modelo-evolucao',
            options=[{'label': ano, 'value': ano} for ano in df['anomodelo'].unique()],
            value=df['anomodelo'].unique()[0],
            multi=False,
            placeholder="Select a model year"
        ),

        # Graph for displaying price evolution
        dcc.Graph(id='evolucao-plot'),
    ])

# Callback to update model dropdown based on selected brand
@app.callback(
    Output('dropdown-modelo-evolucao', 'options'),
    [Input('dropdown-marca-evolucao', 'value')]
)
def update_model_dropdown(selected_marca):
    filtered_df = df[df['marca'].isin(selected_marca)]
    return [{'label': modelo, 'value': modelo} for modelo in filtered_df['modelo'].unique()]

@app.callback(
    Output('dropdown-modelo-evolucao', 'value'),
    [Input('dropdown-marca-evolucao', 'value')]
)

# Callback para atualizar o gráfico de evolução de preços com base nos filtros
@app.callback(
    Output('evolucao-plot', 'figure'),
    [Input('dropdown-marca-evolucao', 'value'),
     Input('dropdown-modelo-evolucao', 'value'),
     Input('dropdown-ano-modelo-evolucao', 'value')]
)
def update_evolucao_plot(selected_marca, selected_modelo, selected_ano_modelo):
    filtered_df = df[df['marca'].isin(selected_marca)]
    filtered_df = filtered_df[filtered_df['modelo'].isin(selected_modelo)]
    filtered_df = filtered_df[filtered_df['anomodelo'] == selected_ano_modelo]

    fig = px.line()

    for modelo in selected_modelo:
        filtered_df_modelo = filtered_df[filtered_df['modelo'] == modelo]
        fig.add_trace(
            go.Scatter(
                x=['setembro', 'outubro', 'novembro'],
                y=filtered_df_modelo[['setembro', 'outubro', 'novembro']].values.flatten(),
                mode='lines',
                name=modelo
            )
        )

    fig.update_layout(
        title=f'Evolução de Preços por Mês - {selected_marca}',
        xaxis=dict(title='Mês'),
        yaxis=dict(title='Preço'),
        hovermode='closest'
    )

    return fig


# Callback para atualizar a informação exibida com base na marca e no top N
@app.callback(
    Output('topn-vehicles-info', 'children'),
    [Input('dropdown-marca-topn', 'value'),
     Input('input-topn', 'value')]
)
def update_topn_info(selected_marca, topn):
    filtered_df = df[df['marca'].isin(selected_marca)].nlargest(topn, 'novembro')

    if not filtered_df.empty:
        table = dbc.Table.from_dataframe(filtered_df, striped=True, bordered=True, hover=True)
        return table
    else:
        return "No data available for the selected brand and top N."


# Callback para atualizar o gráfico de dispersão com base nos filtros
@app.callback(
    Output('scatter-plot', 'figure'),
    [Input('dropdown-marca', 'value')]
)
def update_scatter_plot(selected_marca):
    filtered_df = df[df['marca'].isin(selected_marca)]

    fig = px.scatter(filtered_df, x='anomodelo', y='novembro', color='marca', size='novembro',
                     title='Preços de Veículos por Ano e Marca',
                     labels={'anomodelo': 'Ano do Modelo', 'novembro': 'Preço em Novembro'},
                     hover_name='modelo')

    return fig


# Execute o aplicativo
if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=8050)
