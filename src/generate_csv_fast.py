#!/usr/bin/env python3
"""
Générateur CSV ultra-rapide pour GCP/Databricks
Utilise multi-threading local + gsutil parallel pour maximum de performance

Performance cible : 10M lignes en 5-10 minutes
"""

import concurrent.futures
import csv
import os
import random
import subprocess
import tempfile
import time
from datetime import datetime, timedelta
from faker import Faker
from pathlib import Path
import logging
from typing import List

# Configuration identique à l'ancien projet
class Config:
    # PARAMÈTRES GCP
    PROJECT_ID = "biforaplatform"
    BUCKET_BASE = "gs://supdevinci_bucket/sanda_celia"
    RAW_LOCATION = f"{BUCKET_BASE}/raw"
    
    # GÉNÉRATION OPTIMISÉE
    TOTAL_ROWS = 10_000_000
    NUM_FILES = 5  # Nombre de fichiers à générer
    NUM_THREADS = 10  # Optimisé pour 12 CPU (garde 2 pour le système)
    CHUNK_SIZE = 50_000  # Chunks plus petits pour meilleur parallélisme
    
    # DONNÉES MÉTIER (identiques)
    START_DATE = "2025-06-01"
    DATE_RANGE_DAYS = 29
    PRODUITS = ["auto", "santé", "habitation", "vie"]
    TYPES_OPERATIONS = [
        "cotisation", "remboursement", "commission",
        "rétrocession", "ajustement_cotisation", "ajustement_remboursement", 
        "régularisation", "réajustement_prime",
        "pénalité_retard", "pénalité_résiliation", "correction_comptable", "annulation_opération",
        "virement_interne", "provision_sinistre", "libération_provision", 
        "taxe_assurance", "frais_gestion", "prime_exceptionnelle", "bonus_malus"
    ]
    AGENCES = [f"AG_{str(i).zfill(3)}" for i in range(1, 21)]
    PAYS = ["FR", "ES", "IT", "DE", "BE"]

    @staticmethod
    def get_montant_by_operation_type(type_op: str) -> float:
        """Génère des montants réalistes selon le type d'opération"""
        if type_op in ["cotisation", "prime_exceptionnelle"]:
            return round(random.uniform(50.0, 2500.0), 2)
        elif type_op in ["remboursement"]:
            return round(-random.uniform(100.0, 5000.0), 2)
        elif type_op in ["commission", "frais_gestion"]:
            return round(random.uniform(25.0, 500.0), 2)
        elif type_op in ["rétrocession"]:
            return round(random.uniform(100.0, 1000.0), 2)
        elif type_op in ["ajustement_cotisation", "ajustement_remboursement", "régularisation", "réajustement_prime"]:
            return round(random.uniform(-200.0, 200.0), 2)
        elif type_op in ["pénalité_retard", "pénalité_résiliation"]:
            return round(random.uniform(15.0, 300.0), 2)
        elif type_op in ["correction_comptable", "annulation_opération"]:
            return round(random.uniform(-500.0, 500.0), 2)
        elif type_op in ["virement_interne"]:
            return round(random.uniform(100.0, 10000.0), 2)
        elif type_op in ["provision_sinistre"]:
            return round(random.uniform(500.0, 15000.0), 2)
        elif type_op in ["libération_provision"]:
            return round(-random.uniform(500.0, 15000.0), 2)
        elif type_op in ["taxe_assurance"]:
            return round(random.uniform(5.0, 100.0), 2)
        elif type_op in ["bonus_malus"]:
            return round(random.uniform(-150.0, 150.0), 2)
        else:
            return round(random.uniform(10.0, 1000.0), 2)

def generate_chunk(start_row: int, chunk_size: int, file_index: int) -> str:
    """Génère un chunk de données et retourne le chemin du fichier local"""
    fake = Faker()
    base_date = datetime.strptime(Config.START_DATE, "%Y-%m-%d")
    
    # Créer fichier temporaire local
    temp_dir = Path("temp_csv")
    temp_dir.mkdir(exist_ok=True)
    
    filename = f"mouvements-{file_index:05d}-of-{Config.NUM_FILES:05d}.csv"
    filepath = temp_dir / filename
    
    with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        
        # Header seulement pour le premier chunk de chaque fichier
        if start_row % (Config.TOTAL_ROWS // Config.NUM_FILES) == 0:
            writer.writerow(['id_mouvement', 'date_op', 'produit', 'type_op', 'montant', 'agence_id', 'pays'])
        
        # Générer les données
        for i in range(start_row, min(start_row + chunk_size, Config.TOTAL_ROWS)):
            date_op = base_date + timedelta(days=random.randint(0, Config.DATE_RANGE_DAYS))
            produit = random.choice(Config.PRODUITS)
            type_op = random.choice(Config.TYPES_OPERATIONS)
            montant = Config.get_montant_by_operation_type(type_op)
            agence_id = random.choice(Config.AGENCES)
            pays = random.choice(Config.PAYS)
            
            id_mouv = f"M{str(i+1).zfill(7)}"
            writer.writerow([
                id_mouv, 
                date_op.strftime('%Y-%m-%d'),
                produit, 
                type_op, 
                montant, 
                agence_id, 
                pays
            ])
    
    return str(filepath)

def generate_all_files():
    """Génère tous les fichiers CSV en parallèle"""
    logging.info(f"🚀 Génération de {Config.TOTAL_ROWS:,} lignes avec {Config.NUM_THREADS} threads")
    logging.info(f"📁 Sortie: {Config.NUM_FILES} fichiers de ~{Config.TOTAL_ROWS//Config.NUM_FILES:,} lignes chacun")
    
    start_time = time.time()
    
    # Créer les tâches par chunks
    tasks = []
    rows_per_file = Config.TOTAL_ROWS // Config.NUM_FILES
    
    for file_idx in range(Config.NUM_FILES):
        start_row = file_idx * rows_per_file
        end_row = min(start_row + rows_per_file, Config.TOTAL_ROWS)
        
        # Diviser chaque fichier en chunks pour le multi-threading
        for chunk_start in range(start_row, end_row, Config.CHUNK_SIZE):
            chunk_size = min(Config.CHUNK_SIZE, end_row - chunk_start)
            tasks.append((chunk_start, chunk_size, file_idx))
    
    # Exécution parallèle
    generated_files = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=Config.NUM_THREADS) as executor:
        futures = [executor.submit(generate_chunk, start, size, idx) for start, size, idx in tasks]
        
        for future in concurrent.futures.as_completed(futures):
            try:
                filepath = future.result()
                generated_files.append(filepath)
                print(f"✅ Généré: {filepath}")
            except Exception as e:
                logging.error(f"❌ Erreur génération: {e}")
    
    # Consolider les chunks par fichier
    consolidate_files()
    
    duration = time.time() - start_time
    logging.info(f"⏱️  Génération terminée en {duration:.1f}s")
    
    return get_final_files()

