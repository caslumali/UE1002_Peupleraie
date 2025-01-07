# Importation des bibliothèques
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors


# * ======================================= * #
# * ======================================= * #
#        Fonctions pour le plottage         * #
# * ======================================= * #
# * ======================================= * #

def top_cultivars(df, max_age=12, min_years=6, top_n=20):
    """
    Sélectionne les 'top_n' cultivars les plus représentatifs en fonction du nombre de pixels.

    Args:
        df (DataFrame): Le DataFrame contenant les données des cultivars.
        max_age (int): Âge maximum des plantations à inclure (par défaut 12).
        min_years (int): Nombre minimum d'années avec des données pour un cultivar (par défaut 6).
        top_n (int): Nombre de cultivars à sélectionner (par défaut 20).

    Returns:
        dict: Un dictionnaire trié avec les cultivars valides et leur nombre de pixels.
    """
    # Filtrer les données par âge de la plantation
    df_filtered = df[(df['age_plan'] > 1) & (df['age_plan'] <= max_age)]

    # Compter le nombre de pixels (occurrences) pour chaque cultivar
    counts = df_filtered['cultivar_n'].value_counts()

    # Sélectionner les 'top_n' cultivars les plus représentatifs
    top_cultivars = counts.nlargest(top_n)

    # Filtrer uniquement les cultivars ayant des données pour au moins 'min_years' années
    valid_cultivars = {cultivar: count for cultivar, count in top_cultivars.items()
                       if df_filtered[df_filtered['cultivar_n'] == cultivar]['age_plan'].nunique() >= min_years}

    # Trier par nombre de pixels (décroissant) et retourner
    return valid_cultivars


