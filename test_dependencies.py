#!/usr/bin/env python3
"""
Test script pour vérifier que toutes les dépendances sont disponibles
"""

def test_imports():
    """Test que tous les modules nécessaires peuvent être importés"""
    try:
        print("🔍 Test des imports...")
        
        # Test Apache Beam
        import apache_beam as beam
        print("✅ apache_beam: OK")
        
        # Test Faker
        from faker import Faker
        print("✅ faker: OK")
        
        # Test options Beam
        from apache_beam.options.pipeline_options import PipelineOptions
        print("✅ PipelineOptions: OK")
        
        # Test GCP options
        from apache_beam.options.pipeline_options import GoogleCloudOptions
        print("✅ GoogleCloudOptions: OK")
        
        # Test des modules standards
        import random, datetime, os, tempfile, logging
        print("✅ Modules standards: OK")
        
        print("\n🎉 Tous les imports fonctionnent !")
        return True
        
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        return False

if __name__ == "__main__":
    success = test_imports()
    if success:
        print("\n✅ Le pipeline devrait fonctionner correctement")
    else:
        print("\n❌ Problème de dépendances détecté")
        exit(1) 