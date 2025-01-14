# Importation des bibliothèques nécessaires
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import numpy as np

# Charger les données
df = pd.read_csv("./data_final/tableaux/df_pixel_filtre_dept10.csv")

# Pré-traitement des données
df['date'] = pd.to_datetime(df['date'].astype(str),
                            errors='coerce', format='%Y')
df['year'] = df['date'].dt.year  # Extraire uniquement l'année

# Limiter les valeurs de 'age_plan' entre 1 et 12
df['age_plan'] = df['age_plan'].apply(lambda x: x if 1 <= x <= 12 else np.nan)

# Trier les cultivars par nombre de pixels par ordre décroissant
cultivar_counts = df['cultivar_n'].value_counts()
sorted_cultivars = [{'label': cultivar, 'value': cultivar}
                    for cultivar in cultivar_counts.index]

# Initialiser l'application Dash
app = dash.Dash(__name__)
app.title = "Analyse Interactive des Indices de Confiance"

# Définir le style et la disposition de l'application
app.layout = html.Div(
    style={
        'backgroundColor': 'white',
        'padding': '5px',
        'fontFamily': 'Arial, sans-serif'
    },
    children=[
        html.H1('Analyse Interactive des Indices de Confiance',
                style={'color': 'black', 'textAlign': 'center'}),

        # Conteneur pour les sélections
        html.Div(
            style={'display': 'flex', 'flexWrap': 'wrap',
                   'justifyContent': 'space-between', 'gap': '10px'},
            children=[
                # Sélection du Cultivar
                html.Div([
                    html.Label('Sélectionnez le(s) Cultivar(s):', style={
                        'color': 'black', 'fontWeight': 'bold'}),
                    dcc.Dropdown(
                        id='cultivar-dropdown',
                        options=sorted_cultivars,  # Utilise les cultivars ordonnés
                        value=[],  # Aucun cultivar sélectionné par défaut
                        multi=True,
                        placeholder="Sélectionnez un ou plusieurs cultivars",
                        style={'backgroundColor': 'white', 'color': 'black'}
                    )
                ], style={'width': '30%', 'minWidth': '250px'}),

                # Sélection de la variable pour l'axe X
                html.Div([
                    html.Label('Sélectionnez la variable pour l\'axe X:', style={
                        'color': 'black', 'fontWeight': 'bold'}),
                    dcc.Dropdown(
                        id='xaxis-dropdown',
                        options=[
                            {'label': 'Âge de la plantation', 'value': 'age_plan'},
                            {'label': 'Valeur', 'value': 'valeur'},
                            {'label': 'CC', 'value': 'grid_CC'},
                            {'label': 'ENL', 'value': 'grid_ENL'},
                            {'label': 'MOCH', 'value': 'grid_MOCH'},
                            {'label': 'PAI', 'value': 'grid_PAI'},
                            {'label': 'VCI', 'value': 'grid_VCI'},
                            {'label': 'Densité', 'value': 'densite'},
                            {'label': 'Date du raster', 'value': 'year'},
                            {'label': 'Année de plantation', 'value': 'annee_plan'}
                        ],
                        value='age_plan',
                        style={'backgroundColor': 'white', 'color': 'black'}
                    )
                ], style={'width': '30%', 'minWidth': '250px'}),

                # Sélection de la variable pour l'axe Y
                html.Div([
                    html.Label('Sélectionnez la variable pour l\'axe Y:', style={
                        'color': 'black', 'fontWeight': 'bold'}),
                    dcc.Dropdown(
                        id='yaxis-dropdown',
                        options=[
                            {'label': 'Âge de la plantation', 'value': 'age_plan'},
                            {'label': 'Valeur', 'value': 'valeur'},
                            {'label': 'CC', 'value': 'grid_CC'},
                            {'label': 'ENL', 'value': 'grid_ENL'},
                            {'label': 'MOCH', 'value': 'grid_MOCH'},
                            {'label': 'PAI', 'value': 'grid_PAI'},
                            {'label': 'VCI', 'value': 'grid_VCI'},
                            {'label': 'Densité', 'value': 'densite'},
                            {'label': 'Date du raster', 'value': 'year'},
                            {'label': 'Année de plantation', 'value': 'annee_plan'}
                        ],
                        value='valeur',
                        style={'backgroundColor': 'white', 'color': 'black'}
                    )
                ], style={'width': '30%', 'minWidth': '250px'}),
            ]
        ),

        # Sélection du type de visualisation
        html.Div([
            html.Label('Sélectionnez le type de visualisation:',
                       style={'color': 'black', 'fontWeight': 'bold'}),
            dcc.RadioItems(
                id='visualisation-type',
                options=[
                    {'label': 'Boxplot avec Nuage de Points', 'value': 'box_scatter'},
                    {'label': 'Nuage de Points', 'value': 'scatter'},
                    {'label': 'Heatmap', 'value': 'heatmap'},
                    {'label': 'Graphique en Grille (Facettes)',
                     'value': 'facet_grid'}
                ],
                value='box_scatter',
                labelStyle={'display': 'block', 'color': 'black'},
                style={'marginTop': '0px'}
            )
        ], style={'marginTop': '20px'}),

        # Graphique interactif
        html.Div([
            dcc.Graph(id='graphique-interactif',
                      style={'width': '100%', 'height': '900px'})
        ], style={'marginTop': '50px', 'width': '100%'})
    ]
)

