#!/usr/bin/env python3
"""
Lancement du générateur CSV ultra-rapide
Alternative high-performance au pipeline Dataflow
"""

import subprocess
import sys
import time

def main():
    print("🏎️  GÉNÉRATEUR CSV ULTRA-RAPIDE")
    print("=" * 50)
    print("🎯 Objectif: 10M lignes en 5-10 minutes")
    print("⚡ Méthode: Multi-threading local + gsutil parallel")
    print("📁 Destination: gs://supdevinci_bucket/sanda_celia/raw/")
    print("=" * 50)
    
    # Vérifier les prérequis
    print("🔍 Vérification des prérequis...")
    
    try:
        subprocess.run(["gsutil", "version"], capture_output=True, check=True)
        print("✅ gsutil disponible")
    except:
        print("❌ gsutil non trouvé - installez Google Cloud SDK")
        return 1
    
    try:
        import faker
        print("✅ faker disponible")
    except ImportError:
        print("❌ faker non trouvé - installez avec: pip install faker")
        return 1
    
    print("\n🚀 Lancement de la génération...")
    start_time = time.time()
    
    # Lancer le générateur rapide
    result = subprocess.run([sys.executable, "generate_csv_fast.py"])
    
    if result.returncode == 0:
        duration = time.time() - start_time
        print(f"\n🏁 SUCCÈS ! Terminé en {duration/60:.1f} minutes")
        print("📊 Prochaines étapes:")
        print("   1. Vérifiez vos fichiers: gsutil ls gs://supdevinci_bucket/sanda_celia/raw/")
        print("   2. Lancez Databricks pour la conversion Parquet/Delta")
        return 0
    else:
        print("\n💥 ÉCHEC de la génération")
        return result.returncode

if __name__ == "__main__":
    sys.exit(main()) 