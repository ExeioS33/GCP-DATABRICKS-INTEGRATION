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

# Import de la configuration centralisée
from config import Config

# ---------------------------------------------------
# 1. FONCTION D'ESTIMATION (OPTIONNELLE)
# ---------------------------------------------------

def estimate_rows_for_size(target_size_gb: float, sample_size: int = 1000) -> int:
    """
    Génère un petit fichier CSV local de 'sample_size' lignes pour mesurer
    la taille moyenne d'une ligne, puis calcule combien de lignes il faut
    pour atteindre target_size_gb.
    """
    fake = Faker()
    base_date = datetime.strptime(Config.START_DATE, "%Y-%m-%d")

    # Crée un fichier temporaire
    fd, tmp_path = tempfile.mkstemp(suffix=".csv")
    os.close(fd)

    with open(tmp_path, mode="w", newline="", encoding="utf-8") as f:
        # Entête
        f.write("id_mouvement,date_op,produit,type_op,montant,agence_id,pays\n")
        # Écris 'sample_size' lignes de test avec montants réalistes
        for i in range(1, sample_size + 1):
            date_op = base_date + timedelta(days=random.randint(0, Config.DATE_RANGE_DAYS))
            produit = random.choice(Config.PRODUITS)
            type_op = random.choice(Config.TYPES_OPERATIONS)
            # Utiliser la nouvelle logique de montants
            montant = Config.get_montant_by_operation_type(type_op)
            agence_id = random.choice(Config.AGENCES)
            pays = random.choice(Config.PAYS)
            line = (
                f"M{str(i).zfill(7)},{date_op.strftime('%Y-%m-%d')},"
                f"{produit},{type_op},{montant},{agence_id},{pays}\n"
            )
            f.write(line)

    sample_size_bytes = os.path.getsize(tmp_path)
    os.remove(tmp_path)
    avg_line_size = sample_size_bytes / sample_size
    target_bytes = target_size_gb * (1024**3)
    return int(target_bytes / avg_line_size)


# ---------------------------------------------------
# 2. DoFn POUR GÉNÉRER UNE LIGNE CSV AVEC LOGIQUE MÉTIER
# ---------------------------------------------------

class GenerateRow(beam.DoFn):
    def __init__(self, start_date_str: Optional[str] = None):
        super().__init__()
        self.fake = Faker()
        self.start_date_str = start_date_str or Config.START_DATE
        self.base_date = datetime.strptime(self.start_date_str, "%Y-%m-%d")

    def process(self, element):
        """
        element est un numéro de ligne (1-based). Retourne une string CSV.
        Génère des données réalistes pour le secteur financier/assurance.
        """
        i = element
        date_op = self.base_date + timedelta(days=random.randint(0, Config.DATE_RANGE_DAYS))
        produit = random.choice(Config.PRODUITS)
        type_op = random.choice(Config.TYPES_OPERATIONS)
        
        # Utiliser la logique de montants réalistes selon le type d'opération
        montant = Config.get_montant_by_operation_type(type_op)
        
        agence_id = random.choice(Config.AGENCES)
        pays = random.choice(Config.PAYS)

        id_mouv = f"M{str(i).zfill(7)}"
        csv_line = (
            f"{id_mouv},{date_op.strftime('%Y-%m-%d')},"
            f"{produit},{type_op},{montant},{agence_id},{pays}"
        )
        yield csv_line


# ---------------------------------------------------
# 3. FONCTION PRINCIPALE DU PIPELINE - ARCHITECTURE GCP/DATABRICKS
# ---------------------------------------------------

