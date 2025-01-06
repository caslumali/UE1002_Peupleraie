# Importation des bibliothèques nécessaires
import os
import subprocess
import geopandas as gpd
import numpy as np
import rasterio
from rasterio.mask import mask
from rasterio.enums import Resampling
from rasterio.warp import reproject


# * ======================================= * #
# * ======================================= * #
#     Fonctions pour faire le masquage      * #
# * ======================================= * #
# * ======================================= * #

def add_band_names(raster_path, band_names):
    """
    Ajouter des descriptions aux bandes d'un raster.

    Args:
        raster_path (str): Chemin du raster à modifier.
        band_names (list): Liste des noms à attribuer aux bandes.
    """
    with rasterio.open(raster_path, 'r+') as src:
        if len(band_names) != src.count:
            raise ValueError(
                "Le nombre de noms ne correspond pas au nombre de bandes.")

        # Attribuer des descriptions aux bandes
        for i, name in enumerate(band_names, start=1):
            src.set_band_description(i, name)

        print(f"Descriptions ajoutées pour le raster : {raster_path}")


def create_vrt(base_dir, zone, annees, raster_type, output_dir, rasters=None):
    """
    Crée un fichier VRT en empilant plusieurs rasters.

    Args:
        base_dir (str): Répertoire contenant les rasters.
        zone (str): Nom de la zone géographique.
        annees (list): Liste des années à inclure.
        raster_type (str): Préfixe des rasters.
        output_dir (str): Répertoire de sortie.
        rasters (list, optional): Liste explicite des rasters à inclure.

    Returns:
        str: Chemin du fichier VRT créé ou None si aucun raster trouvé.
    """

    if not rasters:
        rasters = []
        for annee in annees:
            raster_path = os.path.join(base_dir, str(
                annee), f'{raster_type}_{zone}_{annee}.tif')
            if os.path.exists(raster_path):
                rasters.append(raster_path)
            else:
                print(
                    f"Raster non trouvé pour l'année {annee} et la zone {zone}")

    if rasters:
        os.makedirs(output_dir, exist_ok=True)
        vrt_output_path = os.path.join(
            output_dir, f'{raster_type}_stack_{zone}.vrt')
        gdal_command = ['gdalbuildvrt', '-separate', vrt_output_path] + rasters
        subprocess.run(gdal_command)
        print(f'VRT créé à : {vrt_output_path}')
        return vrt_output_path
    else:
        print("Aucun raster disponible pour créer le VRT.")
        return None


def mask_vrt(vrt_path, gpkg_path, output_dir, output_name, nodata_value, dtype_value):
    """
    Applique un masque à un VRT en utilisant un shapefile et gère nodata/dtype.

    Args:
        vrt_path (str): Chemin du fichier VRT.
        gpkg_path (str): Chemin du fichier GeoPackage pour le masque.
        output_dir (str): Répertoire de sortie.
        output_name (str): Nom du fichier raster de sortie.
        nodata_value (int/float): Valeur NoData à attribuer.
        dtype_value (str): Type de données à utiliser (ex: 'int16', 'float32').

    Returns:
        str: Chemin du raster masqué.
    """
    # Charger le shapefile et appliquer un buffer de -10 m pour exclure les pixels en bordure
    shapes = gpd.read_file(gpkg_path, layer='peupleraies_merged_parcelle')
    shapes['geometry'] = shapes['geometry'].buffer(-10)

    # Filtrer les géométries nulles ou invalides
    shapes = shapes[shapes['geometry'].is_valid & ~shapes['geometry'].is_empty]

    # Vérifier la validation des géometries
    if shapes.empty:
        raise ValueError("Le shapefile est vide après application du buffer.")

    # Ouvrir le VRT
    with rasterio.open(vrt_path) as src:
        out_image, out_transform = mask(
            src, shapes.geometry, crop=True, nodata=nodata_value
        )

        # Copier et mettre à jour le profil des métadonnées
        out_meta = src.meta.copy()
        out_meta.update({
            "driver": "GTiff",
            "height": out_image.shape[1],
            "width": out_image.shape[2],
            "transform": out_transform,
            "nodata": nodata_value,
            "dtype": dtype_value,
            "compress": "LZW"
        })

        # Sauvegarder le raster masqué
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f'{output_name}.tif')
        with rasterio.open(output_path, 'w', **out_meta) as dst:
            dst.write(out_image.astype(dtype_value))

        print(f"Raster masqué enregistré à : {output_path}")
        return output_path


