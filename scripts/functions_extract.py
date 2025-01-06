# Importation des bibliothèques nécessaires
from geopandas import sjoin
import os
import re
import pandas as pd
import geopandas as gpd
import numpy as np
import rasterio
from rasterio.transform import xy

# * ======================================= * #
# * ======================================= * #
# *   Fonctions pour extraire les valeurs   * #
# *     des rasters et créers les .csv      * #
# * ======================================= * #
# * ======================================= * #


def extract_confidence_values(confidence_raster_path, annees, nodata=0):
    """
    Extrait les valeurs des pixels valides d'un raster multibande, chaque bande correspondant à une année.

    Args :
        confidence_raster_path (str) : Chemin vers le raster multibande.
        annees (list) : Liste des années correspondant aux bandes.
        nodata (int) : Valeur des pixels sans données (défaut : 0).

    Returns :
        pd.DataFrame ou None : Tableau contenant x, y, valeur, date et tuile.
    """
    # Vérifie si le fichier raster existe
    if not os.path.exists(confidence_raster_path):
        print(f"Raster inexistant : {confidence_raster_path}")
        return None

    # Ouvre le raster
    with rasterio.open(confidence_raster_path) as src:
        df_list = []  # Liste pour stocker les DataFrames de chaque bande

        # Extraire le nom de la tuile à partir du nom du fichier
        zone = os.path.basename(confidence_raster_path).split(
            '_')[-1].replace('.tif', '')

        # Boucle sur chaque bande du raster
        for i, annee in enumerate(annees, start=1):
            image = src.read(i)  # Lit les valeurs de la bande i
            valid_mask = image != nodata  # Crée un masque pour les pixels valides

            # Passe à la bande suivante si tous les pixels sont nodata
            if valid_mask.sum() == 0:
                continue

            # Identifie les coordonnées des pixels valides
            rows, cols = np.where(valid_mask)
            x, y = xy(src.transform, rows, cols)

            # Crée un DataFrame pour la bande actuelle
            df_band = pd.DataFrame({
                'x': np.array(x),            # Coordonnées x
                'y': np.array(y),            # Coordonnées y
                'valeur': image[valid_mask],  # Valeurs des pixels
                'date': annee,               # Année associée à la bande
                'tuile': zone                # Nom de la tuile
            })

            df_list.append(df_band)

        # Combine les DataFrames de toutes les bandes si la liste n'est pas vide
        if df_list:
            df_tuile = pd.concat(df_list, ignore_index=True)
            return df_tuile
        else:
            return None  # Retourne None si aucune donnée valide n'a été trouvée


def extract_lidar_values(lidar_raster_paths, nodata=-999):
    """
    Extrait les valeurs des rasters LiDAR pour chaque métrique en supposant une même grille.

    Args :
        lidar_raster_paths (dict) : Dictionnaire {nom_métrique : chemin_raster}.
        nodata (int) : Valeur des pixels sans données (défaut : -999).

    Returns :
        pd.DataFrame : Tableau contenant les coordonnées x, y et une colonne pour chaque métrique.
    """
    coords_ref = None  # Initialise le DataFrame de référence pour stocker les coordonnées et les valeurs

    # Boucle sur chaque métrique (clé : nom de la métrique, valeur : chemin du raster)
    for metric_name, r_path in lidar_raster_paths.items():
        # Vérifie si le fichier raster existe
        if not os.path.exists(r_path):
            print(f"Raster LiDAR inexistant : {r_path}")
            continue

        # Ouvre le raster et extrait les valeurs
        with rasterio.open(r_path) as src:
            data = src.read(1)  # Lit la première bande du raster
            # Crée un masque pour les pixels valides (différents de nodata)
            valid_mask = data != nodata

            # Identifie les indices des pixels valides
            rows, cols = np.where(valid_mask)

            # Convertit les indices (ligne, colonne) en coordonnées géographiques (x, y)
            x, y = xy(src.transform, rows, cols)

            # Crée un DataFrame pour la métrique en cours
            df_metric = pd.DataFrame({
                'x': np.array(x),         # Coordonnées x
                'y': np.array(y),         # Coordonnées y
                # Valeurs de la métrique pour les pixels valides
                metric_name: data[valid_mask]
            })

            # Fusionne avec le DataFrame de référence
            if coords_ref is None:
                coords_ref = df_metric  # Initialise avec la première métrique
            else:
                coords_ref = coords_ref.merge(
                    df_metric, on=['x', 'y'], how='outer')  # Fusion externe

    # Retourne le DataFrame final avec toutes les métriques
    if coords_ref is not None:
        return coords_ref
    else:
        # Retourne un DataFrame vide si aucun raster n'a été traité
        return pd.DataFrame(columns=['x', 'y'])


