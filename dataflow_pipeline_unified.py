#!/usr/bin/env python3
"""
Pipeline unifié de génération de données financières pour GCP/Databricks
Évite les problèmes d'imports relatifs avec Dataflow

Usage:
    export GOOGLE_APPLICATION_CREDENTIALS="$HOME/key-dataflow.json"
    uv run dataflow_pipeline_unified.py
"""

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions, GoogleCloudOptions, StandardOptions, SetupOptions
from apache_beam.io import WriteToText
from apache_beam.transforms import Create
from faker import Faker
from datetime import datetime, timedelta
import random
import os
import tempfile
import logging
from typing import Optional

# =======================================================================
# CONFIGURATION INTÉGRÉE - ÉVITE LES IMPORTS RELATIFS
# =======================================================================

class Config:
    """Configuration centralisée pour le projet GCP/Databricks"""
    
    # PARAMÈTRES GCP
    PROJECT_ID = "biforaplatform"
    REGION = "europe-west1"
    
    # ARCHITECTURE DES DOSSIERS (Data Lake)
    BUCKET_BASE = "gs://supdevinci_bucket/sanda_celia"
    TEMP_LOCATION = f"{BUCKET_BASE}/tmp"
    RAW_LOCATION = f"{BUCKET_BASE}/raw"
    STAGING_LOCATION = f"{BUCKET_BASE}/staging"
    DELTA_LOCATION = f"{BUCKET_BASE}/delta"
    
    # PARAMÈTRES DE GÉNÉRATION
    NUM_SHARDS = 5
    TARGET_SIZE_GB = 2.0
    ESTIMATED_ROWS = 10_000_000
    
    # DONNÉES MÉTIER
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

    @staticmethod
    def get_job_name() -> str:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        return f"generate-financial-data-{timestamp}"
    
    @staticmethod
    def get_output_paths() -> dict:
        return {
            "raw_csv": f"{Config.RAW_LOCATION}/mouvements",
            "staging_parquet": f"{Config.STAGING_LOCATION}/mouvements",
            "delta_tables": f"{Config.DELTA_LOCATION}/mouvements"
        }

# =======================================================================
# DoFn POUR APACHE BEAM - DANS LE MÊME FICHIER
# =======================================================================

class GenerateRow(beam.DoFn):
    """DoFn pour générer une ligne CSV avec logique métier"""
    
    def __init__(self, start_date_str: Optional[str] = None):
        super().__init__()
        self.fake = Faker()
        self.start_date_str = start_date_str or Config.START_DATE
        self.base_date = datetime.strptime(self.start_date_str, "%Y-%m-%d")

    def process(self, element):
        """Génère une ligne CSV pour le secteur financier/assurance"""
        i = element
        date_op = self.base_date + timedelta(days=random.randint(0, Config.DATE_RANGE_DAYS))
        produit = random.choice(Config.PRODUITS)
        type_op = random.choice(Config.TYPES_OPERATIONS)
        montant = Config.get_montant_by_operation_type(type_op)
        agence_id = random.choice(Config.AGENCES)
        pays = random.choice(Config.PAYS)

        id_mouv = f"M{str(i).zfill(7)}"
        csv_line = (
            f"{id_mouv},{date_op.strftime('%Y-%m-%d')},"
            f"{produit},{type_op},{montant},{agence_id},{pays}"
        )
        yield csv_line

# =======================================================================
# PIPELINE PRINCIPAL
# =======================================================================

def run():
    """Fonction principale du pipeline"""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    logging.info("🚀 Démarrage du pipeline unifié GCP/Databricks")
    logging.info(f"   📁 Bucket: {Config.BUCKET_BASE}")
    logging.info(f"   📊 Architecture: RAW → STAGING → DELTA")
    logging.info(f"   💰 Secteur: Financier/Assurance ({len(Config.TYPES_OPERATIONS)} types d'opérations)")
    logging.info(f"   📋 Génération: {Config.ESTIMATED_ROWS:,} lignes (~{Config.TARGET_SIZE_GB} Go)")
    logging.info(f"   📄 Sortie: {Config.NUM_SHARDS} fichiers")

    # Options Dataflow
    options = PipelineOptions()
    gcloud_opts = options.view_as(GoogleCloudOptions)
    gcloud_opts.project = Config.PROJECT_ID
    gcloud_opts.region = Config.REGION
    gcloud_opts.job_name = Config.get_job_name()
    gcloud_opts.staging_location = Config.STAGING_LOCATION
    gcloud_opts.temp_location = Config.TEMP_LOCATION
    gcloud_opts.service_account_email = "dataflow-generator@biforaplatform.iam.gserviceaccount.com"
    
    logging.info(f"🔑 Service account: {gcloud_opts.service_account_email}")

    options.view_as(StandardOptions).runner = "DataflowRunner"
    
    # Configuration des dépendances - FICHIER UNIFIÉ
    setup_opts = options.view_as(SetupOptions)
    setup_opts.save_main_session = True
    
    if os.path.exists("requirements.txt"):
        setup_opts.requirements_file = "requirements.txt"
        logging.info("📦 Requirements.txt trouvé")
    else:
        logging.info("📦 Utilisation de save_main_session uniquement")

    # Pipeline Beam
    p = beam.Pipeline(options=options)

    indices = list(range(1, Config.ESTIMATED_ROWS + 1))
    
    rows = (
        p
        | "GenerateIndices" >> Create(indices)
        | "CreateCSVRows" >> beam.ParDo(GenerateRow())
    )

    header = "id_mouvement,date_op,produit,type_op,montant,agence_id,pays"
    output_paths = Config.get_output_paths()

    (
        rows
        | "WriteToGCS_RAW" >> WriteToText(
            file_path_prefix=output_paths["raw_csv"],
            file_name_suffix=".csv",
            header=header,
            num_shards=Config.NUM_SHARDS,
            shard_name_template="-SS-of-NN"
        )
    )

    logging.info("🔄 Lancement du pipeline Dataflow...")
    result = p.run()
    result.wait_until_finish()
    
    logging.info("✅ Pipeline terminé avec succès!")
    logging.info(f"📁 Fichiers disponibles: {output_paths['raw_csv']}")

if __name__ == "__main__":
    run() 