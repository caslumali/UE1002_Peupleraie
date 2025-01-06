# -*- coding: utf-8 -*-
# Application d'analyse interactive de données avec gestion des valeurs NULL

import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import numpy as np

# Chargement et préparation des données
df = pd.read_csv("./data_final/tableaux/df_px_filtre_dept10.csv")
df['date'] = pd.to_datetime(df['date'].astype(str),
                            errors='coerce', format='%Y')
df['year'] = df['date'].dt.year
df['age_plan'] = df['age_plan'].apply(lambda x: x if 1 <= x <= 12 else np.nan)

# Options pour les menus déroulants
cultivar_counts = df['cultivar_n'].value_counts()
sorted_cultivars = [{'label': c, 'value': c} for c in cultivar_counts.index]

# Liste des variables disponibles pour les axes
variable_options = [
    {'label': 'Âge de la plantation', 'value': 'age_plan'},
    {'label': 'Valeur', 'value': 'valeur'},
    {'label': 'CC', 'value': 'grid_CC'},
    {'label': 'ENL', 'value': 'grid_ENL'},
    {'label': 'MOCH', 'value': 'grid_MOCH'},
    {'label': 'PAI', 'value': 'grid_PAI'},
    {'label': 'VCI', 'value': 'grid_VCI'},
    {'label': 'Z_mean', 'value': 'Z_mean'},
    {'label': 'Densité', 'value': 'densite'},
    {'label': 'Date du raster', 'value': 'year'},
    {'label': 'Année de plantation', 'value': 'annee_plan'}
]

# Types de visualisations disponibles
visu_options = [
    {'label': 'Boxplot avec Nuage de Points', 'value': 'box_scatter'},
    {'label': 'Nuage de Points', 'value': 'scatter'},
    {'label': 'Heatmap', 'value': 'heatmap'},
    {'label': 'Graphique en Grille', 'value': 'facet_grid'}
]

# Styles CSS pour l'interface
controls_style = {
    'display': 'flex',
    'flexDirection': 'row',
    'flexWrap': 'wrap',
    'gap': '10px',
    'alignItems': 'center',
    'marginBottom': '10px',
    'backgroundColor': '#f8f9fa',
    'padding': '10px',
    'borderRadius': '5px'
}

dropdown_style = {
    'flex': '1',
    'minWidth': '200px',
    'maxWidth': '250px'
}

# Initialisation de l'application Dash
app = dash.Dash(__name__)
app.title = "Analyse Interactive des Indices de Confiance"

# Layout principal de l'application
app.layout = html.Div(
    style={
        'backgroundColor': 'white',
        'padding': '20px',
        'fontFamily': 'Arial, sans-serif',
        'maxWidth': '100%',
        'margin': '0 auto',
        'minHeight': '100vh'
    },
    children=[
        # En-tête
        html.H1('Analyse Interactive des Indices de Confiance',
                style={'textAlign': 'center', 'marginBottom': '20px'}),

        # Conteneur flex pour les deux graphiques
        html.Div(style={'display': 'flex', 'flexWrap': 'wrap', 'gap': '20px'}, children=[
            # Premier graphique et ses contrôles
            html.Div(style={'flex': '1', 'minWidth': '600px'}, children=[
                html.H2('Première Visualisation'),
                html.Div(style=controls_style, children=[
                    html.Div(style=dropdown_style, children=[
                        html.Label('Cultivar(s):'),
                        dcc.Dropdown(id='cultivar-dropdown-1', options=sorted_cultivars,
                                     value=[], multi=True)
                    ]),
                    html.Div(style=dropdown_style, children=[
                        html.Label('Variable X:'),
                        dcc.Dropdown(id='xaxis-dropdown-1',
                                     options=variable_options, value='age_plan')
                    ]),
                    html.Div(style=dropdown_style, children=[
                        html.Label('Variable Y:'),
                        dcc.Dropdown(id='yaxis-dropdown-1',
                                     options=variable_options, value='valeur')
                    ]),
                    html.Div(style=dropdown_style, children=[
                        html.Label('Type:'),
                        dcc.Dropdown(id='visualisation-type-1',
                                     options=visu_options, value='box_scatter')
                    ])
                ]),
                dcc.Graph(id='graphique-interactif-1',
                          style={'height': '700px'})
            ]),

            # Deuxième graphique et ses contrôles
            html.Div(style={'flex': '1', 'minWidth': '600px'}, children=[
                html.H2('Deuxième Visualisation'),
                html.Div(style=controls_style, children=[
                    html.Div(style=dropdown_style, children=[
                        html.Label('Cultivar(s):'),
                        dcc.Dropdown(id='cultivar-dropdown-2', options=sorted_cultivars,
                                     value=[], multi=True)
                    ]),
                    html.Div(style=dropdown_style, children=[
                        html.Label('Variable X:'),
                        dcc.Dropdown(id='xaxis-dropdown-2',
                                     options=variable_options, value='age_plan')
                    ]),
                    html.Div(style=dropdown_style, children=[
                        html.Label('Variable Y:'),
                        dcc.Dropdown(id='yaxis-dropdown-2',
                                     options=variable_options, value='valeur')
                    ]),
                    html.Div(style=dropdown_style, children=[
                        html.Label('Type:'),
                        dcc.Dropdown(id='visualisation-type-2',
                                     options=visu_options, value='box_scatter')
                    ])
                ]),
                dcc.Graph(id='graphique-interactif-2',
                          style={'height': '700px'})
            ])
        ])
    ]
)