def boxnotch_confidenceXage(df, cultivar, index, output_path, color_map=None, pdf=None):
    """
    Génère un boxplot avec encoches pour un cultivar donné, en ajoutant des statistiques et des points colorés.

    Args:
        df (DataFrame): Le DataFrame contenant les données filtrées.
        cultivar (str): Le nom du cultivar à analyser.
        index (int): L'index pour nommer et ordonner les fichiers de sortie.
        output_path (str): Le chemin du dossier pour sauvegarder l'image générée.
        color_map (dict, optional): Un dictionnaire associant chaque 'source' à une couleur spécifique.
        pdf (PdfPages, optional): Un objet PdfPages pour sauvegarder le graphique dans un fichier PDF combiné.

    Returns:
        None: Sauvegarde l'image du boxplot en PNG et dans le PDF si spécifié.
    """
    # Filtrer le DataFrame pour le cultivar sélectionné et éliminer les valeurs manquantes
    df_cultivar = df[df['cultivar_n'] == cultivar].dropna(
        subset=['age_plan', 'valeur'])
    if df_cultivar.empty:
        print(
            f"Aucune donnée pour le cultivar '{cultivar}', graphique non généré.")
        return

    # Définir les catégories d'âge (1 à 12 ans)
    age_categories = list(range(1, 13))
    df_cultivar['age_plan'] = pd.Categorical(
        df_cultivar['age_plan'], categories=age_categories, ordered=True)

    # Préparer les données pour le boxplot (une liste pour chaque catégorie d'âge)
    data = [df_cultivar[df_cultivar['age_plan'] == age]['valeur']
            for age in age_categories]

    # Configuration de la figure et de l'axe
    fig, ax = plt.subplots(figsize=(16, 8), facecolor='white')
    # Ligne horizontale de référence
    ax.axhline(y=50, color='black', linestyle='--', linewidth=0.5)

    # Positions des catégories
    positions = np.arange(1, len(age_categories) + 1)
    boxplot_positions = positions + 0.25  # Décalage du boxplot vers la droite

    # Création du boxplot avec ses propriétés esthétiques
    bp = ax.boxplot(
        data,
        notch=True,
        positions=boxplot_positions,
        patch_artist=True,  # Permet de colorer l'intérieur du boxplot
        widths=0.4,
        showfliers=False,  # Cache les valeurs aberrantes
        # Style de la médiane
        medianprops=dict(color="#051512", linewidth=1.5),
        # Style des moustaches
        whiskerprops=dict(color="#051512", linewidth=1.2),
        # Style des extrémités des moustaches
        capprops=dict(color="#051512", linewidth=1.2),
        boxprops=dict(facecolor="#1e7b6f", color="#0a2925",
                      alpha=0.8)  # Style de la boîte
    )

    # Ajouter les points individuels décalés vers la gauche
    for i, age in enumerate(age_categories):
        subset = df_cultivar[df_cultivar['age_plan'] == age]
        if subset.empty:
            continue
        # Position décalée à gauche
        x = np.random.normal(positions[i] - 0.25, 0.05, size=len(subset))
        y = subset['valeur']
        colors = [color_map.get(src, "grey") for src in subset['source']]
        ax.scatter(x, y, c=colors, s=20, alpha=0.7,
                   edgecolor="lightgrey", linewidth=0.5)

    # Afficher 'NA' lorsque les données sont absentes pour une catégorie
    for i, age in enumerate(age_categories):
        if df_cultivar[df_cultivar['age_plan'] == age]['valeur'].empty:
            ax.text(positions[i], 50, 'NA', ha='center', va='center',
                    color='red', fontsize=14, fontweight='bold')

    # Ajouter les métriques statistiques sous l'axe X
    for i, age in enumerate(age_categories):
        subset = df_cultivar[df_cultivar['age_plan'] == age]['valeur']
        if subset.empty:
            continue
        mean_val = subset.mean()
        median_val = subset.median()
        std_val = subset.std()
        count = len(subset)

        # Texte des statistiques
        ax.text(positions[i], 8, f"Nb={count}",
                ha='center', va='center', fontsize=8, color="darkblue")
        ax.text(positions[i], 6, f"Moy={mean_val:.1f}",
                ha='center', va='center', fontsize=8, color="darkblue")
        ax.text(positions[i], 4, f"Med={median_val:.1f}",
                ha='center', va='center', fontsize=8, color="darkblue")
        ax.text(positions[i], 2, f" σ = {std_val:.1f}",
                ha='center', va='center', fontsize=8, color="darkblue")

    # Ajustement des ticks et des étiquettes de l'axe X
    ax.set_xticks(positions)
    ax.set_xticklabels([str(age) for age in age_categories], fontsize=12)
    ax.set_xlim(0.5, len(age_categories) + 0.5)

    # Ajouter la légende pour les 'source'
    handles = [plt.Line2D([0], [0], marker='o', color=color, linestyle='None', markersize=8, label=source)
               for source, color in color_map.items()]
    ax.legend(handles=handles, title='Départament',
              loc='upper left', bbox_to_anchor=(1, 1))

    # Lignes verticales pour séparer les catégories
    for pos in positions + 0.5:
        plt.axvline(x=pos, color='grey', linestyle=':', linewidth=0.6)

    # Titres et étiquettes des axes
    plt.title(
        f"Incertitude de classification selon l'âge pour le cultivar {cultivar}", fontsize=16, weight='bold', pad=30)
    plt.xlabel("Âge de la plantation (années)", fontsize=14)
    plt.ylabel("Probabilité d’appartenance (%)", fontsize=14)
    plt.ylim(0, 102)

    # Sauvegarder la figure en PNG
    cultivar_safe = cultivar.replace("/", "_")
    filename = f"{index:02d}_{cultivar_safe}.png"
    plt.savefig(os.path.join(output_path, filename),
                bbox_inches="tight", dpi=300)

    # Sauvegarder dans un PDF si disponible
    if pdf is not None:
        pdf.savefig(fig)

    plt.close(fig)
    print(
        f"Boxplot pour le cultivar '{cultivar}' sauvegardé sous le nom '{filename}'.")


