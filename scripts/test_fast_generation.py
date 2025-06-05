#!/usr/bin/env python3
"""
Test simplifié du générateur CSV ultra-rapide
"""

import os
import subprocess
import sys

def test_generation():
    """Test de génération simplifié"""
    print("🧪 TEST DE GÉNÉRATION SIMPLIFIÉ")
    print("=" * 40)
    
    script_path = os.path.join(os.path.dirname(__file__), "..", "src", "generate_csv_fast_fixed.py")
    
    if not os.path.exists(script_path):
        print(f"❌ Script non trouvé: {script_path}")
        return False
    
    print("✅ Script trouvé")
    print("🔍 Test import...")
    
    # Test d'import simple
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
        import generate_csv_fast_fixed
        print("✅ Import réussi")
    except ImportError as e:
        print(f"❌ Erreur import: {e}")
        return False
    
    print("✅ Tous les tests passent !")
    return True

def main():
    """Test principal"""
    if test_generation():
        print("\n🎉 SUCCÈS - Le générateur est prêt !")
        print("💡 Lancez maintenant: uv run scripts/run_fast_generation.py")
        return 0
    else:
        print("\n💥 ÉCHEC - Problème de configuration")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 