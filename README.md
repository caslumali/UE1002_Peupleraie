
# UE1002 – Poplar Plantations Classification Uncertainty Analysis

Geospatial analysis of poplar plantation classification performance in France using Sentinel-2 confidence rasters and LiDAR metrics.

📍 SIGMA Master – UE1002 “Atelier Géomatique”
Agro Toulouse (ENSAT) · Université Toulouse II – Jean Jaurès


---

### 🌍 **Project Overview**

Este módulo consistiu em analisar a **incerteza de classificação de povoamentos de choupos (peupleraies)** no território francês, utilizando:

* Séries temporais de rasters de confiança (2017–2022) produzidos com o índice espectral PI;
* Métricas estruturais LiDAR de alta resolução (Canopy Cover e PAI);
* Dados vetoriais de parcelas agrícolas contendo idade e cultivares de cada plantação.

O objetivo principal foi avaliar como a **probabilidade de classificação** varia em função:

* da idade das plantações;
* dos tipos de cultivares;
* das métricas LiDAR, representando características estruturais.

---

### 🧭 **Study Area & Data**

* 4 departamentos franceses (47, 82, 73, 10) abrangendo 5 tiles Sentinel-2.
* Dados Sentinel-2 (2017–2022), rasters de confiança (PI Index).
* Métricas LiDAR IGN (2021–2023) em resolução de 10 m (CC, PAI).
* Dados vetoriais contendo cultivares, datas de plantio e atributos derivados.

---

### 🧪 **Methodological Workflow**

A pipeline foi inteiramente desenvolvida em **Python 3.10**, usando Jupyter Notebooks e bibliotecas geoespaciais (GeoPandas, Rasterio, Dash, Plotly).
Fluxo de trabalho em 5 etapas:

1. **Cleaning & preparation** of vector data (`1_Nettoyage_gpkg.ipynb`)
2. **Stacking, reprojection & clipping** of raster datasets (`2_Masquage_rasters.ipynb`)
3. **Raster value extraction & spatial join** with vector data (`3_Extraction_valeurs.ipynb`)
4. **Filtering & consistency checks** (dates, canopy thresholds) (`4_Filtrage_csv.ipynb`)
5. **Statistical visualization** using box-notch plots and interactive Dash apps

<p align="center">
  <img src="rapport/diagramme/diagramme_traitement.png" alt="Workflow diagram" width="500">
</p>

---

### 📈 **Key Analyses**

* Temporal evolution of classification confidence by plantation age
* Cultivar-specific uncertainty analysis
* Correlation between LiDAR metrics and classification performance
* Identification of minimum plantation age for reliable classification (~5 years)

All box-notch visualizations are available in the [`/results`](./results) folder:

* [Overall confidence vs age](./results/1_confidenceXage/Boxnotch_confidenceXage_all.pdf)
* [Top cultivars confidence vs age](./results/1_confidenceXage/Boxnotch_confidenceXage_top_cultivars.pdf)
* [Per year analysis](./results/2_confidenceXage_par_annee/Boxnotch_confidenceXage_par_annee.pdf)
* [LiDAR metrics vs age](./results/3_lidar_metrics/Boxnotch_lidar_metrics_top_cultivars.pdf)
* [Confidence & LiDAR combined](./results/4_confidenceXage_lidar_metrics/Boxnotch_confidenceXage_lidar_metrics_top_cultivars.pdf)

---

### 🖥️ **Interactive Visualization**

Two interactive Dash applications were developed:

* `7_0_App_un_graphique.py` — single interactive plot explorer
* `7_1_App_px_confidenceXage.py` — dual-plot comparison mode

They allow cultivar selection, variable choice (X/Y), hover inspection and faceted temporal views.

---

### 📂 **Repository Structure**

```
UE1002_Peupleraie/
├── data_brut/                # Raw raster & vector datasets
├── data_final/               # Preprocessed aligned data
├── scripts/                  # Jupyter notebooks + Python functions
├── results/                  # Boxnotch figures & analyses
├── rapport/                  # Project report & diagrams
└── README.md
```

---

### 🧠 **Key Skills & Tools**

* 🛰 Sentinel-2 time series analysis
* 🌳 LiDAR metrics integration (Canopy Cover, PAI)
* 🐍 Python geospatial stack (GeoPandas, Rasterio, Plotly/Dash)
* 📊 Box-notch visualization for statistical uncertainty analysis
* 🗂 GIS data preparation, masking & spatial joins

---

### 📚 **Reference**

Based on the project report:

> *Abir Ben Abdelghaffar, Lucas Lima, Naly Rakotoarindrazaka (2023). UE1002 – Analyse de l’incertitude de classification de peupleraies plantées.*

---