def grid_boxnotch_confidenceXage_par_anne(df, cultivar, output_path, color_palette, index, pdf=None):
    """
    Génère une grille de boxplots par année pour un cultivar donné, affichant les valeurs par âge de plantation.

    Args:
        df (DataFrame): Le DataFrame contenant les données filtrées.
        cultivar (str): Le nom du cultivar à analyser.
        output_path (str): Le chemin du dossier pour sauvegarder les images générées.
        color_palette (dict): Un dictionnaire associant chaque année à une couleur spécifique.
        index (int): L'index pour nommer et ordonner les fichiers de sortie.
        pdf (PdfPages, optional): Un objet PdfPages pour sauvegarder les graphiques dans un fichier PDF combiné.

    Returns:
        None: Sauvegarde une grille de boxplots en PNG et dans le PDF si spécifié.
    """
    # Définir les catégories d'âges de plantation
    age_categories = list(range(1, 13))

    # Initialiser la figure avec une grille 2x3 pour les années, taille ajustée pour maximiser l'utilisation de l'espace
    fig, axes = plt.subplots(2, 3, figsize=(16, 9), facecolor='white')
    axes = axes.flatten()  # Aplatir pour itérer facilement

    for i, year in enumerate(sorted(df['date'].unique())):
        # Filtrer les données pour l'année et le cultivar sélectionnés
        df_year = df[(df['date'] == year) & (df['cultivar_n'] == cultivar)].dropna(
            subset=['age_plan', 'valeur'])

        # Préparer les données par catégorie d'âge
        data = [df_year[df_year['age_plan'] == age]['valeur']
                for age in age_categories]

        # Vérifier s'il y a des données pour l'année sélectionnée
        if df_year.empty:
            continue

        # Positions pour décaler les boxplots et les points
        # Décaler les boxplots vers la gauche
        boxplot_positions = np.arange(1, len(age_categories) + 1) - 0.25
        # Décaler les points vers la droite
        points_positions = np.arange(1, len(age_categories) + 1) + 0.25

        # Obtenir la couleur pour l'année et une version plus foncée
        year_color = color_palette.get(year, "grey")
        # Couleur légèrement plus foncée
        darker_color = mcolors.to_rgb(year_color) * np.array([0.8, 0.8, 0.8])

        # Créer le boxplot avec des paramètres spécifiques de couleur
        bp = axes[i].boxplot(
            data,
            notch=True,
            positions=boxplot_positions,
            patch_artist=True,
            widths=0.4,
            showfliers=False,
            # Couleur plus foncée pour la médiane
            medianprops=dict(color=darker_color, linewidth=1.5),
            # Couleur plus foncée pour les moustaches
            whiskerprops=dict(color=darker_color, linewidth=1.2),
            capprops=dict(color=darker_color, linewidth=1.2),
            boxprops=dict(facecolor=year_color, color=darker_color, alpha=0.7)
        )

        # Superposer les points individuels avec la couleur de l'année
        for j, age in enumerate(age_categories):
            y = df_year[df_year['age_plan'] == age]['valeur']
            if y.empty:
                # Afficher 'NA' en rouge au centre
                axes[i].text(
                    boxplot_positions[j] + 0.25, 20, 'NA', ha='center', va='center', color='lightcoral',
                    fontsize=14, fontweight='bold'
                )
            else:
                # Générer des positions x légèrement décalées et appliquer la couleur de l'année
                x = np.random.normal(points_positions[j], 0.05, size=len(y))
                axes[i].plot(x, y, 'o', color=year_color,
                             markersize=3, alpha=0.4)

        # Configurer les axes pour une échelle uniforme
        axes[i].set_title(f"Année {year}", fontsize=14, weight='bold')
        axes[i].set_xticks(range(1, 13))
        axes[i].set_xticklabels([str(age)
                                for age in age_categories], fontsize=10)
        axes[i].set_xlim(0.5, 12.5)
        axes[i].set_ylim(0, 102)

        # Ajouter des lignes verticales pour séparer les catégories
        for pos in np.arange(1.5, len(age_categories) + 0.5):
            axes[i].axvline(x=pos, color='grey', linestyle=':', linewidth=0.6)

    # Ajuster les positions des étiquettes X et Y avec un léger décalage
    fig.suptitle(
        f"Incertitude de classification par âge pour le cultivar {cultivar}", fontsize=16, weight='bold')
    fig.supxlabel("Âge de la plantation (années)", fontsize=14, y=0.03)
    fig.supylabel("Probabilité d’appartenance (%)", fontsize=14, x=0.04)

    # Ajuster l'espace entre les sous-graphiques
    plt.subplots_adjust(left=0.08, right=0.95, top=0.88,
                        bottom=0.12, wspace=0.3, hspace=0.3)

    # Sauvegarder le graphique avec un numéro de classement en ordre décroissant
    filename = f"{index:02d}_{cultivar.replace('/', '_')}_grille.png"
    plt.savefig(os.path.join(output_path, filename),
                bbox_inches="tight", dpi=300)

    # Sauvegarder dans le PDF si l'objet pdf est fourni
    if pdf is not None:
        pdf.savefig(fig)
    plt.close(fig)
    print(
        f"Grille de boxplots pour le cultivar '{cultivar}' sauvegardée sous le nom '{filename}'.")


