# Configuration pour le pipeline de génération de données GCP/Databricks
# =======================================================================

import os
from datetime import datetime
import random

class Config:
    """Configuration centralisée pour le projet GCP/Databricks"""
    
    # ---------------------------------------------------
    # PARAMÈTRES GCP
    # ---------------------------------------------------
    PROJECT_ID = "biforaplatform"  # Votre PROJECT_ID
    REGION = "europe-west1"
    
    # ---------------------------------------------------
    # ARCHITECTURE DES DOSSIERS (Data Lake)
    # ---------------------------------------------------
    BUCKET_BASE = "gs://supdevinci_bucket/sanda_celia"
    
    # Dossiers pour l'architecture Modern Data Stack
    TEMP_LOCATION = f"{BUCKET_BASE}/tmp"           # Temporaire Dataflow
    RAW_LOCATION = f"{BUCKET_BASE}/raw"            # Données brutes (CSV)
    STAGING_LOCATION = f"{BUCKET_BASE}/staging"    # Données optimisées (Parquet)
    DELTA_LOCATION = f"{BUCKET_BASE}/delta"        # Format Delta (Databricks)
    
    # ---------------------------------------------------
    # PARAMÈTRES DE GÉNÉRATION - OPTIMISÉS POUR 10M LIGNES/MOIS
    # ---------------------------------------------------
    NUM_SHARDS = 5                     # Moins de fichiers mais plus volumineux (~400MB chacun)
    TARGET_SIZE_GB = 2.0               # Taille cible totale (~2 Go pour 10M lignes)
    ESTIMATED_ROWS = 10_000_000        # 10M lignes par mois comme spécifié
    
    # ---------------------------------------------------
    # DONNÉES MÉTIER - SECTEUR FINANCIER/ASSURANCE
    # ---------------------------------------------------
    START_DATE = "2025-06-01"
    DATE_RANGE_DAYS = 29               # Plage de dates (30 jours = 1 mois)
    
    # Produits d'assurance
    PRODUITS = ["auto", "santé", "habitation", "vie"]
    
    # Types d'opérations financières étendues (19 types)
    TYPES_OPERATIONS = [
        # Opérations de base
        "cotisation", "remboursement", "commission",
        
        # Rétrocessions et ajustements
        "rétrocession", "ajustement_cotisation", "ajustement_remboursement", 
        "régularisation", "réajustement_prime",
        
        # Pénalités et corrections
        "pénalité_retard", "pénalité_résiliation", "correction_comptable", "annulation_opération",
        
        # Opérations internes
        "virement_interne", "provision_sinistre", "libération_provision", 
        "taxe_assurance", "frais_gestion", "prime_exceptionnelle", "bonus_malus"
    ]
    
    # Agences européennes
    AGENCES = [f"AG_{str(i).zfill(3)}" for i in range(1, 21)]  # AG_001 à AG_020
    
    # Pays européens
    PAYS = ["FR", "ES", "IT", "DE", "BE"]

    # ---------------------------------------------------
    # LOGIQUE MÉTIER - MONTANTS RÉALISTES PAR TYPE D'OPÉRATION
    # ---------------------------------------------------
    @staticmethod
    def get_montant_by_operation_type(type_op: str) -> float:
        """
        Génère des montants réalistes selon le type d'opération.
        Les cotisations et primes sont positives, les remboursements négatifs.
        """
        if type_op in ["cotisation", "prime_exceptionnelle"]:
            # Cotisations : 50€ à 2500€
            return round(random.uniform(50.0, 2500.0), 2)
        
        elif type_op in ["remboursement"]:
            # Remboursements : -100€ à -5000€ (négatifs)
            return round(-random.uniform(100.0, 5000.0), 2)
        
        elif type_op in ["commission", "frais_gestion"]:
            # Commissions : 25€ à 500€
            return round(random.uniform(25.0, 500.0), 2)
        
        elif type_op in ["rétrocession"]:
            # Rétrocessions : 100€ à 1000€
            return round(random.uniform(100.0, 1000.0), 2)
        
        elif type_op in ["ajustement_cotisation", "ajustement_remboursement", "régularisation", "réajustement_prime"]:
            # Ajustements : -200€ à +200€ (peuvent être positifs ou négatifs)
            return round(random.uniform(-200.0, 200.0), 2)
        
        elif type_op in ["pénalité_retard", "pénalité_résiliation"]:
            # Pénalités : 15€ à 300€
            return round(random.uniform(15.0, 300.0), 2)
        
        elif type_op in ["correction_comptable", "annulation_opération"]:
            # Corrections : -500€ à +500€
            return round(random.uniform(-500.0, 500.0), 2)
        
        elif type_op in ["virement_interne"]:
            # Virements : 100€ à 10000€
            return round(random.uniform(100.0, 10000.0), 2)
        
        elif type_op in ["provision_sinistre"]:
            # Provisions : 500€ à 15000€
            return round(random.uniform(500.0, 15000.0), 2)
        
        elif type_op in ["libération_provision"]:
            # Libérations de provisions : négatifs -500€ à -15000€
            return round(-random.uniform(500.0, 15000.0), 2)
        
        elif type_op in ["taxe_assurance"]:
            # Taxes : 5€ à 100€
            return round(random.uniform(5.0, 100.0), 2)
        
        elif type_op in ["bonus_malus"]:
            # Bonus/malus : -150€ à +150€
            return round(random.uniform(-150.0, 150.0), 2)
        
        else:
            # Montant par défaut
            return round(random.uniform(10.0, 1000.0), 2)

    # ---------------------------------------------------
    # PARAMÈTRES DATAFLOW
    # ---------------------------------------------------
    @staticmethod
    def get_job_name() -> str:
        """Génère un nom de job unique pour Dataflow"""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        return f"generate-financial-data-{timestamp}"
    
    @staticmethod
    def get_output_paths() -> dict:
        """Retourne les chemins de sortie pour les différents formats"""
        return {
            "raw_csv": f"{Config.RAW_LOCATION}/mouvements",
            "staging_parquet": f"{Config.STAGING_LOCATION}/mouvements",
            "delta_tables": f"{Config.DELTA_LOCATION}/mouvements"
        }
    
    # ---------------------------------------------------
    # VALIDATION DE LA CONFIGURATION
    # ---------------------------------------------------
    @staticmethod
    def validate_config():
        """Valide que la configuration est correcte"""
        if not Config.PROJECT_ID or Config.PROJECT_ID == "projet-mon-dataset":
            raise ValueError(
                f"❌ PROJECT_ID non configuré correctement: '{Config.PROJECT_ID}'\n"
                "   Modifiez la valeur dans src/config.py ou définissez GCP_PROJECT_ID"
            )
        
        if not Config.BUCKET_BASE.startswith("gs://"):
            raise ValueError(f"❌ BUCKET_BASE doit commencer par 'gs://': {Config.BUCKET_BASE}")
        
        if Config.NUM_SHARDS <= 0:
            raise ValueError(f"❌ NUM_SHARDS doit être > 0: {Config.NUM_SHARDS}")
        
        return True


# ---------------------------------------------------
# VARIABLES D'ENVIRONNEMENT (OPTIONNEL)
# ---------------------------------------------------
def load_from_env():
    """Charge la configuration depuis les variables d'environnement si disponibles"""
    if os.getenv('GCP_PROJECT_ID'):
        Config.PROJECT_ID = os.getenv('GCP_PROJECT_ID')
    
    if os.getenv('GCP_REGION'):
        Config.REGION = os.getenv('GCP_REGION')
    
    if os.getenv('GCS_BUCKET_BASE'):
        Config.BUCKET_BASE = os.getenv('GCS_BUCKET_BASE')
        # Recalculer les chemins
        Config.TEMP_LOCATION = f"{Config.BUCKET_BASE}/tmp"
        Config.RAW_LOCATION = f"{Config.BUCKET_BASE}/raw"
        Config.STAGING_LOCATION = f"{Config.BUCKET_BASE}/staging"
        Config.DELTA_LOCATION = f"{Config.BUCKET_BASE}/delta"

# Charger automatiquement les variables d'environnement au démarrage
load_from_env() 