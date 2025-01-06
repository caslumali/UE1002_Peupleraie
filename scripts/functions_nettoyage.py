# Importation des bibliothèques nécessaires
import re
import pandas as pd
import geopandas as gpd


# * ======================================= * #
# * ======================================= * #
#    Fonctions pour nettoyer les vecteurs   * #
# * ======================================= * #
# * ======================================= * #

# Fonction pour vérifier si une valeur dans la colonne 'cultivar' contient un seul cultivar
def seul_cultivar(valeur):
    """
    Vérifie si une valeur de la colonne 'cultivar' correspond à un seul cultivar valide.

    Args:
        valeur (str): La valeur à vérifier.

    Returns:
        bool: True si la valeur est un seul cultivar valide, sinon False.
    """
    if not isinstance(valeur, str):
        return False
    # Si la valeur est vide ou contient 'nan', retourne False
    if not valeur or valeur.strip().lower() == "nan" or valeur.strip() == "":
        return False
    # Si la valeur contient virgule, retourne False
    if ',' in valeur:
        return False
    # Si la valeur contient certains mots spécifiques ou combinaisons, retourne False
    if re.search(r'\b(melange|essai|essais|futaie melangee|divers|et|noyer hybride|noyer commun|robinier|cemagref|cèdre|vesten dellinois|noyer/robinier|A 4 A )\b', valeur, re.IGNORECASE):
        return False
    # Si la valeur correspond à un format d'essai (par ex. 1000-1), retourne False
    if re.search(r'\d{3,4}-\d{1,2}', valeur):
        return False
    # Divise la chaîne de caractères selon des tirets ou espaces et vérifie s'il y a un seul cultivar
    cultivars = re.split(r'\s*-\s*', valeur.strip().lower())
    return len(set(cultivars)) == 1


def corriger_cultivar(nom):
    """
    Corrige les noms de cultivars en appliquant des corrections prédéfinies.

    Args:
        nom (str): Nom du cultivar à corriger.

    Returns:
        str: Nom corrigé si une correspondance existe, sinon la valeur d'origine.
    """

    corrections = {
        'A4a': 'A4A',
        'i 2014': 'i214',
        'i 214': 'i214',
        'i214': 'i214',
        'i45/51': 'i45/51',
        'i 45/51': 'i45/51',
        'ameramo': 'aleramo',
        'aleramo': 'aleramo',
        'dvina': 'diva',
        'diva': 'diva',
        'raspage': 'raspalje',
        'raspalje': 'raspalje',
        'hoogorst': 'hoogvorst',
        'hoogvorst': 'hoogvorst'
    }
    # Vérifie si 'nom' est une chaîne de caractères
    if isinstance(nom, str):
        return corrections.get(nom.lower(), nom)
    return nom  # Retourner la valeur d'origine si ce n'est pas une chaîne

# Nettoyage final du shapefile**


