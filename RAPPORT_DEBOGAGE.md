# 🚨 Rapport de Débogage - Pipeline GCP/Databricks
**Projet :** Générateur de Données Financières Synthétiques  
**Date :** 05 Juin 2025  
**Environnement :** Ubuntu 24.04 WSL2, Python 3.12, uv package manager  

---

## 📋 Résumé Exécutif

**Objectif :** Déployer un pipeline Apache Beam/Dataflow pour générer 10M lignes de données financières synthétiques (~2 Go) et les stocker dans Google Cloud Storage.

**Status Final :** ⚠️ **Pipeline fonctionnel mais bloqué par contraintes IAM organisationnelles**

**Temps de résolution :** ~2 heures de débogage intensif

---

## 🏗️ Architecture Mise en Place

### Structure Data Lake Créée
```
gs://supdevinci_bucket/sanda_celia/
├── tmp/              # Fichiers temporaires Dataflow  
├── raw/              # Données brutes CSV (sortie pipeline)
│   └── mouvements/   # Données financières générées
├── staging/          # Données optimisées Parquet (Databricks)  
│   └── mouvements/   # Tables optimisées
└── delta/            # Tables Delta (Databricks)
    └── mouvements/   # Tables Delta finales
```

### Configuration Technique
- **Projet GCP :** biforaplatform
- **Région :** europe-west1  
- **Bucket :** gs://supdevinci_bucket/sanda_celia
- **Volume cible :** 10M lignes → 5 fichiers de ~400MB
- **Secteur :** Financier/Assurance avec 19 types d'opérations

---

## 🚨 Problèmes Rencontrés et Solutions

### 1. **Erreur de structure des dossiers GCS**
**Problème :** Le script `create_gcs_structure.sh` ne créait pas les sous-dossiers.

**Erreur :**
```bash
./create_gcs_structure.sh:70: bad substitution
```

**Cause racine :** Syntaxe des tableaux associatifs incompatible entre bash et zsh.

**Solution appliquée :**
```bash
# Remplacement de la logique des tableaux associatifs par des fonctions simples
create_folder() {
    local folder_path=$1
    local description=$2
    echo "Dossier créé le $(date)" | gcloud storage cp - "$folder_path/.gitkeep"
}

# Création manuelle de chaque dossier
create_folder "$BUCKET_BASE/tmp" "tmp (fichiers temporaires)"
create_folder "$BUCKET_BASE/raw/mouvements" "raw/mouvements (données financières)"
# etc.
```

**Résultat :** ✅ Structure créée avec succès

---

### 2. **Erreur Application Default Credentials (ADC)**
**Problème :** Apache Beam ne trouvait pas les credentials pour s'authentifier.

**Erreur :**
```
google.auth.exceptions.DefaultCredentialsError: Your default credentials were not found
```

**Solutions tentées :**
1. `gcloud auth application-default login` → Échec (problème navigateur WSL2)
2. `gcloud auth application-default login --no-browser` → Interruption manuelle

**Solution finale :**
```bash
# Utilisation de la clé service account existante
export GOOGLE_APPLICATION_CREDENTIALS="$HOME/key-dataflow.json"
```

**Résultat :** ✅ Credentials détectés, token d'accès généré

---

### 3. **Erreur module pip manquant dans uv**
**Problème :** Dataflow ne trouvait pas pip dans l'environnement uv.

**Erreur :**
```
/home/exeio/.venv/bin/python3: No module named pip
Command '[...] -m pip freeze' returned non-zero exit status 1
```

**Solution :**
```bash
uv add pip
```

**Résultat :** ✅ Pip ajouté à l'environnement, erreur résolue

---

### 4. **Erreur permissions IAM Service Account**
**Problème :** L'utilisateur ne peut pas utiliser le service account Dataflow par défaut.

**Erreur :**
```
Current user cannot act as service account 115938710183-compute@developer.gserviceaccount.com
Enforced by Org Policy constraint constraints/dataflow.enforceComputeDefaultServiceAccountCheck
```

**Analyses effectuées :**
- Service account détecté : `dataflow-generator@biforaplatform.iam.gserviceaccount.com`
- Rôles vérifiés dans IAM policy
- Contraintes organisationnelles identifiées

**Solutions tentées :**

#### A. Ajout de permissions utilisateur
```bash
gcloud projects add-iam-policy-binding biforaplatform \
  --member="user:andrirazafy9@gmail.com" \
  --role="roles/iam.serviceAccountUser"
```
**Résultat :** ✅ Rôle ajouté mais contraintes org persistent

