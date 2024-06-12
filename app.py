import panel as pn
import laspy
import whitebox
import geopandas as gpd
import rioxarray as rxr
import earthpy.plot as ep
import matplotlib.pyplot as plt

# Initialiser Panel
pn.extension()

# Widgets
file_input = pn.widgets.FileInput(name="Fichier LiDAR")
crs_select = pn.widgets.RadioButtonGroup(
    name='Système de coordonnées',
    options={"Français": "epsg:2154", "Suisse": "epsg:2056", "Mondial (WGS84)": "epsg:4326"},
    button_type='success'
)

@pn.depends(file_input, crs_select)
def process_lidar(file_input, crs_select):
    if file_input is None:
        return "Veuillez télécharger un fichier LiDAR."
    
    file_path = file_input.filename
    crs = crs_select

    # Enregistrer le fichier téléchargé
    with open("uploaded_file.las", "wb") as f:
        f.write(file_input.value)

    # Initialiser les outils whitebox
    wbt = whitebox.WhiteboxTools()

    # Normaliser les données LiDAR
    wbt.normalize_lidar(
        i="uploaded_file.las",
        output="normalized.las",
        dtm="idw_dem_filled.tif"
    )

    # Détecter les arbres individuels et leurs couronnes
    wbt.individual_tree_detection(
        i="normalized.las",
        output="trees.shp",
        min_search_radius=2,
        min_height=5,
        max_search_radius="7",
        max_height="20",
        only_use_veg=True
    )

    # Charger les arbres détectés
    trees = gpd.read_file("trees.shp")
    trees.crs = crs
    trees.to_file("trees_{}.shp".format(crs.split(":")[1]))

    # Créer le Modèle de Hauteur de Canopée (CHM)
    wbt.subtract("dsm_filled.tif", "idw_dem_filled.tif", output="chm.tif")

    chm = rxr.open_rasterio("chm.tif", masked=True)
    chm_extent = ep.plotting_extent(chm[0], chm.rio.transform())

    # Tracer le CHM avec les arbres détectés
    fig, ax = plt.subplots(figsize=(12, 8))
    ep.plot_bands(arr=chm, cmap="RdYlGn", extent=chm_extent, ax=ax, title="Modèle de Hauteur de Canopée avec Arbres Détectés")
    trees.plot(color="steelblue", ax=ax, markersize=1.5)

    return pn.pane.Matplotlib(fig)

process_button = pn.widgets.Button(name="Lancer le traitement", button_type="primary")
process_button.on_click(process_lidar)

# Disposition de l'application
app = pn.Column(
    file_input,
    crs_select,
    process_button,
    process_lidar
)

# Afficher l'application
app.show()
