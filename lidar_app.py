import tkinter as tk
from tkinter import filedialog, messagebox
import whitebox
import geopandas as gpd
import rioxarray as rxr
import matplotlib.pyplot as plt
import earthpy.plot as ep

# Initialiser les outils Whitebox
wbt = whitebox.WhiteboxTools()

# Fonction pour sélectionner un fichier
def select_file():
    file_path = filedialog.askopenfilename(filetypes=[("LiDAR files", "*.las *.laz")])
    if file_path:
        las_file_entry.delete(0, tk.END)
        las_file_entry.insert(0, file_path)

# Fonction pour afficher la progression
def update_progress(message):
    progress_label.config(text=message)
    root.update_idletasks()

# Fonction pour traiter le fichier LiDAR
def process_lidar():
    input_file = las_file_entry.get()
    crs = crs_var.get()
    
    if not input_file:
        messagebox.showerror("Erreur", "Veuillez sélectionner un fichier LAS.")
        return
    
    try:
        update_progress("Création du DEM...")
        dem_file = input_file.replace('.las', '_dem.tif')
        wbt.lidar_idw_interpolation(i=input_file, output=dem_file, parameter="elevation", returns="last", resolution=1)
        
        update_progress("Création du DSM...")
        dsm_file = input_file.replace('.las', '_dsm.tif')
        wbt.lidar_digital_surface_model(i=input_file, output=dsm_file, resolution=1)
        
        update_progress("Création du CHM...")
        chm_file = input_file.replace('.las', '_chm.tif')
        wbt.subtract(dsm_file, dem_file, chm_file)
        
        update_progress("Détection des arbres...")
        trees_file = input_file.replace('.las', '_trees.shp')
        wbt.individual_tree_detection(i=chm_file, output=trees_file, min_height=5, only_use_veg=True)
        
        update_progress("Chargement et affichage des résultats...")
        trees = gpd.read_file(trees_file)
        trees.crs = crs
        
        fig, ax = plt.subplots(figsize=(10, 10))
        trees.plot(ax=ax, color='green', markersize=5)
        plt.title('Arbres détectés')
        plt.xlabel('Longitude')
        plt.ylabel('Latitude')
        plt.show()
        
        update_progress("Traitement terminé.")
        messagebox.showinfo("Succès", f"Traitement terminé. Fichier des arbres enregistré : {trees_file}")
    except Exception as e:
        messagebox.showerror("Erreur", f"Une erreur est survenue : {e}")

# Configurer l'interface Tkinter
root = tk.Tk()
root.title("Traitement des données LiDAR")

# Variables Tkinter
crs_var = tk.StringVar(value='EPSG:2056')

# Widgets Tkinter
las_file_label = tk.Label(root, text="Sélectionner le fichier LAS :")
las_file_entry = tk.Entry(root, width=50)
las_file_button = tk.Button(root, text="Parcourir", command=select_file)

crs_label = tk.Label(root, text="Sélectionner le système de coordonnées :")
crs_option = tk.OptionMenu(root, crs_var, "EPSG:2056", "EPSG:4326")

process_button = tk.Button(root, text="Traiter le fichier LiDAR", command=process_lidar)

progress_label = tk.Label(root, text="")

# Disposition des widgets Tkinter
las_file_label.grid(row=0, column=0, padx=10, pady=10)
las_file_entry.grid(row=0, column=1, padx=10, pady=10)
las_file_button.grid(row=0, column=2, padx=10, pady=10)

crs_label.grid(row=1, column=0, padx=10, pady=10)
crs_option.grid(row=1, column=1, padx=10, pady=10)

process_button.grid(row=2, column=0, columnspan=3, padx=10, pady=20)
progress_label.grid(row=3, column=0, columnspan=3, padx=10, pady=10)

# Démarrage de l'interface Tkinter
root.mainloop()