def clip_and_align_raster(input_raster, reference_raster, output_raster):
    """
    Aligne et clip un raster lidar sur la base d'un raster de référence.

    Args:
        input_raster (str): Chemin du raster lidar à aligner.
        reference_raster (str): Chemin du raster de référence.
        output_raster (str): Chemin de sortie pour le raster aligné et clipé.
    """
    with rasterio.open(reference_raster) as ref:
        ref_transform = ref.transform
        ref_crs = ref.crs
        ref_width = ref.width
        ref_height = ref.height
        ref_bounds = ref.bounds

    with rasterio.open(input_raster) as src:
        # Assurer une valeur NoData correcte
        nodata_value = src.nodata if src.nodata is not None else -999

        # Créer un tableau vide aligné à la résolution du raster de référence
        aligned_data = np.full((ref_height, ref_width),
                               nodata_value, dtype=np.float32)

        # Reprojection avec filtre sur les limites valides
        reproject(
            source=src.read(1),
            destination=aligned_data,
            src_transform=src.transform,
            src_crs=src.crs,
            dst_transform=ref_transform,
            dst_crs=ref_crs,
            dst_width=ref_width,
            dst_height=ref_height,
            resampling=Resampling.nearest,  # Utiliser 'nearest' pour éviter la moyenne
        )

        # Corriger les pixels invalides (zones hors raster source)
        aligned_data = np.where(
            aligned_data == src.nodata, nodata_value, aligned_data)

    # Mettre à jour le profil pour l'écriture
    profile = {
        "driver": "GTiff",
        "dtype": "float32",
        "nodata": nodata_value,
        "width": ref_width,
        "height": ref_height,
        "count": 1,
        "crs": ref_crs,
        "transform": ref_transform,
        "compress": "LZW"
    }

    # Sauvegarder le raster aligné
    os.makedirs(os.path.dirname(output_raster), exist_ok=True)
    with rasterio.open(output_raster, "w", **profile) as dst:
        dst.write(aligned_data, 1)

    print(f"Raster clipé et aligné sauvegardé : {output_raster}")


def verifier_raster(raster_path):
    """
    Vérifie les propriétés et statistiques d'un raster.

    Args:
        raster_path (str): Chemin du fichier raster à analyser.

    Affiche :
        - Nombre de bandes, valeur NoData, résolution, et projection.
        - Nombre de pixels valides et NoData pour chaque bande.
        - Statistiques (min, max, moyenne) pour les pixels valides.
    """

    with rasterio.open(raster_path) as src:
        print(f"=== Vérification du Raster: {raster_path} ===")
        print(f"Nombre de bandes: {src.count}")
        print(f"Valeur NoData: {src.nodata}")
        print(f"Résolution: {src.res}")
        print(f"Projection (CRS): {src.crs}")

        # Parcourir chaque bande
        for i in range(1, src.count + 1):
            bande = src.read(i)
            nodata_valeur = src.nodata

            # Exclure les valeurs NoData pour les statistiques
            bande_valide = bande[bande != nodata_valeur]

            # Compter les pixels NoData et valides
            nodata_count = np.sum(bande == nodata_valeur)
            valide_count = np.sum(bande != nodata_valeur)

            # Afficher les résultats
            print(f"--- Bande {i} ---")
            print(f"  Pixels NoData (0): {nodata_count}")
            print(f"  Pixels valides: {valide_count}")

            if bande_valide.size > 0:
                print(f"  Min: {np.min(bande_valide)}")
                print(f"  Max: {np.max(bande_valide)}")
                print(f"  Moyenne: {np.mean(bande_valide)}")
            else:
                print(f"  Bande {i} contient uniquement des valeurs NoData.")

        print("="*40)
