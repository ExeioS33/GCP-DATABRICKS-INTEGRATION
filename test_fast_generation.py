#!/usr/bin/env python3
"""
Test du générateur CSV ultra-rapide avec un échantillon réduit
"""

import sys
import subprocess
import tempfile
from pathlib import Path

# Import du générateur rapide avec config modifiée
sys.path.insert(0, '.')
from generate_csv_fast import Config, generate_chunk, get_final_files, cleanup_temp_files

# Configuration test (plus petite)
Config.TOTAL_ROWS = 100_000  # 100k lignes pour test
Config.NUM_FILES = 2
Config.NUM_THREADS = 4
Config.CHUNK_SIZE = 10_000

def test_generation():
    """Test de génération locale seulement"""
    print("🧪 TEST DE GÉNÉRATION (100k lignes)")
    print("=" * 40)
    
    try:
        # Test génération d'un chunk
        print("🔍 Test génération chunk...")
        test_file = generate_chunk(0, 1000, 0)
        
        if Path(test_file).exists():
            print(f"✅ Chunk généré: {test_file}")
            
            # Vérifier le contenu
            with open(test_file, 'r') as f:
                lines = f.readlines()
                print(f"📝 Lignes générées: {len(lines)}")
                print(f"📋 Header: {lines[0].strip()}")
                print(f"🔍 Exemple ligne: {lines[1].strip()}")
            
            print("✅ Test chunk OK")
        else:
            print("❌ Échec génération chunk")
            return False
            
    except Exception as e:
        print(f"❌ Erreur test: {e}")
        return False
    finally:
        cleanup_temp_files()
    
    return True

def test_gsutil():
    """Test gsutil disponibilité"""
    print("\n🔍 Test gsutil...")
    try:
        result = subprocess.run(["gsutil", "version"], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ gsutil disponible")
            print(f"📦 Version: {result.stdout.split()[2]}")
            
            # Test accès au bucket
            result = subprocess.run(
                ["gsutil", "ls", "gs://supdevinci_bucket/sanda_celia/"],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                print("✅ Accès bucket OK")
                return True
            else:
                print("⚠️  Problème accès bucket (vérifiez les permissions)")
                return False
        else:
            print("❌ gsutil non disponible")
            return False
    except Exception as e:
        print(f"❌ Erreur gsutil: {e}")
        return False

def main():
    print("🧪 TEST GÉNÉRATEUR ULTRA-RAPIDE")
    print("=" * 50)
    
    # Test 1: Génération
    if not test_generation():
        print("\n💥 Échec test génération")
        return 1
    
    # Test 2: gsutil
    if not test_gsutil():
        print("\n⚠️  gsutil non opérationnel")
        print("📝 Vous pouvez quand même générer en local")
    
    print("\n🏁 TESTS TERMINÉS")
    print("✅ Prêt pour la génération complète !")
    print("\n🚀 Lancez: python run_fast_generation.py")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 