def jointure_parcelle(df_pixels, peupleraies_merged):
    """
    Réalise une jointure spatiale à l'échelle des parcelles.

    Args :
        df_pixels (pd.DataFrame) : pixels avec coordonnées x et y.
        peupleraies_merged (gpd.GeoDataFrame) : parcelles avec géométrie.

    Returns :
        pd.DataFrame : données jointes contenant les colonnes pertinentes.
    """
    # Conversion en GeoDataFrame avec géométrie basée sur x, y
    gdf_pixels = gpd.GeoDataFrame(
        df_pixels,
        geometry=gpd.points_from_xy(df_pixels['x'], df_pixels['y']),
        crs=peupleraies_merged.crs
    )

    # Jointure spatiale entre les pixels et les parcelles
    gdf_joined = sjoin(gdf_pixels, peupleraies_merged,
                       how='left', predicate='intersects')

    # Sélection des colonnes
    cols = [
        'unique_id', 'id_parc', 'annee_plan', 'cultivar', 'cultivar_n',
        'source', 'PAI_GF_mean', 'VCI_mean', 'CC', 'MOCH', 'ENL',
        'Z_mean', 'densite', 'biomass_mean', 'lidar_date'
    ]

    # Renommer les colonnes avec suffixe '_right' si nécessaire
    rename_map = {
        f"{c}_right": c for c in cols if f"{c}_right" in gdf_joined.columns}
    gdf_joined = gdf_joined.rename(columns=rename_map)

    # Calcul de l'âge de la plantation si les colonnes nécessaires existent
    if 'date' in gdf_joined.columns and 'annee_plan' in gdf_joined.columns:
        gdf_joined['annee_plan'] = pd.to_numeric(
            gdf_joined['annee_plan'], errors='coerce')
        gdf_joined['age_plan'] = gdf_joined['date'] - gdf_joined['annee_plan']
    else:
        gdf_joined['age_plan'] = pd.NA

    # Filtrer pour supprimer les lignes avec age_plan négatif
    gdf_joined = gdf_joined[gdf_joined['age_plan'] >= 0]

    # Retourner le DataFrame sans les colonnes géométriques inutiles
    return pd.DataFrame(gdf_joined.drop(columns=['geometry', 'index_right'], errors='ignore'))


def jointure_pixel(df_pixels, peupleraies_merged):
    """
    Réalise une jointure spatiale à l'échelle du pixel.

    Args :
        df_pixels (pd.DataFrame) : Données contenant les coordonnées x, y des pixels.
        peupleraies_merged (gpd.GeoDataFrame) : Données géospatiales des parcelles.

    Returns :
        pd.DataFrame : Données jointes avec colonnes pertinentes pour l'échelle du pixel.
    """
    # Conversion du DataFrame en GeoDataFrame avec une géométrie basée sur x et y
    gdf_pixels = gpd.GeoDataFrame(
        df_pixels,
        geometry=gpd.points_from_xy(df_pixels['x'], df_pixels['y']),
        crs=peupleraies_merged.crs
    )

    # Jointure spatiale entre les pixels et les parcelles
    gdf_joined = sjoin(gdf_pixels, peupleraies_merged,
                       how='left', predicate='intersects')

    # Liste des colonnes pertinentes pour l'échelle du pixel
    cols = [
        'unique_id', 'id_parc', 'annee_plan', 'cultivar', 'cultivar_n',
        'source', 'lidar_date'
    ]

    # Renommer les colonnes qui contiennent le suffixe '_right'
    rename_map = {
        f"{c}_right": c for c in cols if f"{c}_right" in gdf_joined.columns}
    gdf_joined = gdf_joined.rename(columns=rename_map)

    # Calculer l'âge de plantation si les colonnes 'date' et 'annee_plan' sont présentes
    if 'date' in gdf_joined.columns and 'annee_plan' in gdf_joined.columns:
        gdf_joined['annee_plan'] = pd.to_numeric(
            gdf_joined['annee_plan'], errors='coerce')
        gdf_joined['age_plan'] = gdf_joined['date'] - gdf_joined['annee_plan']
    else:
        # Colonne vide si les données nécessaires sont absentes
        gdf_joined['age_plan'] = pd.NA

    # Filtrer pour supprimer les lignes avec age_plan négatif
    gdf_joined = gdf_joined[gdf_joined['age_plan'] >= 0]

    # Retourne un DataFrame sans la géométrie ni les colonnes inutiles
    return pd.DataFrame(gdf_joined.drop(columns=['geometry', 'index_right'], errors='ignore'))