def boxnotch_lidar_metrics(df, cultivar, metric, color_map, y_limits, pdf, output_path, cultivar_index):
    """
    Génère un boxplot avec encoches et nuage de points pour une métrique Lidar donnée en fonction de l'âge de plantation.
    Sauvegarde le graphique dans un PDF et en PNG individuellement avec un index basé sur le cultivar.

    Args:
        df (DataFrame): Le DataFrame contenant les données filtrées.
        cultivar (str): Le nom du cultivar à analyser.
        metric (str): La métrique Lidar à analyser.
        color_map (dict): Un dictionnaire associant chaque 'source' à une couleur spécifique.
        y_limits (tuple): Les limites de l'axe Y pour la métrique en cours.
        pdf (PdfPages): Un objet PdfPages pour sauvegarder le graphique dans un fichier PDF combiné.
        output_path (str): Le chemin du dossier pour sauvegarder les fichiers PNG individuels.
        cultivar_index (int): L'index basé sur le cultivar.

    Returns:
        None: Sauvegarde les graphiques dans le PDF et en PNG.
    """
    # Dictionnaire des noms complets des métriques Lidar
    metric_names = {
        "grid_CC": "Canopy Cover (CC)",
        "grid_PAI": "Plant Area Index (PAI)",
        "grid_ENL": "Effective Number of Layers (ENL)",
        "grid_VCI": "Vertical Canopy Index (VCI)",
        "grid_MOCH": "Mean Overstory Canopy Height (MOCH)"
    }

    # Obtenir le nom complet de la métrique
    metric_full_name = metric_names.get(metric, metric)

    # Filtrer le DataFrame pour le cultivar sélectionné et éliminer les valeurs manquantes
    df_cultivar = df[df['cultivar_n'] == cultivar].dropna(
        subset=['age_plan', metric])
    if df_cultivar.empty:
        print(
            f"Aucune donnée pour le cultivar '{cultivar}' et la métrique '{metric}', graphique non généré.")
        return

    # Définir les catégories d'âge (1 à 12 ans)
    age_categories = list(range(1, 13))
    df_cultivar['age_plan'] = pd.Categorical(
        df_cultivar['age_plan'], categories=age_categories, ordered=True)

    # Préparer les données pour le boxplot (une liste pour chaque catégorie d'âge)
    data = [df_cultivar[df_cultivar['age_plan'] == age][metric]
            for age in age_categories]

    # Configuration de la figure et de l'axe
    fig, ax = plt.subplots(figsize=(16, 8), facecolor='white')

    # Calculer le milieu du graphique Y
    mid_y = (y_limits[0] + y_limits[1]) / 2

    # Traçar a linha horizontal no meio do gráfico
    ax.axhline(y=mid_y, color='black', linestyle='--', linewidth=0.5)

    # Positions des catégories
    positions = np.arange(1, len(age_categories) + 1)
    boxplot_positions = positions + 0.25  # Décalage du boxplot vers la droite

    # Création du boxplot avec ses propriétés esthétiques
    bp = ax.boxplot(
        data,
        notch=True,
        positions=boxplot_positions,
        patch_artist=True,  # Permet de colorer l'intérieur du boxplot
        widths=0.4,
        showfliers=False,  # Cache les valeurs aberrantes
        # Style de la médiane
        medianprops=dict(color="#051512", linewidth=1.5),
        # Style des moustaches
        whiskerprops=dict(color="#051512", linewidth=1.2),
        # Style des extrémités des moustaches
        capprops=dict(color="#051512", linewidth=1.2),
        boxprops=dict(facecolor="#1e7b6f", color="#0a2925",
                      alpha=0.8)  # Style de la boîte
    )

    # Ajouter les points individuels décalés vers la gauche
    for i, age in enumerate(age_categories):
        subset = df_cultivar[df_cultivar['age_plan'] == age]
        if subset.empty:
            # Afficher 'NA' si aucune donnée pour cette catégorie d'âge
            ax.text(positions[i], mid_y, 'NA', ha='center', va='center',
                    color='red', fontsize=14, fontweight='bold')
            continue

        # Générer des positions légèrement décalées
        x = np.random.normal(positions[i] - 0.25, 0.05, size=len(subset))
        y = subset[metric]
        colors = [color_map.get(src, "grey") for src in subset['source']]
        ax.scatter(x, y, c=colors, s=20, alpha=0.7,
                   edgecolor="lightgrey", linewidth=0.5)

    # Ajustement des ticks et des étiquettes de l'axe X
    ax.set_xticks(positions)
    ax.set_xticklabels([str(age) for age in age_categories], fontsize=12)
    ax.set_xlim(0.5, len(age_categories) + 0.5)
    ax.set_ylim(*y_limits)  # Fixer les limites de l'axe Y

    # Ajouter la légende pour les 'source'
    handles = [plt.Line2D([0], [0], marker='o', color=color, linestyle='None', markersize=8, label=source)
               for source, color in color_map.items()]
    ax.legend(handles=handles, title='Départament',
              loc='upper left', bbox_to_anchor=(1, 1))

    # Lignes verticales pour séparer les catégories
    for pos in positions + 0.5:
        ax.axvline(x=pos, color='grey', linestyle=':', linewidth=0.6)

    # Titres et étiquettes des axes
    ax.set_title(f"{metric_full_name} selon l'âge pour le cultivar '{cultivar}'",
                 fontsize=16, weight='bold', pad=30)
    ax.set_xlabel("Âge de la plantation (années)", fontsize=14)
    ax.set_ylabel(metric_full_name, fontsize=14, labelpad=10)

    # Ajouter le graphique au PDF
    pdf.savefig(fig)

    # Sauvegarder le graphique comme PNG com index do cultivar
    filename = f"{cultivar_index:02d}_{cultivar}_{metric}.png".replace(
        "/", "_")
    filepath = os.path.join(output_path, filename)
    plt.savefig(filepath, bbox_inches="tight", dpi=300)

    # Fermer la figure
    plt.close(fig)


