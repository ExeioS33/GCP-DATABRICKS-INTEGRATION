#!/bin/bash

# ========================================
# SCRIPT DE DÉPLOIEMENT AUTOMATISÉ
# Pipeline GCP/Databricks - Infrastructure as Code
# ========================================

set -e  # Arrêt en cas d'erreur

# Couleurs pour les logs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonctions utilitaires
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# ========================================
# VÉRIFICATIONS PRÉALABLES
# ========================================

log_info "🔍 Vérification des prérequis..."

# Vérifier Terraform
if ! command -v terraform &> /dev/null; then
    log_error "Terraform n'est pas installé"
    exit 1
fi

# Vérifier gcloud
if ! command -v gcloud &> /dev/null; then
    log_error "gcloud CLI n'est pas installé"
    exit 1
fi

# Vérifier uv
if ! command -v uv &> /dev/null; then
    log_error "uv n'est pas installé"
    exit 1
fi

# Vérifier l'authentification GCP
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "@"; then
    log_error "Vous n'êtes pas authentifié sur GCP"
    log_info "Exécutez: gcloud auth login"
    exit 1
fi

log_success "✅ Tous les prérequis sont satisfaits"

# ========================================
# CONFIGURATION TERRAFORM
# ========================================

log_info "🏗️ Configuration de l'infrastructure..."

# Créer le fichier terraform.tfvars s'il n'existe pas
if [ ! -f "terraform/terraform.tfvars" ]; then
    log_warning "Fichier terraform.tfvars non trouvé, création à partir de l'exemple..."
    cp terraform/terraform.tfvars.example terraform/terraform.tfvars
    log_info "📝 Éditez terraform/terraform.tfvars si nécessaire"
fi

# Aller dans le dossier terraform
cd terraform

# Initialiser Terraform
log_info "🔧 Initialisation de Terraform..."
terraform init

# Planifier les changements
log_info "📋 Planification des changements..."
terraform plan

# Demander confirmation
echo -e "\n${YELLOW}Voulez-vous appliquer ces changements ? (y/N)${NC}"
read -r response
if [[ ! "$response" =~ ^[Yy]$ ]]; then
    log_info "Déploiement annulé"
    exit 0
fi

# Appliquer les changements
log_info "🚀 Application des changements..."
terraform apply -auto-approve

# Récupérer les outputs
log_info "📤 Récupération des informations de déploiement..."
SERVICE_ACCOUNT_EMAIL=$(terraform output -raw service_account_email)
BUCKET_URL=$(terraform output -raw bucket_url)
SERVICE_ACCOUNT_KEY=$(terraform output -raw service_account_key)

log_success "✅ Infrastructure déployée avec succès"
log_info "📧 Service Account: $SERVICE_ACCOUNT_EMAIL"
log_info "🪣 Bucket URL: $BUCKET_URL"

# Retourner au dossier racine
cd ..

# ========================================
# CONFIGURATION DES CREDENTIALS
# ========================================

log_info "🔑 Configuration des credentials..."

# Créer le fichier de clé
echo "$SERVICE_ACCOUNT_KEY" | base64 -d > key-dataflow.json
chmod 600 key-dataflow.json

# Exporter la variable d'environnement
export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/key-dataflow.json"

log_success "✅ Credentials configurés"

# ========================================
# INSTALLATION DES DÉPENDANCES PYTHON
# ========================================

log_info "🐍 Installation des dépendances Python..."

# Synchroniser l'environnement uv
uv sync

log_success "✅ Dépendances installées"

# ========================================
# LANCEMENT DU PIPELINE (OPTIONNEL)
# ========================================

echo -e "\n${YELLOW}Voulez-vous lancer le pipeline maintenant ? (y/N)${NC}"
read -r response
if [[ "$response" =~ ^[Yy]$ ]]; then
    log_info "🚀 Lancement du pipeline de génération de données..."
    
    # Lancer le pipeline
    GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/key-dataflow.json" uv run src/generate_to_gcs.py
    
    log_success "✅ Pipeline lancé avec succès"
    log_info "📊 Surveillez le progress sur: https://console.cloud.google.com/dataflow"
fi

# ========================================
# INFORMATIONS FINALES
# ========================================

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}🎉 DÉPLOIEMENT TERMINÉ AVEC SUCCÈS${NC}"
echo -e "${GREEN}========================================${NC}"

echo -e "\n📋 ${BLUE}Informations utiles:${NC}"
echo -e "   🔑 Service Account: $SERVICE_ACCOUNT_EMAIL"
echo -e "   🪣 Bucket: $BUCKET_URL"
echo -e "   📁 Credentials: $(pwd)/key-dataflow.json"

echo -e "\n📝 ${BLUE}Commandes utiles:${NC}"
echo -e "   # Lancer le pipeline"
echo -e "   export GOOGLE_APPLICATION_CREDENTIALS=\"$(pwd)/key-dataflow.json\""
echo -e "   uv run src/generate_to_gcs.py"
echo -e ""
echo -e "   # Monitoring Dataflow"
echo -e "   gcloud dataflow jobs list --region=europe-west1"
echo -e ""
echo -e "   # Guide Databricks"
echo -e "   uv run src/generate_to_gcs.py --guide"

echo -e "\n🔧 ${BLUE}Gestion de l'infrastructure:${NC}"
echo -e "   # Voir l'état Terraform"
echo -e "   cd terraform && terraform show"
echo -e ""
echo -e "   # Détruire l'infrastructure"
echo -e "   cd terraform && terraform destroy"

echo -e "\n${YELLOW}⚠️  N'oubliez pas de sauvegarder le fichier key-dataflow.json${NC}" 