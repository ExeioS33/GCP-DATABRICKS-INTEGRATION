# 🚀 GCP gcloud CLI - Cheat Sheet Complet

Guide des commandes essentielles pour interagir avec Google Cloud Platform via gcloud CLI.

## 📋 Table des Matières

1. [Configuration initiale](#-configuration-initiale)
2. [Gestion des projets](#-gestion-des-projets)
3. [Google Cloud Storage (GCS)](#-google-cloud-storage-gcs)
4. [Création de l'architecture du projet](#-création-de-larchitecture-du-projet)
5. [Gestion des fichiers](#-gestion-des-fichiers)
6. [Permissions et IAM](#-permissions-et-iam)
7. [Dataflow](#-dataflow)
8. [Monitoring et Logs](#-monitoring-et-logs)
9. [Dépannage](#-dépannage)

---

## 🔧 Configuration initiale

### Installation et authentification
```bash
# Installer gcloud SDK (si pas déjà fait)
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# Initialiser gcloud
gcloud init

# Authentification
gcloud auth login
gcloud auth application-default login

# Vérifier la configuration actuelle
gcloud config list
gcloud info

# Définir le projet par défaut
gcloud config set project VOTRE_PROJECT_ID

# Définir la région par défaut
gcloud config set compute/region europe-west1
gcloud config set compute/zone europe-west1-b
```

### Gestion des configurations
```bash
# Créer une nouvelle configuration
gcloud config configurations create ma-config

# Lister les configurations
gcloud config configurations list

# Activer une configuration
gcloud config configurations activate ma-config

# Afficher la configuration active
gcloud config configurations describe ma-config
```

---

## 🏗️ Gestion des projets

### Projets
```bash
# Lister tous les projets
gcloud projects list

# Créer un nouveau projet
gcloud projects create NOUVEAU_PROJECT_ID --name="Nom du projet"

# Obtenir les détails d'un projet
gcloud projects describe PROJECT_ID

# Définir le projet actuel
gcloud config set project PROJECT_ID

# Activer des APIs
gcloud services enable storage.googleapis.com
gcloud services enable dataflow.googleapis.com
gcloud services enable compute.googleapis.com

# Lister les APIs activées
gcloud services list --enabled
```

### Facturation
```bash
# Lister les comptes de facturation
gcloud billing accounts list

# Lier un projet à un compte de facturation
gcloud billing projects link PROJECT_ID --billing-account=BILLING_ACCOUNT_ID
```

---

## 💾 Google Cloud Storage (GCS)

### Gestion des buckets
```bash
# Lister tous les buckets
gcloud storage ls

# Lister les buckets d'un projet spécifique
gcloud storage ls --project=VOTRE_PROJECT_ID

# Créer un bucket
gcloud storage buckets create gs://nom-du-bucket --location=europe-west1

# Créer un bucket avec classe de stockage spécifique
gcloud storage buckets create gs://nom-du-bucket \
  --location=europe-west1 \
  --default-storage-class=STANDARD

# Obtenir les détails d'un bucket
gcloud storage buckets describe gs://nom-du-bucket

# Supprimer un bucket (doit être vide)
gcloud storage buckets delete gs://nom-du-bucket
```

### Gestion des objets et dossiers
```bash
# Lister le contenu d'un bucket
gcloud storage ls gs://nom-du-bucket/

# Lister récursivement
gcloud storage ls --recursive gs://nom-du-bucket/

# Créer un "dossier" (en uploadant un fichier placeholder)
echo "" | gcloud storage cp - gs://nom-du-bucket/dossier/.gitkeep

# Uploader un fichier
gcloud storage cp fichier-local.txt gs://nom-du-bucket/

# Uploader un dossier complet
gcloud storage cp --recursive dossier-local/ gs://nom-du-bucket/dossier-distant/

# Télécharger un fichier
gcloud storage cp gs://nom-du-bucket/fichier.txt ./

# Télécharger un dossier complet
gcloud storage cp --recursive gs://nom-du-bucket/dossier/ ./dossier-local/

# Déplacer/Renommer un fichier
gcloud storage mv gs://bucket/ancien-nom.txt gs://bucket/nouveau-nom.txt

# Supprimer un fichier
gcloud storage rm gs://nom-du-bucket/fichier.txt

# Supprimer un dossier et son contenu
gcloud storage rm --recursive gs://nom-du-bucket/dossier/
```

### Informations sur les objets
```bash
# Afficher la taille d'un dossier
gcloud storage du gs://nom-du-bucket/dossier/

# Afficher la taille avec résumé
gcloud storage du --summarize gs://nom-du-bucket/

# Afficher les détails d'un fichier
gcloud storage ls --long gs://nom-du-bucket/fichier.txt

# Afficher le contenu d'un fichier
gcloud storage cat gs://nom-du-bucket/fichier.txt

# Afficher les premières lignes d'un fichier
gcloud storage cat gs://nom-du-bucket/fichier.txt | head -10
```

---

## 🏗️ Création de l'architecture du projet

### Création des sous-dossiers pour supdevinci_bucket/sanda_celia/

```bash
# Vérifier que le bucket existe
gcloud storage ls gs://supdevinci_bucket/

# Créer la structure de dossiers pour le projet
# Méthode 1: Créer des fichiers .gitkeep pour marquer les dossiers
echo "Dossier temporaire pour Dataflow" | gcloud storage cp - gs://supdevinci_bucket/sanda_celia/tmp/.gitkeep
echo "Données brutes CSV générées" | gcloud storage cp - gs://supdevinci_bucket/sanda_celia/raw/.gitkeep  
echo "Données optimisées Parquet" | gcloud storage cp - gs://supdevinci_bucket/sanda_celia/staging/.gitkeep
echo "Tables Delta Databricks" | gcloud storage cp - gs://supdevinci_bucket/sanda_celia/delta/.gitkeep

# Méthode 2: Créer des dossiers vides (plus propre)
printf "" | gcloud storage cp - gs://supdevinci_bucket/sanda_celia/tmp/
printf "" | gcloud storage cp - gs://supdevinci_bucket/sanda_celia/raw/
printf "" | gcloud storage cp - gs://supdevinci_bucket/sanda_celia/staging/
printf "" | gcloud storage cp - gs://supdevinci_bucket/sanda_celia/delta/

# Vérifier la structure créée
gcloud storage ls gs://supdevinci_bucket/sanda_celia/

# Lister de façon récursive pour voir tous les sous-dossiers
gcloud storage ls --recursive gs://supdevinci_bucket/sanda_celia/
```

### Script automatisé pour créer l'architecture
```bash
#!/bin/bash
# Script pour créer l'architecture complète du projet

BUCKET_BASE="gs://supdevinci_bucket/sanda_celia"

echo "🏗️ Création de l'architecture du projet Data Lake..."

# Créer les dossiers principaux
folders=("tmp" "raw" "staging" "delta")

for folder in "${folders[@]}"; do
    echo "📁 Création du dossier: $folder"
    printf "" | gcloud storage cp - "$BUCKET_BASE/$folder/"
done

# Créer des sous-dossiers spécifiques si nécessaire
echo "📁 Création des sous-dossiers métier..."
printf "" | gcloud storage cp - "$BUCKET_BASE/raw/mouvements/"
printf "" | gcloud storage cp - "$BUCKET_BASE/staging/mouvements/"
printf "" | gcloud storage cp - "$BUCKET_BASE/delta/mouvements/"

echo "✅ Architecture créée avec succès!"
echo "📋 Vérification de la structure:"
gcloud storage ls --recursive "$BUCKET_BASE/"
```

---

## 📁 Gestion des fichiers

### Opérations avancées
```bash
# Synchroniser un dossier local avec GCS
gcloud storage rsync dossier-local/ gs://bucket/dossier-distant/ --recursive

# Synchroniser avec suppression des fichiers absents
gcloud storage rsync dossier-local/ gs://bucket/dossier-distant/ --recursive --delete-unmatched-destination-objects

# Copier avec métadonnées personnalisées
gcloud storage cp fichier.txt gs://bucket/ --custom-metadata=key1=value1,key2=value2

# Définir le type de contenu
gcloud storage cp image.jpg gs://bucket/ --content-type=image/jpeg

# Copier uniquement les fichiers modifiés
gcloud storage cp --recursive dossier/ gs://bucket/ --skip-if-exists
```

### Recherche et filtrage
```bash
# Chercher des fichiers par extension
gcloud storage ls gs://bucket/**/*.csv

# Chercher avec wildcards
gcloud storage ls gs://bucket/data-202*

# Lister avec informations détaillées
gcloud storage ls --long --readable-sizes gs://bucket/

# Lister uniquement les fichiers (pas les dossiers)
gcloud storage ls gs://bucket/ | grep -v '/$'
```

---

## 🔐 Permissions et IAM

### Gestion des permissions sur les buckets
```bash
# Voir les permissions IAM d'un bucket
gcloud storage buckets get-iam-policy gs://nom-du-bucket

# Donner accès lecture à un utilisateur
gcloud storage buckets add-iam-policy-binding gs://nom-du-bucket \
  --member=user:email@domain.com \
  --role=roles/storage.objectViewer

# Donner accès admin à un service account
gcloud storage buckets add-iam-policy-binding gs://nom-du-bucket \
  --member=serviceAccount:sa@project.iam.gserviceaccount.com \
  --role=roles/storage.admin

# Retirer une permission
gcloud storage buckets remove-iam-policy-binding gs://nom-du-bucket \
  --member=user:email@domain.com \
  --role=roles/storage.objectViewer
```

### Service Accounts
```bash
# Créer un service account
gcloud iam service-accounts create dataflow-sa \
  --display-name="Service Account Dataflow"

# Lister les service accounts
gcloud iam service-accounts list

# Donner des rôles à un service account
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:dataflow-sa@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/dataflow.worker"

# Créer une clé pour un service account
gcloud iam service-accounts keys create key.json \
  --iam-account=dataflow-sa@PROJECT_ID.iam.gserviceaccount.com
```

---

## 🌊 Dataflow

### Gestion des jobs Dataflow
```bash
# Lister les jobs Dataflow
gcloud dataflow jobs list --region=europe-west1

# Voir les détails d'un job
gcloud dataflow jobs describe JOB_ID --region=europe-west1

# Annuler un job
gcloud dataflow jobs cancel JOB_ID --region=europe-west1

# Voir les logs d'un job
gcloud dataflow jobs show JOB_ID --region=europe-west1

# Lancer un job à partir d'un template
gcloud dataflow jobs run mon-job \
  --gcs-location=gs://dataflow-templates/latest/Word_Count \
  --region=europe-west1 \
  --parameters=inputFile=gs://bucket/input.txt,output=gs://bucket/output
```

---

## 📊 Monitoring et Logs

### Logs
```bash
# Voir les logs d'un projet
gcloud logging logs list

# Lire les logs récents
gcloud logging read "timestamp >= \"2024-01-01T00:00:00Z\""

# Filtrer les logs par service
gcloud logging read "resource.type=dataflow_job"

# Logs en temps réel
gcloud logging tail
```

### Métriques
```bash
# Lister les métriques disponibles
gcloud monitoring metrics list

# Obtenir des métriques de storage
gcloud monitoring metrics list --filter="metric.type:storage"
```

---

## 🔍 Dépannage

### Diagnostic
```bash
# Vérifier la connectivité
gcloud auth list
gcloud config list

# Tester l'accès à un bucket
gcloud storage ls gs://bucket-test 2>&1 | head -5

# Vérifier les quotas
gcloud compute project-info describe --format="table(quotas.metric,quotas.usage,quotas.limit)"

# Vérifier les APIs activées
gcloud services list --enabled --filter="storage"

# Obtenir de l'aide sur une commande
gcloud storage --help
gcloud storage cp --help
```

### Erreurs courantes et solutions
```bash
# Erreur 403 - Permissions insuffisantes
gcloud auth application-default login
gcloud auth login --update-adc

# Erreur de projet non trouvé
gcloud config set project CORRECT_PROJECT_ID

# Vérifier les permissions sur un bucket
gcloud storage buckets get-iam-policy gs://bucket-name

# Tester avec un autre utilisateur/service account
gcloud config set account autre-compte@domain.com
```

---

## 💡 Astuces et bonnes pratiques

### Optimisation des performances
```bash
# Utiliser des transferts parallèles pour gros volumes
gcloud storage cp --recursive dossier/ gs://bucket/ -j 10

# Utiliser la compression pour réduire les coûts
gcloud storage cp fichier.txt gs://bucket/ --gzip-in-flight

# Définir la classe de stockage à l'upload
gcloud storage cp fichier.txt gs://bucket/ --storage-class=NEARLINE
```

### Sécurité
```bash
# Activer le versioning sur un bucket
gcloud storage buckets update gs://bucket --versioning

# Définir une politique de rétention
gcloud storage buckets update gs://bucket --retention-period=30d

# Activer les logs d'audit
gcloud logging sinks create storage-audit-logs \
  bigquery.googleapis.com/projects/PROJECT_ID/datasets/audit_logs \
  --log-filter="resource.type=gcs_bucket"
```

---

## 📚 Ressources supplémentaires

- [Documentation officielle gcloud](https://cloud.google.com/sdk/gcloud)
- [Guide Cloud Storage](https://cloud.google.com/storage/docs)
- [Référence gcloud storage](https://cloud.google.com/sdk/gcloud/reference/storage)
- [Bonnes pratiques GCS](https://cloud.google.com/storage/docs/best-practices)

---

*Dernière mise à jour: $(date)* 