def run():
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Validation de la configuration
    try:
        Config.validate_config()
    except ValueError as e:
        logging.error(str(e))
        logging.error("📝 Modifiez le fichier config.py avec vos paramètres GCP")
        return
    
    logging.info("🚀 Démarrage du pipeline de génération de données pour GCP/Databricks")
    logging.info(f"   📁 Bucket de destination: {Config.BUCKET_BASE}")
    logging.info(f"   📊 Architecture: RAW (CSV) → STAGING (Parquet) → DELTA")
    logging.info(f"   💰 Secteur: Financier/Assurance avec {len(Config.TYPES_OPERATIONS)} types d'opérations")

    # 1) Calculer ou récupérer le nombre de lignes à générer
    if Config.ESTIMATED_ROWS:
        rows_to_generate = Config.ESTIMATED_ROWS
        logging.info(f"   📋 Génération de {rows_to_generate:,} lignes (≈ 10M lignes/mois)")
        logging.info(f"   📄 Fichiers de sortie: {Config.NUM_SHARDS} fichiers (~{(Config.TARGET_SIZE_GB * 1000) / Config.NUM_SHARDS:.0f}MB chacun)")
    else:
        logging.info("→ Estimation du nombre de lignes pour ~2 Go …")
        rows_to_generate = estimate_rows_for_size(Config.TARGET_SIZE_GB)
        logging.info(f"   • Lignes estimées : {rows_to_generate:,}")

    # 2) Paramétrer les options de Dataflow
    options = PipelineOptions()
    gcloud_opts = options.view_as(GoogleCloudOptions)
    gcloud_opts.project = Config.PROJECT_ID
    gcloud_opts.region = Config.REGION
    gcloud_opts.job_name = Config.get_job_name()
    gcloud_opts.staging_location = Config.STAGING_LOCATION
    gcloud_opts.temp_location = Config.TEMP_LOCATION
    
    # Spécifier explicitement le service account Dataflow pour contourner la contrainte
    gcloud_opts.service_account_email = "dataflow-generator@biforaplatform.iam.gserviceaccount.com"
    logging.info(f"🔑 Utilisation du service account: {gcloud_opts.service_account_email}")

    options.view_as(StandardOptions).runner = "DataflowRunner"
    options.view_as(SetupOptions).save_main_session = True

    # 3) Construire le pipeline Beam
    p = beam.Pipeline(options=options)

    # Création de la séquence d'indices - corrigé pour Apache Beam
    indices = list(range(1, rows_to_generate + 1))
    sequence = (
        p
        | "GenerateIndices" >> Create(indices)
    )

    # Pour chaque indice, on génère une ligne CSV avec logique métier
    rows = (
        sequence
        | "CreateCSVRows" >> beam.ParDo(GenerateRow())
    )

    # Entête des fichiers CSV
    header = "id_mouvement,date_op,produit,type_op,montant,agence_id,pays"

    # Obtenir les chemins de sortie
    output_paths = Config.get_output_paths()

    # Écriture dans le dossier RAW du bucket GCS (compatible Databricks)
    (
        rows
        | "WriteToGCS_RAW" >> WriteToText(
            file_path_prefix=output_paths["raw_csv"],
            file_name_suffix=".csv",
            header=header,
            num_shards=Config.NUM_SHARDS,
            shard_name_template="-SS-of-NN"  # Exemple : mouvements-00000-of-00005.csv
        )
    )

    # 4) Lancer le pipeline sur Dataflow
    logging.info("🔄 Lancement du pipeline Dataflow...")
    result = p.run()
    result.wait_until_finish()
    
    logging.info("✅ Génération et export vers GCS terminés.")
    logging.info(f"📁 Fichiers CSV disponibles dans: {output_paths['raw_csv']}")
    logging.info(f"   📊 {Config.NUM_SHARDS} fichiers de ~{(Config.TARGET_SIZE_GB * 1000) / Config.NUM_SHARDS:.0f}MB chacun")
    logging.info("🔄 Prochaines étapes:")
    logging.info(f"   1. Optimisation en Parquet via Databricks → {output_paths['staging_parquet']}")
    logging.info(f"   2. Conversion en format Delta via Databricks → {output_paths['delta_tables']}")


# ---------------------------------------------------
# 4. FONCTIONS UTILITAIRES POUR DATABRICKS
# ---------------------------------------------------

def print_databricks_setup_guide():
    """Affiche un guide pour configurer Databricks avec le bucket GCS"""
    print("\n" + "="*70)
    print("📘 GUIDE DE CONFIGURATION DATABRICKS - DONNÉES FINANCIÈRES")
    print("="*70)
    print(f"1. 📁 Données CSV générées dans: {Config.RAW_LOCATION}")
    print(f"   • Volume: {Config.ESTIMATED_ROWS:,} lignes (~{Config.TARGET_SIZE_GB} Go)")
    print(f"   • Fichiers: {Config.NUM_SHARDS} fichiers de ~{(Config.TARGET_SIZE_GB * 1000) / Config.NUM_SHARDS:.0f}MB")
    print(f"   • Types d'opérations: {len(Config.TYPES_OPERATIONS)} (rétrocessions, ajustements, pénalités)")
    print(f"2. 🔧 Configurer l'accès GCS dans Databricks:")
    print(f"   - Service Account avec accès au bucket: {Config.BUCKET_BASE}")
    print(f"   - Clés JSON stockées dans Databricks Secrets")
    print(f"3. 📊 Chemin de lecture Databricks:")
    print(f"   - df = spark.read.csv('{Config.RAW_LOCATION}/mouvements-*.csv', header=True)")
    print(f"4. 💾 Sauvegarde optimisée en Parquet avec partitioning:")
    print(f"   - df.write.mode('overwrite').partitionBy('pays', 'produit')")
    print(f"     .parquet('{Config.STAGING_LOCATION}/mouvements')")
    print(f"5. 🔄 Conversion en Delta Table:")
    print(f"   - df.write.format('delta').mode('overwrite')")
    print(f"     .save('{Config.DELTA_LOCATION}/mouvements')")
    print("\n💡 Exemples d'analyses possibles:")
    print("   • Détection d'anomalies sur les montants par type d'opération")
    print("   • Analyse des rétrocessions et ajustements par agence/pays")
    print("   • Suivi des pénalités et corrections comptables")
    print("="*70)


# ---------------------------------------------------
# 5. POINT D'ENTRÉE
# ---------------------------------------------------

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--guide":
        print_databricks_setup_guide()
    else:
        run()
