# Projet Génération Données Synthétiques GCP/Databricks

Pipeline de génération de données financières synthétiques optimisé pour GCP et Databricks, réalisé par Sanda ANDRIA et Celia HADJI.

**Date de dernière mise à jour :** 05 Juin 2025

## 📋 **Vue d'ensemble**

Ce projet génère 10 millions de transactions financières synthétiques (~2GB) avec 19 types d'opérations réalistes pour l'analyse dans Databricks. Il propose une solution multi-thread locale ultra-performante, fruit d'une optimisation intensive lors de notre première journée de travail.

**Performance Atteinte :** 10M lignes générées et uploadées sur GCS en **3-5 minutes**.

## 🏗️ **Structure du Projet**

```
├── 📁 docs/                           # Documentation complète
│   ├── README.md                       # Ce guide détaillé
│   ├── RAPPORT_TECHNIQUE_GENERATION_DONNEES.md  # Rapport technique complet (par Sanda & Celia)
│   ├── RAPPORT_DEBOGAGE.md            # Historique debugging (ancienne approche Dataflow)
│   └── GCP_GCLOUD_CHEATSHEET.md       # Commandes GCP utiles
│
├── 📁 src/                            # Code source principal
│   └── generate_csv_fast_fixed.py     # Générateur multi-thread optimisé ⭐
│
├── 📁 scripts/                        # Scripts d'exécution et tests
│   ├── run_fast_generation.py         # Lancement génération rapide ⭐
│   ├── test_fast_generation.py        # Tests validation
│   ├── deploy.sh                      # Déploiement infrastructure (Terraform)
│   └── create_gcs_structure.sh        # Ancien script (maintenu pour référence)
│
├── 📁 infrastructure/                 # Infrastructure as Code
│   └── terraform/                     # Configuration Terraform
│       ├── main.tf                    # Ressources GCP complètes
│       └── terraform.tfvars.example   # Variables d'exemple
│
├── 📁 notebooks/                      # Notebooks Databricks pour l'analyse
│   └── 01_ingestion_brute_gcs.ipynb   # Ingestion GCS -> Databricks
│
├── requirements.txt                   # Dépendances Python (pour uv)
├── pyproject.toml                     # Configuration uv/Python
└── .gitignore                         # Fichiers ignorés par Git
```

## 🚀 **Démarrage Rapide**

### **1. Génération Rapide des Données (Recommandée)**

```bash
# Assurez-vous que l'environnement virtuel est activé
# (source .venv/bin/activate ou uv venv)

# Génération ultra-rapide de 10M lignes en 3-5 minutes
uv run scripts/run_fast_generation.py
```
Les fichiers CSV seront générés localement dans `csv_output/` puis uploadés sur `gs://supdevinci_bucket/sanda_celia/raw/`.

### **2. Déploiement de l'Infrastructure (Si nécessaire)**

Si vous partez de zéro, déployez l'infrastructure GCS et IAM avec Terraform :
```bash
# Authentification GCP (une seule fois)
gcloud auth login
gcloud auth application-default login

# Déploiement automatisé
./scripts/deploy.sh
```

### **3. Intégration Databricks**

Ouvrez le notebook `notebooks/01_ingestion_brute_gcs.ipynb` dans votre workspace Databricks et exécutez les cellules pour :
1. Configurer l'accès sécurisé à GCS.
2. Lire les données CSV depuis `gs://supdevinci_bucket/sanda_celia/raw/`.
3. Explorer et valider les données.

## ⚙️ **Configuration Préalable**

- **Python 3.12+** avec [uv](https://docs.astral.sh/uv/) (gestionnaire de packages).
- **Google Cloud SDK** (`gcloud`, `gsutil`) configuré.
- **Credentials GCP** avec permissions sur le projet `biforaplatform` et le bucket `gs://supdevinci_bucket/sanda_celia/`.
- **Terraform** installé si vous utilisez le script `deploy.sh`.

**Installation des dépendances Python :**
```bash
# Créer l'environnement (si pas fait)
uv venv --python 3.12
source .venv/bin/activate # ou équivalent

# Synchroniser les dépendances
uv sync
```

## 🎯 **Données Générées**

- **Format :** CSV avec 19 types d'opérations financières.
- **Volume :** 10 millions de lignes, environ 2GB.
- **Structure :** `id_mouvement,date_op,produit,type_op,montant,agence_id,pays`.

## 📖 **Documentation Détaillée**

- **[Rapport Technique (Sanda & Celia)](docs/RAPPORT_TECHNIQUE_GENERATION_DONNEES.md)** : Revivez notre première journée de développement et comprenez nos choix d'optimisation.
- **[Ancien Rapport de Debugging Dataflow](docs/RAPPORT_DEBOGAGE.md)** : Pour mémoire, les défis de l'approche Dataflow initiale.
- **[Aide-Mémoire Commandes GCP](docs/GCP_GCLOUD_CHEATSHEET.md)**.

## 🔗 **Intégration Databricks - Points Clés**

Le notebook `01_ingestion_brute_gcs.ipynb` utilise `dbutils.fs.ls` et `spark.read.csv` pour accéder aux données sur GCS. Assurez-vous que votre cluster Databricks a les permissions nécessaires (via un profil d'instance ou une configuration de service account) pour lire depuis le bucket `gs://supdevinci_bucket`.

Exemple de lecture dans Databricks (après configuration) :
```python
DATA_PATH = "gs://supdevinci_bucket/sanda_celia"
df_raw = spark.read \
    .option("header", "true") \
    .option("inferSchema", "false") \
    .csv(f"{DATA_PATH}/raw/*.csv")
df_raw.show()
```

## 💡 **Pourquoi cette solution locale plutôt que Dataflow ?**

Notre rapport technique détaille notre parcours, mais en résumé :
- **Performance Brute :** 3-5 minutes contre 30+ minutes.
- **Simplicité :** Moins de dépendances complexes et de configuration cloud.
- **Fiabilité :** Élimination des erreurs liées aux ressources et politiques GCP spécifiques à Dataflow.
- **Coût :** Pas de coût de compute pour la génération (uniquement stockage GCS).

Pour notre cas d'usage (génération massive de CSV), l'approche locale s'est avérée largement supérieure.

---

*Projet mené par Sanda ANDRIA & Celia HADJI - Optimisé pour uv ⚡*