def boxnotch_confidenceXage_lidar_metrics(df, cultivar, metric, color_map, y_limits, pdf, output_path, cultivar_index):
    """
    Génère deux graphiques par page : un pour la "Probabilité d’appartenance (%)"
    et un pour une métrique Lidar spécifique, et sauvegarde chaque graphique individuellement en PNG.

    Args:
        df (DataFrame): Le DataFrame filtré.
        cultivar (str): Le nom du cultivar analysé.
        metric (str): Le nom de la métrique Lidar analysée.
        color_map (dict): Un dictionnaire associant chaque 'source' à une couleur.
        y_limits (tuple): Les limites de l'axe Y pour la métrique Lidar.
        pdf (PdfPages): Un objet PdfPages pour sauvegarder les graphiques au format PDF.
        output_path (str): Le chemin du dossier pour sauvegarder les fichiers PNG individuels.
        cultivar_index (int): L'index basé sur le cultivar.

    Returns:
        None: Sauvegarde les deux graphiques sur une page du PDF et en PNG.
    """
    # Dictionnaire des noms complets pour les métriques Lidar
    metric_names = {
        "grid_CC": "Canopy Cover (CC)",
        "grid_PAI": "Plant Area Index (PAI)",
        "grid_ENL": "Effective Number of Layers (ENL)",
        "grid_VCI": "Vertical Canopy Index (VCI)",
        "grid_MOCH": "Mean Overstory Canopy Height (MOCH)"
    }

    # Obtenir le nom complet de la métrique
    metric_full_name = metric_names.get(metric, metric)

    # Filtrer le DataFrame pour le cultivar et éliminer les valeurs manquantes
    df_cultivar = df[df['cultivar_n'] == cultivar].dropna(
        subset=['age_plan', metric, 'valeur']
    ).copy()

    if df_cultivar.empty:
        print(
            f"Aucune donnée pour le cultivar '{cultivar}', métrique '{metric}'.")
        return

    # Définir les catégories d'âge (1 à 12 ans)
    age_categories = list(range(1, 13))
    df_cultivar['age_plan'] = pd.Categorical(
        df_cultivar['age_plan'], categories=age_categories, ordered=True)

    # Préparer les données pour les graphiques
    data_prob = [df_cultivar[df_cultivar['age_plan'] == age]['valeur']
                 for age in age_categories]
    data_metric = [df_cultivar[df_cultivar['age_plan'] == age][metric]
                   for age in age_categories]

    # Créer la figure avec deux graphiques empilés
    fig, axes = plt.subplots(2, 1, figsize=(16, 16), facecolor='white')

    # Configurations de base
    positions = np.arange(1, len(age_categories) + 1)
    boxplot_positions = positions + 0.25  # Ajustement des positions des boxplots

    # === Graphique 1 : Probabilité d’appartenance (%) ===
    ax1 = axes[0]
    mid_y_prob = 50  # Valeur médiane fixe pour "Probabilité d’appartenance"
    ax1.axhline(y=mid_y_prob, color='black', linestyle='--',
                linewidth=0.5)  # Ligne centrale horizontale

    # Création du boxplot pour la probabilité
    bp1 = ax1.boxplot(
        data_prob,
        notch=True,
        positions=boxplot_positions,
        patch_artist=True,
        widths=0.4,
        showfliers=False,  # Cacher les valeurs aberrantes
        medianprops=dict(color="#051512", linewidth=1.5),
        whiskerprops=dict(color="#051512", linewidth=1.2),
        capprops=dict(color="#051512", linewidth=1.2),
        boxprops=dict(facecolor="#1e7b6f", color="#0a2925", alpha=0.8)
    )

    # Ajout des points individuels
    for i, age in enumerate(age_categories):
        subset = df_cultivar[df_cultivar['age_plan'] == age]
        if subset.empty:
            ax1.text(positions[i], mid_y_prob, 'NA', ha='center',
                     va='center', color='red', fontsize=14, fontweight='bold')
            continue
        x = np.random.normal(positions[i] - 0.25, 0.05, size=len(subset))
        y = subset['valeur']
        colors = [color_map.get(src, "grey") for src in subset['source']]
        ax1.scatter(x, y, c=colors, s=20, alpha=0.7,
                    edgecolor="lightgrey", linewidth=0.5)

    # Lignes verticales pour séparer les années
    for pos in positions + 0.5:
        ax1.axvline(x=pos, color='grey', linestyle=':', linewidth=0.6)

    # Titres et étiquettes pour le graphique 1
    ax1.set_title(
        f"Probabilité d’appartenance (%) selon l'âge pour le cultivar '{cultivar}'", fontsize=16, weight='bold')
    ax1.set_xlabel("Âge de la plantation (années)", fontsize=14)
    ax1.set_ylabel("Probabilité d’appartenance (%)", fontsize=14, labelpad=10)
    ax1.set_xticks(positions)
    ax1.set_xticklabels([str(age) for age in age_categories], fontsize=12)
    ax1.set_xlim(0.5, len(age_categories) + 0.5)
    ax1.set_ylim(0, 102)  # Limites fixes pour la probabilité

    # === Graphique 2 : Métrique Lidar ===
    ax2 = axes[1]
    mid_y_metric = (y_limits[0] + y_limits[1]) / 2
    ax2.axhline(y=mid_y_metric, color='black', linestyle='--',
                linewidth=0.5)  # Ligne centrale horizontale

    # Création du boxplot pour la métrique Lidar
    bp2 = ax2.boxplot(
        data_metric,
        notch=True,
        positions=boxplot_positions,
        patch_artist=True,
        widths=0.4,
        showfliers=False,  # Cacher les valeurs aberrantes
        medianprops=dict(color="#051512", linewidth=1.5),
        whiskerprops=dict(color="#051512", linewidth=1.2),
        capprops=dict(color="#051512", linewidth=1.2),
        boxprops=dict(facecolor="#1e7b6f", color="#0a2925", alpha=0.8)
    )

    # Ajout des points individuels
    for i, age in enumerate(age_categories):
        subset = df_cultivar[df_cultivar['age_plan'] == age]
        if subset.empty:
            ax2.text(positions[i], mid_y_metric, 'NA', ha='center',
                     va='center', color='red', fontsize=14, fontweight='bold')
            continue
        x = np.random.normal(positions[i] - 0.25, 0.05, size=len(subset))
        y = subset[metric]
        colors = [color_map.get(src, "grey") for src in subset['source']]
        ax2.scatter(x, y, c=colors, s=20, alpha=0.7,
                    edgecolor="lightgrey", linewidth=0.5)

    # Lignes verticales pour séparer les années
    for pos in positions + 0.5:
        ax2.axvline(x=pos, color='grey', linestyle=':', linewidth=0.6)

    # Titres et étiquettes pour le graphique 2
    ax2.set_title(
        f"{metric_full_name} selon l'âge pour le cultivar '{cultivar}'", fontsize=16, weight='bold')
    ax2.set_xlabel("Âge de la plantation (années)", fontsize=14)
    ax2.set_ylabel(metric_full_name, fontsize=14, labelpad=10)
    ax2.set_xticks(positions)
    ax2.set_xticklabels([str(age) for age in age_categories], fontsize=12)
    ax2.set_xlim(0.5, len(age_categories) + 0.5)
    ax2.set_ylim(*y_limits)  # Limites spécifiques pour la métrique

    # Ajouter les deux graphiques à la page PDF
    pdf.savefig(fig)

    # Sauvegarder les graphiques en PNG
    filename = f"{cultivar_index:02d}_{cultivar}_{metric}.png".replace(
        "/", "_")
    filepath = os.path.join(output_path, filename)
    plt.savefig(filepath, bbox_inches="tight", dpi=300)

    # Fermer la figure
    plt.close(fig)