#### B. Configuration service account explicite
```python
gcloud_opts.service_account_email = "dataflow-generator@biforaplatform.iam.gserviceaccount.com"
```
**Résultat :** ❌ Même erreur de permissions

#### C. Utilisation credentials utilisateur
```python
# Suppression de la spécification du service account
# gcloud_opts.service_account_email = "..."
```
**Résultat :** ❌ Contrainte `dataflow.enforceComputeDefaultServiceAccountCheck` active

---

## 🔍 Analyse des Contraintes Organisationnelles

### Politiques IAM Détectées
D'après `gcloud projects get-iam-policy biforaplatform` :

1. **Contraintes temporelles :** Plusieurs rôles avec conditions d'expiration
2. **Contraintes Databricks :** Ressources protégées par conditions complexes  
3. **Politique org :** `constraints/dataflow.enforceComputeDefaultServiceAccountCheck`

### Configuration IAM Actuelle
```yaml
# Rôles utilisateur confirmés
- user:andrirazafy9@gmail.com → roles/owner
- user:andrirazafy9@gmail.com → roles/iam.serviceAccountUser

# Service accounts configurés  
- dataflow-generator@biforaplatform.iam.gserviceaccount.com → roles/dataflow.admin
- dataflow-generator@biforaplatform.iam.gserviceaccount.com → roles/dataflow.worker
- dataflow-generator@biforaplatform.iam.gserviceaccount.com → roles/storage.admin
```

---

## 🚦 État Final du Pipeline

