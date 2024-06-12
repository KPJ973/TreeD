import tkinter as tk
from tkinter import filedialog, messagebox
import os
import whitebox
import geopandas as gpd
import rioxarray as rxr
import matplotlib.pyplot as plt
import earthpy.plot as ep
from rasterio.plot import plotting_extent

# Initialiser les outils Whitebox
wbt = whitebox.WhiteboxTools()

# Fonction pour sélectionner un fichier
def select_file():
    file_path = filedialog.askopenfilename(filetypes=[("LiDAR files", "*.las *.laz")])
    if file_path:
        las_file_entry.delete(0, tk.END)
        las_file_entry.insert(0, file_path)

# Fonction pour sélectionner le dossier de sortie
def select_output_folder():
    folder_path = filedialog.askdirectory()
    if folder_path:
        output_folder_entry.delete(0, tk.END)
        output_folder_entry.insert(0, folder_path)

# Fonction pour afficher la progression
def update_progress(message):
    progress_label.config(text=message)
    root.update_idletasks()

# Fonction pour exécuter les options sélectionnées
def run_selected_tasks():
    input_file = las_file_entry.get()
    output_folder = output_folder_entry.get()
    crs = crs_var.get()
    
    if not input_file:
        messagebox.showerror("Erreur", "Veuillez sélectionner un fichier LAS.")
        return
    
    if not output_folder:
        messagebox.showerror("Erreur", "Veuillez sélectionner un dossier de sortie.")
        return
    
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    try:
        files_to_update = []
        
        # Créer DEM (IDW)
        if dem_idw_var.get():
            update_progress("Création du DEM (IDW)...")
            dem_idw_file = os.path.join(output_folder, 'dem_idw.tif')
            wbt.lidar_idw_interpolation(
                i=input_file, 
                output=dem_idw_file, 
                parameter="elevation", 
                returns="last", 
                resolution=1
            )
            files_to_update.append(dem_idw_file)
        
        # Créer DEM (TIN)
        if dem_tin_var.get():
            update_progress("Création du DEM (TIN)...")
            dem_tin_file = os.path.join(output_folder, 'dem_tin.tif')
            wbt.lidar_tin_gridding(
                i=input_file, 
                output=dem_tin_file, 
                parameter="elevation", 
                returns="last", 
                resolution=1
            )
            files_to_update.append(dem_tin_file)
        
        # Créer DSM
        if dsm_var.get():
            update_progress("Création du DSM...")
            dsm_file = os.path.join(output_folder, 'dsm.tif')
            wbt.lidar_digital_surface_model(
                i=input_file, 
                output=dsm_file, 
                resolution=1
            )
            files_to_update.append(dsm_file)
        
        # Normaliser les données LiDAR
        if normalize_var.get():
            update_progress("Normalisation des données LiDAR...")
            normalized_file = os.path.join(output_folder, 'normalized.las')
            wbt.normalize_lidar(
                i=input_file, 
                output=normalized_file, 
                dtm=dem_idw_file  # Utilisation de DEM IDW pour la normalisation
            )
            files_to_update.append(normalized_file)
        
        # Créer CHM avec DEM IDW
        if chm_idw_var.get():
            update_progress("Création du CHM (DEM IDW)...")
            chm_idw_file = os.path.join(output_folder, 'chm_idw.tif')
            wbt.subtract(
                input1=dsm_file, 
                input2=dem_idw_file, 
                output=chm_idw_file
            )
            files_to_update.append(chm_idw_file)
        
        # Créer CHM avec DEM TIN
        if chm_tin_var.get():
            update_progress("Création du CHM (DEM TIN)...")
            chm_tin_file = os.path.join(output_folder, 'chm_tin.tif')
            wbt.subtract(
                input1=dsm_file, 
                input2=dem_tin_file, 
                output=chm_tin_file
            )
            files_to_update.append(chm_tin_file)
        
        # Détecter les arbres
        if detect_trees_var.get():
            update_progress("Détection des arbres...")
            trees_file = os.path.join(output_folder, 'trees.shp')
            wbt.individual_tree_detection(
                i=normalized_file, 
                output=trees_file, 
                min_search_radius=2.0, 
                min_height=5.0, 
                max_search_radius=7.0, 
                max_height=20.0, 
                only_use_veg=True
            )
            files_to_update.append(trees_file)
        
        update_progress("Traitement terminé.")
        messagebox.showinfo("Succès", f"Traitement terminé. Fichiers enregistrés dans : {output_folder}")
        
        # Mettre à jour la liste des fichiers pour visualisation
        update_file_list(files_to_update)
    except Exception as e:
        messagebox.showerror("Erreur", f"Une erreur est survenue : {e}")

# Fonction pour mettre à jour la liste des fichiers
def update_file_list(files):
    file_listbox.delete(0, tk.END)
    for file in files:
        if os.path.exists(file):
            file_listbox.insert(tk.END, file)

