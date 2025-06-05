#!/usr/bin/env python3
"""
Générateur CSV ultra-rapide CORRIGÉ pour GCP/Databricks
Version corrigée qui résout les problèmes d'encodage UTF-8

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
    NUM_THREADS = 10  # Optimisé pour 12 CPU
    CHUNK_SIZE = 250_000  # Chunks plus gros pour éviter trop de fichiers
    
    # DONNÉES MÉTIER (identiques)
    START_DATE = "2025-06-01"
    DATE_RANGE_DAYS = 29
    PRODUITS = ["auto", "sante", "habitation", "vie"]  # Pas d'accents
    TYPES_OPERATIONS = [
        "cotisation", "remboursement", "commission",
        "retrocession", "ajustement_cotisation", "ajustement_remboursement", 
        "regularisation", "reajustement_prime",
        "penalite_retard", "penalite_resiliation", "correction_comptable", "annulation_operation",
        "virement_interne", "provision_sinistre", "liberation_provision", 
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
        elif type_op in ["retrocession"]:
            return round(random.uniform(100.0, 1000.0), 2)
        elif type_op in ["ajustement_cotisation", "ajustement_remboursement", "regularisation", "reajustement_prime"]:
            return round(random.uniform(-200.0, 200.0), 2)
        elif type_op in ["penalite_retard", "penalite_resiliation"]:
            return round(random.uniform(15.0, 300.0), 2)
        elif type_op in ["correction_comptable", "annulation_operation"]:
            return round(random.uniform(-500.0, 500.0), 2)
        elif type_op in ["virement_interne"]:
            return round(random.uniform(100.0, 10000.0), 2)
        elif type_op in ["provision_sinistre"]:
            return round(random.uniform(500.0, 15000.0), 2)
        elif type_op in ["liberation_provision"]:
            return round(-random.uniform(500.0, 15000.0), 2)
        elif type_op in ["taxe_assurance"]:
            return round(random.uniform(5.0, 100.0), 2)
        elif type_op in ["bonus_malus"]:
            return round(random.uniform(-150.0, 150.0), 2)
        else:
            return round(random.uniform(10.0, 1000.0), 2)

def generate_file_direct(file_index: int, rows_per_file: int) -> str:
    """Génère directement un fichier complet (sans chunks intermédiaires)"""
    base_date = datetime.strptime(Config.START_DATE, "%Y-%m-%d")
    
    # Créer dossier de sortie directement
    output_dir = Path("csv_output")
    output_dir.mkdir(exist_ok=True)
    
    filename = f"mouvements-{file_index:05d}-of-{Config.NUM_FILES:05d}.csv"
    filepath = output_dir / filename
    
    start_row = file_index * rows_per_file
    end_row = min(start_row + rows_per_file, Config.TOTAL_ROWS)
    
    # Écriture directe avec encodage explicite
    with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile, quoting=csv.QUOTE_MINIMAL)
        
        # Header
        writer.writerow(['id_mouvement', 'date_op', 'produit', 'type_op', 'montant', 'agence_id', 'pays'])
        
        # Générer les données ligne par ligne
        for i in range(start_row, end_row):
            date_op = base_date + timedelta(days=random.randint(0, Config.DATE_RANGE_DAYS))
            produit = random.choice(Config.PRODUITS)
            type_op = random.choice(Config.TYPES_OPERATIONS)
            montant = Config.get_montant_by_operation_type(type_op)
            agence_id = random.choice(Config.AGENCES)
            pays = random.choice(Config.PAYS)
            
            id_mouv = f"M{str(i+1).zfill(7)}"
            
            # Utiliser des données simples sans caractères spéciaux
            writer.writerow([
                id_mouv, 
                date_op.strftime('%Y-%m-%d'),
                produit, 
                type_op, 
                str(montant),  # Convertir en string explicitement
                agence_id, 
                pays
            ])
    
    return str(filepath)

def generate_all_files():
    """Génère tous les fichiers CSV en parallèle (version simplifiée)"""
    logging.info(f"🚀 Génération de {Config.TOTAL_ROWS:,} lignes avec {Config.NUM_THREADS} threads")
    logging.info(f"📁 Sortie: {Config.NUM_FILES} fichiers de ~{Config.TOTAL_ROWS//Config.NUM_FILES:,} lignes chacun")
    
    start_time = time.time()
    
    # Calculer les lignes par fichier
    rows_per_file = Config.TOTAL_ROWS // Config.NUM_FILES
    
    # Générer en parallèle (un thread par fichier)
    generated_files = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(Config.NUM_FILES, Config.NUM_THREADS)) as executor:
        futures = [executor.submit(generate_file_direct, i, rows_per_file) for i in range(Config.NUM_FILES)]
        
        for i, future in enumerate(concurrent.futures.as_completed(futures)):
            try:
                filepath = future.result()
                generated_files.append(filepath)
                logging.info(f"✅ Fichier {i+1}/{Config.NUM_FILES} généré: {Path(filepath).name}")
            except Exception as e:
                logging.error(f"❌ Erreur génération fichier: {e}")
    
    duration = time.time() - start_time
    logging.info(f"⏱️  Génération terminée en {duration:.1f}s")
    
    return generated_files

def upload_to_gcs(local_files: List[str]):
    """Upload parallèle vers GCS avec gsutil -m"""
    logging.info("☁️  Upload vers GCS...")
    start_time = time.time()
    
    # Construire la commande gsutil avec upload parallèle
    gcs_destination = f"{Config.RAW_LOCATION}/"
    
    # Upload avec gsutil -m (parallèle)
    cmd = ["gsutil", "-m", "cp"] + local_files + [gcs_destination]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        duration = time.time() - start_time
        logging.info(f"✅ Upload terminé en {duration:.1f}s")
        logging.info(f"📁 Fichiers disponibles: {gcs_destination}")
        return True
        
    except subprocess.CalledProcessError as e:
        logging.error(f"❌ Erreur upload: {e}")
        logging.error(f"Sortie: {e.stdout}")
        logging.error(f"Erreur: {e.stderr}")
        return False

def cleanup_temp_files():
    """Nettoie les fichiers temporaires"""
    import shutil
    
    for temp_dir in ["csv_output"]:
        if Path(temp_dir).exists():
            shutil.rmtree(temp_dir)
            logging.info(f"🧹 Nettoyé: {temp_dir}")

def verify_files(local_files: List[str]):
    """Vérifie la qualité des fichiers générés"""
    logging.info("🔍 Vérification des fichiers...")
    
    total_lines = 0
    for filepath in local_files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = len(f.readlines())
                total_lines += lines - 1  # Enlever le header
                logging.info(f"📝 {Path(filepath).name}: {lines-1:,} lignes")
        except Exception as e:
            logging.error(f"❌ Erreur lecture {filepath}: {e}")
    
    logging.info(f"📊 Total: {total_lines:,} lignes générées")
    return total_lines

def main():
    """Fonction principale optimisée et corrigée"""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    total_start = time.time()
    
    logging.info("🏎️  GÉNÉRATEUR CSV ULTRA-RAPIDE (VERSION CORRIGÉE)")
    logging.info(f"🎯 Objectif: {Config.TOTAL_ROWS:,} lignes → {Config.RAW_LOCATION}")
    logging.info(f"⚡ Config: {Config.NUM_THREADS} threads, génération directe")
    
    try:
        # 1. Génération locale parallèle (directe, sans consolidation)
        local_files = generate_all_files()
        
        if not local_files:
            logging.error("💥 Aucun fichier généré")
            return 1
        
        # 2. Vérification des fichiers
        total_lines = verify_files(local_files)
        
        # 3. Upload parallèle vers GCS
        if upload_to_gcs(local_files):
            logging.info("✅ Upload réussi")
        else:
            logging.warning("⚠️  Upload échoué, fichiers disponibles localement")
        
        # 4. Nettoyage
        cleanup_temp_files()
        
        total_duration = time.time() - total_start
        logging.info(f"🏁 TERMINÉ en {total_duration:.1f}s ({total_duration/60:.1f} minutes)")
        logging.info(f"📊 Performance: {total_lines / total_duration:,.0f} lignes/seconde")
        
        return 0
        
    except Exception as e:
        logging.error(f"💥 Erreur fatale: {e}")
        cleanup_temp_files()
        return 1

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code) 