def consolidate_files():
    """Consolide les chunks en fichiers finaux"""
    logging.info("🔄 Consolidation des chunks...")
    
    temp_dir = Path("temp_csv")
    final_dir = Path("csv_output")
    final_dir.mkdir(exist_ok=True)
    
    for file_idx in range(Config.NUM_FILES):
        final_filename = f"mouvements-{file_idx:05d}-of-{Config.NUM_FILES:05d}.csv"
        final_path = final_dir / final_filename
        
        # Trouver tous les chunks pour ce fichier
        chunk_files = sorted([f for f in temp_dir.glob("*.csv") if f"mouvements-{file_idx:05d}-" in f.name])
        
        with open(final_path, 'w', newline='', encoding='utf-8') as outfile:
            # Header
            outfile.write("id_mouvement,date_op,produit,type_op,montant,agence_id,pays\n")
            
            for chunk_file in chunk_files:
                with open(chunk_file, 'r', encoding='utf-8') as infile:
                    # Skip header if present
                    first_line = infile.readline()
                    if not first_line.startswith('id_mouvement'):
                        outfile.write(first_line)
                    
                    # Copy rest of file
                    outfile.write(infile.read())
        
        logging.info(f"📝 Consolidé: {final_path}")

def get_final_files() -> List[str]:
    """Retourne la liste des fichiers finaux générés"""
    final_dir = Path("csv_output")
    return [str(f) for f in final_dir.glob("*.csv")]

def upload_to_gcs(local_files: List[str]):
    """Upload parallèle vers GCS avec gsutil -m"""
    logging.info("☁️  Upload vers GCS...")
    start_time = time.time()
    
    # Construire la commande gsutil avec upload parallèle
    gcs_destination = f"{Config.RAW_LOCATION}/"
    
    # Option 1: Upload tous les fichiers en une commande (plus rapide)
    cmd = ["gsutil", "-m", "cp"] + local_files + [gcs_destination]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        duration = time.time() - start_time
        logging.info(f"✅ Upload terminé en {duration:.1f}s")
        logging.info(f"📁 Fichiers disponibles: {gcs_destination}")
        
    except subprocess.CalledProcessError as e:
        logging.error(f"❌ Erreur upload: {e}")
        logging.error(f"Output: {e.stdout}")
        logging.error(f"Error: {e.stderr}")

def cleanup_temp_files():
    """Nettoie les fichiers temporaires"""
    import shutil
    
    for temp_dir in ["temp_csv", "csv_output"]:
        if Path(temp_dir).exists():
            shutil.rmtree(temp_dir)
            logging.info(f"🧹 Nettoyé: {temp_dir}")

def main():
    """Fonction principale optimisée"""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    total_start = time.time()
    
    logging.info("🏎️  GÉNÉRATEUR CSV ULTRA-RAPIDE")
    logging.info(f"🎯 Objectif: {Config.TOTAL_ROWS:,} lignes → {Config.RAW_LOCATION}")
    logging.info(f"⚡ Config: {Config.NUM_THREADS} threads, chunks de {Config.CHUNK_SIZE:,}")
    
    try:
        # 1. Génération locale parallèle
        local_files = generate_all_files()
        
        # 2. Upload parallèle vers GCS
        upload_to_gcs(local_files)
        
        # 3. Nettoyage
        cleanup_temp_files()
        
        total_duration = time.time() - total_start
        logging.info(f"🏁 TERMINÉ en {total_duration:.1f}s ({total_duration/60:.1f} minutes)")
        logging.info(f"📊 Performance: {Config.TOTAL_ROWS / total_duration:,.0f} lignes/seconde")
        
    except Exception as e:
        logging.error(f"💥 Erreur fatale: {e}")
        cleanup_temp_files()

if __name__ == "__main__":
    main() 