# Fonction principale de génération des graphiques


def generer_graphique(df, cultivars, var_x, var_y, visu_type):
    # Vérification de la sélection des cultivars
    if not cultivars:
        return go.Figure().update_layout(
            title="Veuillez sélectionner au moins un cultivar",
            annotations=[{
                'text': "Aucun cultivar sélectionné",
                'xref': "paper",
                'yref': "paper",
                'showarrow': False,
                'font': {'size': 16}
            }]
        )

    # Filtrage des données et gestion des valeurs NULL
    df_filtre = df[df['cultivar_n'].isin(
        cultivars)].dropna(subset=[var_x, var_y])

    # Calcul des statistiques sur les points filtrés
    total_points = len(df[df['cultivar_n'].isin(cultivars)])
    points_restants = len(df_filtre)
    points_filtres = total_points - points_restants

    # Création des différents types de graphiques
    if visu_type == 'box_scatter':
        fig = px.box(df_filtre, x=var_x, y=var_y, color='cultivar_n',
                     points="all", template='simple_white', notched=True, hover_data={'unique_id': True})
        fig.update_traces(marker=dict(size=4, opacity=0.5))

    elif visu_type == 'scatter':
        fig = px.scatter(df_filtre, x=var_x, y=var_y, color='cultivar_n',
                         opacity=0.5, template='simple_white', hover_data={'unique_id': True})

    elif visu_type == 'heatmap':
        fig = px.density_heatmap(df_filtre, x=var_x, y=var_y,
                                 nbinsx=30, nbinsy=30,
                                 color_continuous_scale='Viridis')

    elif visu_type == 'facet_grid':
        unique_years = sorted(df_filtre['year'].dropna().unique())[:6]
        fig = make_subplots(rows=2, cols=3,
                            subplot_titles=[f"Année: {year}" for year in unique_years])

        for i, year in enumerate(unique_years):
            row, col = i // 3 + 1, i % 3 + 1
            df_year = df_filtre[df_filtre['year'] == year]
            fig.add_trace(
                go.Box(x=df_year[var_x], y=df_year[var_y],
                       name=f"Année {year}", boxpoints='all'),
                row=row, col=col
            )

    # Configuration du layout avec informations sur les points filtrés
    title = (f"{var_y} vs {var_x}<br>"
             f"<sup>Points total: {total_points} | "
             f"Points utilisés: {points_restants} | "
             f"Points filtrés: {points_filtres} "
             f"({(points_filtres/total_points*100):.1f}%)</sup>")

    # Mise à jour du layout général
    fig.update_layout(
        height=700,
        margin=dict(l=50, r=50, t=70, b=50),
        title=title,
        title_x=0.5,
        legend=dict(orientation='h', yanchor='bottom',
                    y=1.02, xanchor='right', x=1)
    )

    # Ajout des lignes verticales pour l'âge de plantation
    if var_x == 'age_plan':
        for i in range(1, 13):
            fig.add_vline(x=i-0.5, line=dict(dash='dash',
                                             color='gray', width=0.5))

    return fig

# Callback pour la mise à jour des graphiques


@app.callback(
    [Output('graphique-interactif-1', 'figure'),
     Output('graphique-interactif-2', 'figure')],
    [Input('cultivar-dropdown-1', 'value'),
     Input('xaxis-dropdown-1', 'value'),
     Input('yaxis-dropdown-1', 'value'),
     Input('visualisation-type-1', 'value'),
     Input('cultivar-dropdown-2', 'value'),
     Input('xaxis-dropdown-2', 'value'),
     Input('yaxis-dropdown-2', 'value'),
     Input('visualisation-type-2', 'value')]
)
def update_graphs(cultivars1, x1, y1, type1,
                  cultivars2, x2, y2, type2):
    return (
        generer_graphique(df, cultivars1, x1, y1, type1),
        generer_graphique(df, cultivars2, x2, y2, type2)
    )


# Lancement du serveur
if __name__ == '__main__':
    app.run_server(debug=True, host='127.0.0.1', port=8050)