# Fonction pour visualiser un fichier sélectionné
def visualize_file():
    selected_file = file_listbox.get(tk.ACTIVE)
    if selected_file:
        try:
            if selected_file.endswith('.tif'):
                data = rxr.open_rasterio(selected_file, masked=True)
                ep.plot_bands(data, cmap="RdYlGn", figsize=(8, 8), title=f"Visualisation de {os.path.basename(selected_file)}")
                plt.show()
            elif selected_file.endswith('.shp'):
                data = gpd.read_file(selected_file)
                fig, ax = plt.subplots(figsize=(10, 10))
                data.plot(ax=ax, color='green', markersize=5)
                plt.title(f"Visualisation de {os.path.basename(selected_file)}")
                plt.xlabel('Longitude')
                plt.ylabel('Latitude')
                plt.show()
        except Exception as e:
            messagebox.showerror("Erreur", f"Une erreur est survenue lors de la visualisation : {e}")

# Configurer l'interface Tkinter
root = tk.Tk()
root.title("Traitement des données LiDAR")

# Variables Tkinter
crs_var = tk.StringVar(value='EPSG:2056')

# Variables des cases à cocher
dem_idw_var = tk.BooleanVar()
dem_tin_var = tk.BooleanVar()
dsm_var = tk.BooleanVar()
normalize_var = tk.BooleanVar()
chm_idw_var = tk.BooleanVar()
chm_tin_var = tk.BooleanVar()
detect_trees_var = tk.BooleanVar()

# Widgets Tkinter
las_file_label = tk.Label(root, text="Sélectionner le fichier LAS :")
las_file_entry = tk.Entry(root, width=50)
las_file_button = tk.Button(root, text="Parcourir", command=select_file)

output_folder_label = tk.Label(root, text="Sélectionner le dossier de sortie :")
output_folder_entry = tk.Entry(root, width=50)
output_folder_button = tk.Button(root, text="Parcourir", command=select_output_folder)

crs_label = tk.Label(root, text="Sélectionner le système de coordonnées :")
crs_option = tk.OptionMenu(root, crs_var, "EPSG:2056", "EPSG:4326")

# Cases à cocher pour les options de traitement
dem_idw_check = tk.Checkbutton(root, text="Créer DEM (IDW)", variable=dem_idw_var)
dem_tin_check = tk.Checkbutton(root, text="Créer DEM (TIN)", variable=dem_tin_var)
dsm_check = tk.Checkbutton(root, text="Créer DSM", variable=dsm_var)
normalize_check = tk.Checkbutton(root, text="Normaliser les données LiDAR", variable=normalize_var)
chm_idw_check = tk.Checkbutton(root, text="Créer CHM (IDW)", variable=chm_idw_var)
chm_tin_check = tk.Checkbutton(root, text="Créer CHM (TIN)", variable=chm_tin_var)
detect_trees_check = tk.Checkbutton(root, text="Détecter les arbres", variable=detect_trees_var)

# Bouton pour lancer les tâches sélectionnées
run_button = tk.Button(root, text="Lancer", command=run_selected_tasks)

progress_label = tk.Label(root, text="")

file_listbox_label = tk.Label(root, text="Fichiers disponibles :")
file_listbox = tk.Listbox(root, width=60, height=10)
visualize_button = tk.Button(root, text="Visualiser", command=visualize_file)

# Disposition des widgets Tkinter
las_file_label.grid(row=0, column=0, padx=10, pady=10)
las_file_entry.grid(row=0, column=1, padx=10, pady=10)
las_file_button.grid(row=0, column=2, padx=10, pady=10)

output_folder_label.grid(row=1, column=0, padx=10, pady=10)
output_folder_entry.grid(row=1, column=1, padx=10, pady=10)
output_folder_button.grid(row=1, column=2, padx=10, pady=10)

crs_label.grid(row=2, column=0, padx=10, pady=10)
crs_option.grid(row=2, column=1, padx=10, pady=10)

dem_idw_check.grid(row=3, column=0, columnspan=3, padx=10, pady=5, sticky='w')
dem_tin_check.grid(row=4, column=0, columnspan=3, padx=10, pady=5, sticky='w')
dsm_check.grid(row=5, column=0, columnspan=3, padx=10, pady=5, sticky='w')
normalize_check.grid(row=6, column=0, columnspan=3, padx=10, pady=5, sticky='w')
chm_idw_check.grid(row=7, column=0, columnspan=3, padx=10, pady=5, sticky='w')
chm_tin_check.grid(row=8, column=0, columnspan=3, padx=10, pady=5, sticky='w')
detect_trees_check.grid(row=9, column=0, columnspan=3, padx=10, pady=5, sticky='w')

run_button.grid(row=10, column=0, columnspan=3, padx=10, pady=20)
progress_label.grid(row=11, column=0, columnspan=3, padx=10, pady=10)

file_listbox_label.grid(row=12, column=0, padx=10, pady=10)
file_listbox.grid(row=13, column=0, columnspan=3, padx=10, pady=10)

visualize_button.grid(row=14, column=0, columnspan=3, padx=10, pady=10)

# Démarrage de l'interface Tkinter
root.mainloop()