def nettoyer_gpkg(df, colonnes_a_conserver, dictionnaire_noms, couche_nom, echelle):
    """
    Nettoie un shapefile en sélectionnant certaines colonnes, en les renommant,
    en gérant les colonnes spécifiques (densite) et en s'assurant que la structure finale est cohérente.

    Args:
        df (GeoDataFrame): Données brutes.
        colonnes_a_conserver (list): Liste des colonnes à conserver.
        dictionnaire_noms (dict): Dictionnaire pour renommer les colonnes.
        couche_nom (str): Nom de la couche pour la logique spécifique.
        echelle (str): 'parcelle' ou 'pixel' pour déterminer les colonnes finales.

    Returns:
        GeoDataFrame: Données nettoyées et cohérentes.
    """

    # 1. Vérifier que l'objet est un GeoDataFrame avec une colonne 'geometry'
    df = gpd.GeoDataFrame(df, geometry='geometry', crs=df.crs)

    # 2. Sélectionner et renommer les colonnes d'après le dictionnaire fourni
    df = df[colonnes_a_conserver].rename(columns=dictionnaire_noms)

    # 3. Extraire les 4 premiers caractères de 'lidar_date' si elle existe
    if 'lidar_date' in df.columns:
        df['lidar_date'] = df['lidar_date'].astype(
            str).str[:4].replace('nan', pd.NA)

    # 4. Ajouter une colonne 'id_parc' si elle est absente (index unique par parcelle)
    if 'id_parc' not in df.columns:
        df['id_parc'] = range(1, len(df) + 1)

    # 5. Appliquer la logique spécifique selon le nom de la couche
    if couche_nom == 'dep47':
        # Renommer 'Densité' en 'densite'
        df = df.rename(columns={'Densité': 'densite'})

    elif couche_nom in ['dep82_bb', 'dep82_sp']:
        # Ajouter une densité par défaut de 204 pour ces couches
        df['densite'] = 204

    elif couche_nom == 'dep73':
        # Ajouter une colonne 'densite' vide
        df['densite'] = pd.NA

    elif couche_nom == 'dep10':
        # Ajouter des colonnes uniquement si l'échelle est 'parcelle'
        if echelle == 'parcelle':
            colonnes_a_remplir = ['PAI_GF_mean', 'CC', 'MOCH', 'ENL',
                                  'Z_mean', 'densite', 'biomass_mean', 'lidar_date']
            for col in colonnes_a_remplir:
                df[col] = pd.NA

        # Filtrer temporairement en fonction de 'd_essenc_2'
        if 'd_essenc_2' in df.columns:
            df = df[df['d_essenc_2'].isna()]
            # Supprimer la colonne après le filtre
            df = df.drop(columns=['d_essenc_2'])

    # 6. Corriger les noms des cultivars pour uniformiser les données
    df['cultivar_n'] = df['cultivar'].apply(corriger_cultivar)

    # 7. Convertir les MultiPolygon en Polygon si nécessaire
    df["geometry"] = df["geometry"].apply(
        lambda geom: geom.geoms[0] if geom.geom_type == "MultiPolygon" else geom
    )

    # 8. Définir les colonnes finales en fonction de l'échelle
    if echelle == 'parcelle':
        colonnes_finales = ['unique_id', 'id_parc', 'annee_plan', 'cultivar_n',
                            'source', 'PAI_GF_mean', 'VCI_mean', 'CC', 'MOCH', 'ENL',
                            'Z_mean', 'densite', 'biomass_mean', 'lidar_date', 'geometry']
    elif echelle == 'pixel':
        colonnes_finales = ['unique_id', 'id_parc', 'annee_plan', 'cultivar_n',
                            'source', 'lidar_date', 'geometry']
    else:
        # Lancer une erreur si l'échelle n'est pas valide
        raise ValueError(
            "L'argument 'echelle' doit être 'parcelle' ou 'pixel'.")

    # 9. Ajouter les colonnes manquantes pour garantir la cohérence
    for col in colonnes_finales:
        if col not in df.columns:
            df[col] = pd.NA

    # 10. Filtrer les parcelles pour ne garder que celles avec un seul cultivar
    df = df[df['cultivar'].apply(seul_cultivar)]

    # 11. Retourner le GeoDataFrame final avec les colonnes organisées
    return df[colonnes_finales]


# Fonction pour finaliser le shapefile et ajouter un identifiant unique
def finaliser_gpkg(df, source, echelle):
    """
    Capitalise la première lettre de chaque mot dans 'cultivar_n' et réorganise les colonnes.
    Ajoute également un identifiant unique pour chaque parcelle en fonction de l'échelle spécifiée.

    Args:
        df (GeoDataFrame): Données nettoyées.
        source (str): Nom de la couche pour la colonne 'source'.
        echelle (str): 'parcelle' ou 'pixel' pour déterminer les colonnes finales.

    Returns:
        GeoDataFrame: Données finalisées avec colonnes cohérentes.
    """
    # Ajouter la colonne 'source' avec le nom de la couche
    df['source'] = source

    # Créer un identifiant unique en combinant la source et l'id de la parcelle
    df['unique_id'] = df['source'] + '_' + df['id_parc'].astype(str)

    # Définir les colonnes finales selon l'échelle
    if echelle == 'parcelle':
        colonnes_finales = ['unique_id', 'id_parc', 'annee_plan', 'cultivar_n',
                            'source', 'PAI_GF_mean', 'VCI_mean', 'CC', 'MOCH', 'ENL',
                            'Z_mean', 'densite', 'biomass_mean', 'lidar_date', 'geometry']
    elif echelle == 'pixel':
        colonnes_finales = ['unique_id', 'id_parc', 'annee_plan', 'cultivar_n',
                            'source', 'lidar_date', 'geometry']
    else:
        raise ValueError(
            "L'argument 'echelle' doit être 'parcelle' ou 'pixel'.")

    # Ajouter les colonnes manquantes avec des valeurs NA
    for col in colonnes_finales:
        if col not in df.columns:
            df[col] = pd.NA

    # Capitaliser chaque mot de la chaîne 'cultivar_n' si elle existe
    if 'cultivar_n' in df.columns:
        df['cultivar_n'] = df['cultivar_n'].apply(lambda nom: ' '.join(
            mot.capitalize() for mot in nom.split()) if isinstance(nom, str) else nom)

    # Retourner les colonnes dans l'ordre spécifié
    return df[colonnes_finales]
