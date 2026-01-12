import requests
import pandas as pd
import os
from datetime import datetime

# --- CONFIGURATION ---
CSV_FILE = "data_bordeaux.csv"
BASE_URL = "https://datahub.bordeaux-metropole.fr/api/records/1.0/search/"

# Listes stratégiques
PARKINGS_CENTRE = [
    "Pey-Berland", "Tourny", "Bourse", "Jean Jaurès", 
    "Mériadeck", "Grands Hommes", "Victor Hugo", "Salinières"
]
PARKINGS_PERIPHERIE = [
    "Buttinière", "Arlac", "Quatre Chemins", "Arts et Métiers", 
    "Galin", "Stalingrad", "La Gardette", "Brandenburg", "Ravezies"
]

def get_data():
    timestamp = datetime.now()
    lignes = []

    # --- 1. PISCINE JUDAÏQUE ---
    try:
        resp = requests.get(BASE_URL, params={"dataset": "bor_frequentation_piscine_tr", "q": "Judaïque", "rows": 5})
        data = resp.json()
        if data.get('nhits', 0) > 0:
            for r in data['records']:
                f = r['fields']
                # On ne garde que si des valeurs existent
                if 'fmicourante' in f and 'fmizonmax' in f:
                    occ = f['fmicourante']
                    cap = f['fmizonmax']
                    taux = round(occ/cap*100, 1) if cap > 0 else 0
                    
                    lignes.append({
                        "date": timestamp,
                        "heure": timestamp.hour,
                        "type": "Piscine",
                        "sous_type": "Sport",
                        "nom": f"Judaïque - {f.get('fmizonlib', 'Bassin')}",
                        "occupe": occ,
                        "capacite": cap,
                        "taux_saturation": taux
                    })
    except Exception as e:
        print(f"Erreur Piscine: {e}")

    # --- 2. PARKINGS (CENTRE ET PÉRIPHÉRIE) ---
    try:
        resp = requests.get(BASE_URL, params={"dataset": "st_park_p", "rows": 100})
        data = resp.json()
        if data.get('nhits', 0) > 0:
            for r in data['records']:
                f = r['fields']
                nom = f.get('nom', 'Inconnu')
                total = f.get('total', 0)
                libres = f.get('libres', 0)
                
                # Identification du type de parking
                categorie = None
                if any(c.lower() in nom.lower() for c in PARKINGS_CENTRE):
                    categorie = "Parking Centre"
                elif any(c.lower() in nom.lower() for c in PARKINGS_PERIPHERIE):
                    categorie = "Parking P+R"
                
                if categorie and total > 0:
                    occupe = total - libres
                    taux = round(occupe/total*100, 1)
                    
                    lignes.append({
                        "date": timestamp,
                        "heure": timestamp.hour,
                        "type": "Mobilité",
                        "sous_type": categorie,
                        "nom": nom,
                        "occupe": occupe,
                        "capacite": total,
                        "taux_saturation": taux
                    })
    except Exception as e:
        print(f"Erreur Parking: {e}")

    return lignes

# --- EXÉCUTION ET SAUVEGARDE ---
if __name__ == "__main__":
    nouvelles_donnees = get_data()
    
    if nouvelles_donnees:
        df_new = pd.DataFrame(nouvelles_donnees)
        
        # Sauvegarde (Ajout ou Création)
        if os.path.exists(CSV_FILE):
            df_new.to_csv(CSV_FILE, mode='a', header=False, index=False)
        else:
            df_new.to_csv(CSV_FILE, mode='w', header=True, index=False)
            
        print(f"{len(nouvelles_donnees)} lignes ajoutées (Piscine + Parkings).")
    else:
        print("Aucune donnée récupérée.")
