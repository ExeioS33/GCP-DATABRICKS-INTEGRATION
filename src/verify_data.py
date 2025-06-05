#!/usr/bin/env python3
"""
Script utilitaire pour vérifier et analyser les données générées dans GCS
Usage: python verify_data.py [--sample] [--stats]
"""

import sys
import subprocess
import json
from datetime import datetime
from config import Config

def run_gcloud_command(command: str) -> str:
    """Exécute une commande gcloud et retourne le résultat"""
    try:
        result = subprocess.run(command.split(), capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors de l'exécution de: {command}")
        print(f"Erreur: {e.stderr}")
        return ""

def check_bucket_access():
    """Vérifie l'accès au bucket GCS"""
    print("🔍 Vérification de l'accès au bucket...")
    
    # Test d'accès au bucket
    result = run_gcloud_command(f"gcloud storage ls {Config.BUCKET_BASE}/")
    if result:
        print(f"✅ Accès au bucket {Config.BUCKET_BASE} confirmé")
        return True
    else:
        print(f"❌ Impossible d'accéder au bucket {Config.BUCKET_BASE}")
        return False

def list_generated_files():
    """Liste les fichiers générés dans le dossier raw"""
    print(f"\n📁 Fichiers générés dans {Config.RAW_LOCATION}/")
    print("-" * 60)
    
    # Lister les fichiers CSV générés
    result = run_gcloud_command(f"gcloud storage ls {Config.RAW_LOCATION}/")
    if result:
        files = result.split('\n')
        csv_files = [f for f in files if f.endswith('.csv')]
        
        print(f"Nombre de fichiers CSV: {len(csv_files)}")
        for file in csv_files:
            # Obtenir la taille du fichier
            size_result = run_gcloud_command(f"gcloud storage du {file}")
            if size_result:
                size_info = size_result.split()[0]
                filename = file.split('/')[-1]
                print(f"  📄 {filename} - {size_info}")
        
        return csv_files
    else:
        print("❌ Aucun fichier trouvé ou erreur d'accès")
        return []

def get_total_size():
    """Calcule la taille totale des données générées"""
    print(f"\n📊 Taille totale des données dans {Config.RAW_LOCATION}/")
    print("-" * 60)
    
    result = run_gcloud_command(f"gcloud storage du --summarize {Config.RAW_LOCATION}/")
    if result:
        lines = result.split('\n')
        total_line = [line for line in lines if 'TOTAL:' in line or 'total:' in line]
        if total_line:
            print(f"Taille totale: {total_line[0]}")
    else:
        print("❌ Impossible de calculer la taille totale")

def sample_data():
    """Affiche un échantillon des données générées"""
    print(f"\n🔍 Échantillon des données (premières lignes du premier fichier)")
    print("-" * 60)
    
    # Trouver le premier fichier CSV
    result = run_gcloud_command(f"gcloud storage ls {Config.RAW_LOCATION}/")
    if result:
        files = [f for f in result.split('\n') if f.endswith('.csv')]
        if files:
            first_file = files[0]
            print(f"Fichier échantillonné: {first_file.split('/')[-1]}")
            
            # Télécharger les premières lignes
            sample_result = run_gcloud_command(f"gcloud storage cat {first_file}")
            if sample_result:
                lines = sample_result.split('\n')[:11]  # Header + 10 lignes
                for i, line in enumerate(lines):
                    if i == 0:
                        print(f"Header: {line}")
                        print("-" * 80)
                    elif line.strip():
                        print(f"Ligne {i}: {line}")
            else:
                print("❌ Impossible de lire l'échantillon de données")
        else:
            print("❌ Aucun fichier CSV trouvé")

def analyze_data_stats():
    """Analyse statistique basique des données"""
    print(f"\n📈 Analyse statistique des données")
    print("-" * 60)
    
    # Cette fonction nécessiterait de télécharger et traiter les données
    # Pour une version simple, on affiche les paramètres de configuration
    print(f"Configuration utilisée:")
    print(f"  • Nombre de lignes cible: {Config.ESTIMATED_ROWS:,}")
    print(f"  • Nombre de fichiers: {Config.NUM_SHARDS}")
    print(f"  • Taille cible: {Config.TARGET_SIZE_GB} Go")
    print(f"  • Période: {Config.START_DATE} + {Config.DATE_RANGE_DAYS} jours")
    print(f"  • Produits: {len(Config.PRODUITS)} ({', '.join(Config.PRODUITS)})")
    print(f"  • Types d'opérations: {len(Config.TYPES_OPERATIONS)}")
    print(f"  • Pays: {len(Config.PAYS)} ({', '.join(Config.PAYS)})")
    print(f"  • Agences: {len(Config.AGENCES)} (AG01 à AG{len(Config.AGENCES):02d})")

def show_databricks_connection_info():
    """Affiche les informations de connexion pour Databricks"""
    print(f"\n🔗 Informations de connexion Databricks")
    print("-" * 60)
    print(f"Chemin GCS pour Databricks:")
    print(f"  spark.read.option('header', 'true')")
    print(f"    .csv('{Config.RAW_LOCATION}/mouvements-*.csv')")
    print(f"\nChemin pour montage:")
    print(f"  /mnt/gcs{Config.RAW_LOCATION.replace('gs://', '/')}")

def main():
    """Fonction principale"""
    print("🚀 Vérification des données générées - Pipeline GCP/Databricks")
    print("=" * 70)
    
    # Vérifier les arguments
    show_sample = "--sample" in sys.argv
    show_stats = "--stats" in sys.argv
    
    # Vérification de l'accès
    if not check_bucket_access():
        print("\n❌ Vérifiez votre configuration gcloud et les permissions du bucket")
        sys.exit(1)
    
    # Lister les fichiers
    files = list_generated_files()
    
    if not files:
        print("\n⚠️  Aucun fichier trouvé. Le pipeline a-t-il été exécuté ?")
        sys.exit(1)
    
    # Taille totale
    get_total_size()
    
    # Échantillon si demandé
    if show_sample:
        sample_data()
    
    # Statistiques si demandé
    if show_stats:
        analyze_data_stats()
    
    # Infos de connexion Databricks
    show_databricks_connection_info()
    
    print(f"\n✅ Vérification terminée - {len(files)} fichiers trouvés")
    print(f"💡 Utilisez --sample pour voir un échantillon des données")
    print(f"💡 Utilisez --stats pour voir les statistiques détaillées")

if __name__ == "__main__":
    main() 