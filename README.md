# 🚀 Générateur de Données Synthétiques GCP/Databricks

Ce projet génère des données synthétiques de mouvements financiers dans Google Cloud Storage (GCS) en utilisant Apache Beam/Dataflow, optimisé pour une intégration avec Databricks.

## 📊 Architecture du Data Lake

```
gs://supdevinci_bucket/sanda_celia/
├── tmp/           # Fichiers temporaires Dataflow
├── raw/           # Données brutes (CSV) - Sortie de ce script
├── staging/       # Données optimisées (Parquet) - Via Databricks
└── delta/         # Tables Delta - Via Databricks
```

## 🛠️ Installation

### 1. Prérequis
- Python 3.12+
- [uv](https://docs.astral.sh/uv/) - Gestionnaire de packages et environnements Python ultra-rapide
- Compte GCP avec Dataflow API activée
- Bucket GCS créé : `gs://supdevinci_bucket/sanda_celia/`
- gcloud CLI configuré

### 2. Installation d'uv (si pas déjà fait)
```bash
# Installation d'uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Ou via pip si vous préférez
pip install uv
```

### 3. Configuration de l'environnement Python
```bash
# Créer et activer l'environnement virtuel avec uv
uv venv --python 3.12

# Activer l'environnement (Linux/macOS)
source .venv/bin/activate

# Activer l'environnement (Windows)
# .venv\Scripts\activate

# Installer les dépendances avec uv
uv sync
```

### 4. Configuration GCP
```bash
# Authentification
gcloud auth application-default login

# Configuration du projet (remplacez par votre PROJECT_ID)
gcloud config set project YOUR_PROJECT_ID
```

## ⚙️ Configuration

Modifiez le fichier `src/config.py` :

```python
class Config:
    PROJECT_ID = "biforaplatform"  # ⚠️ Modifiez avec votre PROJECT_ID
    REGION = "europe-west1"        # Région de votre choix
    # ... autres paramètres
```

Ou utilisez les variables d'environnement :
```bash
export GCP_PROJECT_ID="biforaplatform"
export GCP_REGION="europe-west1"
export GCS_BUCKET_BASE="gs://supdevinci_bucket/sanda_celia"
```

## 🚀 Utilisation

### Génération des données
```bash
# Avec uv (recommandé)
uv run src/generate_to_gcs.py

# Ou si l'environnement est activé
python src/generate_to_gcs.py
```

### Afficher le guide Databricks
```bash
uv run src/generate_to_gcs.py --guide
```

### Vérification des données générées
```bash
# Vérification basique
uv run src/verify_data.py

# Avec échantillon des données
uv run src/verify_data.py --sample

# Avec statistiques détaillées
uv run src/verify_data.py --stats
```

## 📈 Structure des Données Générées

### Schema CSV
| Champ          | Type   | Description                     | Exemple                         |
| -------------- | ------ | ------------------------------- | ------------------------------- |
| `id_mouvement` | string | Identifiant unique du mouvement | M0000001                        |
| `date_op`      | date   | Date de l'opération             | 2025-06-15                      |
| `produit`      | string | Type de produit d'assurance     | auto, santé, habitation, vie    |
| `type_op`      | string | Type d'opération financière     | cotisation, remboursement, etc. |
| `montant`      | float  | Montant de l'opération (€)      | 1250.50                         |
| `agence_id`    | string | Identifiant de l'agence         | AG_001                          |
| `pays`         | string | Code pays                       | FR, ES, IT, DE, BE              |

### Types d'opérations financières (19 types)
- **Opérations de base** : cotisation, remboursement, commission
- **Ajustements** : rétrocession, ajustement, régularisation
- **Pénalités** : pénalité, correction, annulation
- **Opérations internes** : virement, provision, réassurance
- **Autres** : frais_gestion, prime_exceptionnelle, bonus_malus, etc.

## 🏗️ Architecture Technique

### Pipeline de données
1. **Génération** (Apache Beam/Dataflow) → GCS RAW (CSV)
2. **Transformation** (Databricks) → GCS STAGING (Parquet)
3. **Optimisation** (Databricks) → GCS DELTA (Tables Delta)

### Volumes et performances
- **Volume cible** : ~10M lignes/mois (~2 Go)
- **Fichiers de sortie** : 5 fichiers de ~400MB chacun
- **Format initial** : CSV avec entêtes
- **Partitioning Databricks** : Par pays et produit

## 🔧 Commandes utiles avec uv

### Gestion de l'environnement
```bash
# Créer un nouvel environnement
uv venv --python 3.12

# Installer une nouvelle dépendance
uv add apache-beam[gcp]

# Installer en mode développement
uv add --dev pytest

# Synchroniser les dépendances
uv sync

# Exécuter un script
uv run src/generate_to_gcs.py

# Ouvrir un shell Python dans l'environnement
uv run python
```

### Tests et développement
```bash
# Installer les dépendances de test
uv add --dev pytest pytest-cov

# Exécuter les tests
uv run pytest

# Linter le code
uv add --dev ruff
uv run ruff check src/
```

## 📁 Gestion des fichiers GCS

### Commandes gcloud utiles
```bash
# Lister la structure complète
gcloud storage ls --recursive gs://supdevinci_bucket/sanda_celia/

# Vérifier la taille des dossiers
gcloud storage du gs://supdevinci_bucket/sanda_celia/raw/

# Télécharger un échantillon
gcloud storage cp gs://supdevinci_bucket/sanda_celia/raw/mouvements-00000-of-00005.csv ./sample.csv

# Supprimer toute la structure (si nécessaire)
gcloud storage rm --recursive gs://supdevinci_bucket/sanda_celia/
```

## 🔗 Intégration Databricks

### Configuration de l'accès GCS
1. **Service Account** : Créer un SA avec accès au bucket
2. **Secrets Databricks** : Stocker les clés JSON
3. **Montage GCS** : Configurer l'accès au bucket

### Exemples de code Databricks
```python
# Lecture des données CSV
df = spark.read.option("header", "true") \
    .csv("gs://supdevinci_bucket/sanda_celia/raw/mouvements-*.csv")

# Sauvegarde optimisée en Parquet
df.write.mode("overwrite") \
  .partitionBy("pays", "produit") \
  .parquet("gs://supdevinci_bucket/sanda_celia/staging/mouvements")

# Conversion en Delta Table
df.write.format("delta") \
  .mode("overwrite") \
  .save("gs://supdevinci_bucket/sanda_celia/delta/mouvements")
```

## 📊 Analyses possibles

### Exemples d'analyses métier
- **Détection d'anomalies** : Montants exceptionnels par type d'opération
- **Analyse des rétrocessions** : Suivi par agence et pays
- **Tendances temporelles** : Évolution des cotisations et remboursements
- **Performance des agences** : Volumes et types d'opérations
- **Conformité** : Suivi des pénalités et corrections

## 🚨 Dépannage

### Erreurs courantes
```bash
# Erreur d'authentification GCP
gcloud auth application-default login

# Erreur de projet GCP
gcloud config set project YOUR_PROJECT_ID

# Erreur de permissions bucket
gcloud storage buckets get-iam-policy gs://supdevinci_bucket

# Réinstaller les dépendances
uv sync --reinstall
```

### Variables d'environnement
```bash
# Définir le projet GCP
export GCP_PROJECT_ID="biforaplatform"
export GCP_REGION="europe-west1"

# Vérifier la configuration
uv run python -c "from src.config import Config; print(f'Project: {Config.PROJECT_ID}')"
```

## 📚 Ressources

### Documentation
- [Apache Beam Python SDK](https://beam.apache.org/documentation/sdks/python/)
- [Google Cloud Dataflow](https://cloud.google.com/dataflow/docs)
- [uv Documentation](https://docs.astral.sh/uv/)
- [Databricks on GCP](https://docs.databricks.com/en/getting-started/overview.html)

### Liens utiles
- [Faker Documentation](https://faker.readthedocs.io/) - Génération de données synthétiques
- [GCS Best Practices](https://cloud.google.com/storage/docs/best-practices)
- [Delta Lake Guide](https://docs.delta.io/latest/index.html)

## 🏗️ Infrastructure as Code (IaC)

### 🚀 Déploiement automatisé avec Terraform

Pour éviter toutes les configurations manuelles, utilisez le déploiement automatisé :

```bash
# Installation de Terraform (si pas déjà fait)
# Sur Ubuntu/Debian :
wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt update && sudo apt install terraform

# Ou avec Homebrew (macOS) :
# brew install terraform

# Authentification GCP (une seule fois)
gcloud auth login
gcloud auth application-default login

# Déploiement complet en une commande
./deploy.sh
```

### 📁 Structure Infrastructure as Code

```
terraform/
├── main.tf                    # Configuration principale Terraform
├── terraform.tfvars.example  # Variables d'exemple
└── terraform.tfvars          # Vos variables (créé automatiquement)

deploy.sh                     # Script de déploiement automatisé
```

### 🎯 Ce que Terraform déploie automatiquement

1. **Service Account** `dataflow-generator` avec toutes les permissions
2. **Rôles IAM** pour utilisateur et service account
3. **APIs GCP** (Dataflow, Storage, BigQuery, IAM)
4. **Structure GCS** (tmp/, raw/, staging/, delta/)
5. **Organization Policy** (désactivation contrainte Dataflow)
6. **Lifecycle rules** pour optimisation des coûts
7. **Credentials** automatiquement générés

### 🔧 Gestion de l'infrastructure

```bash
# Voir l'état actuel
cd terraform && terraform show

# Planifier des changements
cd terraform && terraform plan

# Appliquer des changements
cd terraform && terraform apply

# Détruire l'infrastructure
cd terraform && terraform destroy
```

### 💡 Avantages de l'approche IaC

- ✅ **Reproductible** : Déploiement identique sur différents environnements
- ✅ **Versionnable** : Infrastructure sous contrôle de version Git
- ✅ **Auditable** : Traçabilité complète des changements
- ✅ **Scalable** : Facilement adaptable pour d'autres projets
- ✅ **Sécurisé** : Permissions minimales et bonnes pratiques
- ✅ **Automatisé** : Zéro configuration manuelle

## 📊 Monitoring et Observabilité

### 🔍 Surveillance du pipeline

```bash
# Status des jobs Dataflow
gcloud dataflow jobs list --region=europe-west1

# Logs détaillés d'un job
gcloud dataflow jobs show JOB_ID --region=europe-west1

# Métriques temps réel
gcloud dataflow jobs show JOB_ID --region=europe-west1 --view=JOB_VIEW_ALL
```

### 📈 Dashboards recommandés

1. **Console Dataflow** : https://console.cloud.google.com/dataflow
2. **Cloud Monitoring** : Métriques custom et alertes
3. **Cloud Logging** : Recherche et analyse des logs
4. **Cost Management** : Suivi des coûts GCS et Dataflow

---

*Projet optimisé pour uv - Gestionnaire de packages Python ultra-rapide* ⚡

*Dernière mise à jour: Janvier 2025*