### ✅ Éléments Fonctionnels
1. **Authentification :** Service account key fonctionnelle
2. **Structure GCS :** Dossiers créés et accessibles
3. **Code Pipeline :** Logique métier validée (19 types d'opérations)
4. **Environnement uv :** Dépendances installées correctement
5. **Upload Staging :** Fichiers pipeline uploadés avec succès

### ❌ Blocage Restant
**Contrainte organisationnelle :** `constraints/dataflow.enforceComputeDefaultServiceAccountCheck`

Cette contrainte empêche l'utilisation de service accounts par défaut et nécessite une intervention administrateur organisation GCP.

---

## 🎯 Solutions Recommandées

### Solution 1 : Résolution Administrative (Recommandée)
**Action :** Contacter l'administrateur GCP pour :
```bash
# Désactiver la contrainte organisationnelle
gcloud org-policies delete constraints/dataflow.enforceComputeDefaultServiceAccountCheck \
  --organization=ORGANIZATION_ID
```

### Solution 2 : Mode Local de Développement
**Action :** Utiliser DirectRunner pour tests :
```python
options.view_as(StandardOptions).runner = "DirectRunner"
```
**Limite :** Performance réduite, pas de parallélisation cloud

### Solution 3 : Migration vers un projet sans contraintes
**Action :** Créer un nouveau projet GCP dédié sans contraintes organisationnelles.

---

## 📊 Données de Test Générées

### Schema CSV Final
| Champ          | Type   | Description                 | Exemple                         |
| -------------- | ------ | --------------------------- | ------------------------------- |
| `id_mouvement` | string | Identifiant unique          | M0000001                        |
| `date_op`      | date   | Date de l'opération         | 2025-06-15                      |
| `produit`      | string | Type produit d'assurance    | auto, santé, habitation, vie    |
| `type_op`      | string | Type d'opération financière | cotisation, remboursement, etc. |
| `montant`      | float  | Montant en euros            | 1250.50                         |
| `agence_id`    | string | Identifiant agence          | AG_001                          |
| `pays`         | string | Code pays européen          | FR, ES, IT, DE, BE              |

### Types d'Opérations Implémentés (19 types)
- **Base :** cotisation, remboursement, commission
- **Ajustements :** rétrocession, ajustement_cotisation, régularisation  
- **Pénalités :** pénalité_retard, correction_comptable, annulation
- **Internes :** virement_interne, provision_sinistre, frais_gestion
- **Autres :** prime_exceptionnelle, bonus_malus, etc.

### Logique Métier des Montants
```python
# Exemples de distribution réaliste
cotisation: 50€ → 2500€ (positif)
remboursement: -100€ → -5000€ (négatif)  
pénalités: 15€ → 300€ (positif)
ajustements: -200€ → +200€ (bi-directionnel)
```

---

## 🔧 Configuration Technique Validée

### Environnement uv
```toml
[project]
name = "gcp-databricks-project"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "apache-beam[gcp]>=2.65.0",
    "faker>=37.3.0", 
    "pip>=25.1.1"
]
```

### Variables d'Environnement
```bash
export GOOGLE_APPLICATION_CREDENTIALS="$HOME/key-dataflow.json"
export GCP_PROJECT_ID="biforaplatform"  
export GCP_REGION="europe-west1"
```

### Commandes de Validation
```bash
# Test credentials
gcloud auth application-default print-access-token

# Test accès bucket  
gcloud storage ls gs://supdevinci_bucket/sanda_celia/

# Validation configuration
uv run python -c "from src.config import Config; Config.validate_config()"
```

---

## 📈 Métriques de Performance

### Uploads Réussis
```
✅ submission_environment_dependencies.txt (0 secondes)
✅ pipeline.pb (0-1 secondes)  
✅ Fichiers staging uploadés vers GCS
```

### Warnings Non-Critiques
```
⚠️ Bucket soft-delete policy enabled (facturation optimisable)
⚠️ Additional dependencies in SDK container (performance optimisable)
```

---

## 🚀 Prochaines Étapes

### Immédiat (Post-résolution contraintes)
1. **Lancer pipeline :** `uv run src/generate_to_gcs.py`
2. **Monitoring :** `gcloud dataflow jobs list --region=europe-west1`
3. **Validation :** `uv run src/verify_data.py --sample`

### Court terme
1. **Intégration Databricks :** Conversion CSV → Parquet → Delta
2. **Optimisation :** Partitioning par pays/produit  
3. **Monitoring :** Alertes et dashboards

### Long terme  
1. **Automatisation :** Cloud Scheduler pour génération mensuelle
2. **Pipeline ML :** Détection d'anomalies sur les données
3. **API :** Exposition des données via Cloud Functions

---

## 📚 Documentation Créée

### Fichiers de Configuration
- ✅ `src/config.py` - Configuration centralisée
- ✅ `src/generate_to_gcs.py` - Pipeline principal  
- ✅ `src/verify_data.py` - Utilitaires de validation
- ✅ `pyproject.toml` - Dépendances uv
- ✅ `README.md` - Documentation utilisateur (mise à jour uv)
- ✅ `create_gcs_structure.sh` - Script d'initialisation
- ✅ `GCP_GCLOUD_CHEATSHEET.md` - Commandes de référence

### Scripts Utilitaires
```bash
# Création structure
./create_gcs_structure.sh

# Vérification données  
uv run src/verify_data.py --stats

# Guide Databricks
uv run src/generate_to_gcs.py --guide
```

---

## 🎓 Enseignements Tirés

### Bonnes Pratiques
1. **uv vs pip :** uv offre des performances supérieures pour la gestion d'environnements
2. **Service Accounts :** Préférer les SAs dédiés aux credentials utilisateur
3. **Structure GCS :** Organisation claire Raw/Staging/Delta facilite l'intégration
4. **Monitoring :** Logs détaillés essentiels pour le débogage

### Pièges Évités  
1. **Syntaxe Shell :** Différences bash/zsh dans les scripts
2. **ADC vs SA Keys :** Confusion entre types d'authentification
3. **Contraintes Org :** Impact sur les permissions individuelles
4. **Environnements Python :** Spécificités uv vs virtualenv classique

### Améliorations Futures
1. **Tests Unitaires :** Validation logique métier
2. **CI/CD :** Automatisation déploiement  
3. **Infrastructure as Code :** Terraform pour ressources GCP
4. **Observabilité :** Métriques custom et alerting

---

## 📞 Support et Escalade

### Contacts Techniques
- **GCP Admin :** Résolution contraintes organisationnelles
- **Databricks Team :** Configuration intégration GCS
- **Équipe Projet :** andrirazafy9@gmail.com

### Ressources de Référence
- [Documentation Apache Beam](https://beam.apache.org/documentation/)
- [GCP IAM Troubleshooting](https://cloud.google.com/iam/docs/troubleshooting)
- [uv Documentation](https://docs.astral.sh/uv/)
- [Databricks GCS Integration](https://docs.databricks.com/external-data/gcs.html)

---

**Fin du Rapport - Préparé avec ❤️ et beaucoup de café ☕**

*Ce rapport documumente 2h de débogage intensif et constitue une base de connaissance pour les futurs projets similaires.* 