# Callback pour mettre à jour le graphique


@app.callback(
    Output('graphique-interactif', 'figure'),
    [
        Input('cultivar-dropdown', 'value'),
        Input('xaxis-dropdown', 'value'),
        Input('yaxis-dropdown', 'value'),
        Input('visualisation-type', 'value')
    ]
)
def update_graph(cultivars_selectionnes, variable_x, variable_y, type_visualisation):
    if not cultivars_selectionnes:
        return {
            'data': [],
            'layout': go.Layout(
                title="Veuillez sélectionner au moins un cultivar pour afficher le graphique.",
                xaxis={'visible': False},
                yaxis={'visible': False},
                annotations=[
                    {
                        'text': "Aucun cultivar sélectionné.",
                        'xref': "paper",
                        'yref': "paper",
                        'showarrow': False,
                        'font': {'size': 20}
                    }
                ],
                paper_bgcolor='white',
                plot_bgcolor='white'
            )
        }

    # Filtrer les données pour les cultivars sélectionnés et retirer les valeurs manquantes sur l'axe Y
    df_filtre = df[df['cultivar_n'].isin(
        cultivars_selectionnes)].dropna(subset=[variable_y])

    # Créer toutes les combinaisons possibles de 'year' et 'age_plan' pour garantir l'affichage de 1 à 12
    all_years = df['year'].dropna().unique()
    all_age_plans = range(1, 13)
    combinations = pd.MultiIndex.from_product([all_years, all_age_plans], names=[
        'year', 'age_plan']).to_frame(index=False)

    # Mesclar les combinaisons pour s'assurer de la présence de toutes les valeurs d'âge
    df_filtre = combinations.merge(
        df_filtre, on=['year', 'age_plan'], how='left')

    # ====================================================
    # Graphique en Grille (Facettes)
    # ====================================================
    if type_visualisation == 'facet_grid':
        unique_facets = sorted(df_filtre['year'].dropna().unique())[:6]
        fig = make_subplots(
            rows=2, cols=3,
            subplot_titles=[f"Année: {facet}" for facet in unique_facets],
            horizontal_spacing=0.05, vertical_spacing=0.2
        )
        for i, facet in enumerate(unique_facets):
            row = i // 3 + 1
            col = i % 3 + 1
            df_facet = df_filtre[df_filtre['year'] == facet]
            box = go.Box(
                x=df_facet[variable_x],
                y=df_facet[variable_y],
                name=f"Année {facet}",
                boxpoints='all',
                notched=True,
                jitter=0.5,
                pointpos=0,
                marker=dict(size=4, opacity=0.6),
                line=dict(width=1),
                showlegend=False,
                hovertext=df_facet['unique_id']
            )
            fig.add_trace(box, row=row, col=col)
            fig.update_xaxes(
                title_text=variable_x.capitalize(),
                row=row, col=col,
                tickvals=list(
                    range(1, 13)) if variable_x == 'age_plan' else None,
                range=[1, 12],
                autorange=True
            )
            fig.update_yaxes(
                title_text=variable_y.capitalize(),
                row=row, col=col,
                autorange=True
            )

        fig.update_layout(
            height=700,
            title_text=f"{variable_y.capitalize()} en fonction de {variable_x.capitalize()} par Année",
            template='simple_white',
            title_x=0.5
        )

    # ====================================================
    # Démarche pour les autres types de visualisation
    # ====================================================
    else:
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # 1) BOX + SCATTER (nuage de points) avec box coloré par 'cultivar_n' et points par 'source'
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        if type_visualisation == 'box_scatter':
            # --- Boxplot "Clean" : pas de points, coloré par cultivar_n
            box_fig = px.box(
                df_filtre,
                x=variable_x,
                y=variable_y,
                color='cultivar_n',          # couleur de la boîte par cultivar
                template='simple_white',
                title=f"{variable_y.capitalize()} en fonction de {variable_x.capitalize()}",
                category_orders={variable_x: list(
                    range(1, 13))} if variable_x == 'age_plan' else {},
                notched=True,                # notch activé
                # <--- IMPORTANT : pas de points (dans px.box, utilisez False)
                points=False,
                hover_data={'unique_id': True}
            )

            # --- Nuage de points coloré par 'source' (départements)
            strip_fig = px.strip(
                df_filtre,
                x=variable_x,
                y=variable_y,
                color='source',              # couleur des points par département
                template='simple_white',
                hover_data=['unique_id', 'source']
            )
            # Ajuster la position des points (légers déplacements)
            strip_fig.update_traces(
                jitter=0.5,
                pointpos=-0.8,  # diffusion horizontale
                marker=dict(size=5, opacity=0.7)
            )

            # --- Combiner les deus figures
            fig = go.Figure(data=box_fig.data + strip_fig.data)
            # Copier layout du box_fig (titre, axys, etc)
            fig.update_layout(box_fig.layout)

        elif type_visualisation == 'scatter':
            fig = px.scatter(
                df_filtre,
                x=variable_x,
                y=variable_y,
                color='cultivar_n',
                opacity=0.7,
                hover_data=['unique_id', 'source'],
                template='simple_white',
                title=f"{variable_y.capitalize()} en fonction de {variable_x.capitalize()}"
            )

        elif type_visualisation == 'heatmap':
            fig = px.density_heatmap(
                df_filtre,
                x=variable_x,
                y=variable_y,
                nbinsx=30,
                nbinsy=30,
                color_continuous_scale='Viridis',
                template='simple_white',
                title=f"Heatmap de {variable_y.capitalize()} en fonction de {variable_x.capitalize()}"
            )

        # Ajustements généraux de la mise en page
        fig.update_layout(
            height=900,
            xaxis=dict(
                tickmode='array',
                tickvals=list(
                    range(1, 13)) if variable_x == 'age_plan' else None,
                range=[1, 12] if variable_x == 'age_plan' else None,
                autorange=True
            ),
            yaxis=dict(autorange=True),
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(color='black'),
            margin=dict(l=20, r=20, t=50, b=20),
            legend_title_text='Cultivar',
            title_x=0.5
        )

    # Si 'age_plan' sur l'axe X, ajoutez des lignes verticales entre chaque âge
    if variable_x == 'age_plan':
        for i in range(1, 13):
            fig.add_vline(
                x=i - 0.5,
                line=dict(dash='dash', color='black', width=1)
            )

    return fig


# Exécuter l'application
if __name__ == '__main__':
    app.run_server(debug=True, host='127.0.0.1', port=8050)
