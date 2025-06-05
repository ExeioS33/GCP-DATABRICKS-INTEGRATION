#!/bin/zsh

# Script pour créer l'architecture complète du projet GCP/Databricks
# Usage: ./create_gcs_structure.sh

set -e  # Arrêter le script en cas d'erreur

# Configuration
BUCKET_BASE="gs://supdevinci_bucket/sanda_celia"
PROJECT_ID="biforaplatform"  # Remplacez par votre PROJECT_ID

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Création de l'architecture Data Lake GCP/Databricks${NC}"
echo -e "${BLUE}====================================================${NC}\n"

# Vérification des prérequis
echo -e "${YELLOW}🔍 Vérification des prérequis...${NC}"

# Vérifier que gcloud est installé
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI n'est pas installé${NC}"
    exit 1
fi

# Vérifier l'authentification
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -1 > /dev/null; then
    echo -e "${RED}❌ Vous n'êtes pas authentifié avec gcloud${NC}"
    echo -e "${YELLOW}💡 Exécutez: gcloud auth login${NC}"
    exit 1
fi

echo -e "${GREEN}✅ gcloud CLI configuré et authentifié${NC}"

# Définir le projet si nécessaire
echo -e "${YELLOW}📋 Configuration du projet...${NC}"
gcloud config set project $PROJECT_ID

# Vérifier l'accès au bucket principal
echo -e "${YELLOW}🔍 Vérification de l'accès au bucket...${NC}"
if gcloud storage ls gs://supdevinci_bucket/ > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Accès au bucket supdevinci_bucket confirmé${NC}"
else
    echo -e "${RED}❌ Impossible d'accéder au bucket gs://supdevinci_bucket/${NC}"
    echo -e "${YELLOW}💡 Vérifiez que le bucket existe et que vous avez les permissions${NC}"
    exit 1
fi

# Création de l'architecture des dossiers
echo -e "\n${BLUE}🏗️ Création de l'architecture du projet...${NC}"

# Fonction pour créer un dossier dans GCS
create_folder() {
    local folder_path=$1
    local description=$2
    echo -e "${YELLOW}📁 Création du dossier: $description${NC}"
    
    # Créer un fichier vide pour marquer le dossier
    echo "Dossier créé le $(date)" | gcloud storage cp - "$folder_path/.gitkeep" 2>/dev/null || {
        echo -e "${RED}❌ Erreur lors de la création de: $folder_path${NC}"
        return 1
    }
    echo -e "${GREEN}✅ Dossier créé: $folder_path${NC}"
}

# Créer tous les dossiers un par un
create_folder "$BUCKET_BASE/tmp" "tmp (fichiers temporaires Dataflow)"
create_folder "$BUCKET_BASE/raw" "raw (données brutes CSV)"
create_folder "$BUCKET_BASE/raw/mouvements" "raw/mouvements (données financières)"
create_folder "$BUCKET_BASE/staging" "staging (données optimisées Parquet)"
create_folder "$BUCKET_BASE/staging/mouvements" "staging/mouvements (tables optimisées)"
create_folder "$BUCKET_BASE/delta" "delta (tables Delta)"
create_folder "$BUCKET_BASE/delta/mouvements" "delta/mouvements (tables Delta finales)"

# Vérification de la structure créée
echo -e "\n${BLUE}📋 Vérification de la structure créée...${NC}"
echo -e "${YELLOW}Structure du bucket:${NC}"

# Lister la structure complète
gcloud storage ls --recursive "$BUCKET_BASE/" | head -20

echo -e "\n${GREEN}✅ Architecture créée avec succès!${NC}"

# Compter les dossiers créés
folder_count=$(gcloud storage ls --recursive "$BUCKET_BASE/" | grep "\.gitkeep" | wc -l)
echo -e "${GREEN}📂 Nombre de dossiers créés: $folder_count${NC}"

# Affichage du résumé
echo -e "\n${BLUE}📊 Résumé de l'architecture créée:${NC}"
echo -e "${GREEN}├── tmp/              ${NC}→ Fichiers temporaires Dataflow"
echo -e "${GREEN}├── raw/              ${NC}→ Données brutes CSV (sortie du pipeline)"
echo -e "${GREEN}│   └── mouvements/   ${NC}→ Données financières générées"
echo -e "${GREEN}├── staging/          ${NC}→ Données optimisées Parquet (Databricks)"
echo -e "${GREEN}│   └── mouvements/   ${NC}→ Tables optimisées"
echo -e "${GREEN}└── delta/            ${NC}→ Tables Delta (Databricks)"
echo -e "${GREEN}    └── mouvements/   ${NC}→ Tables Delta finales"

# Prochaines étapes
echo -e "\n${BLUE}🔄 Prochaines étapes:${NC}"
echo -e "${YELLOW}1.${NC} Configurer votre PROJECT_ID dans src/config.py"
echo -e "${YELLOW}2.${NC} Exécuter le pipeline de génération: ${GREEN}python src/generate_to_gcs.py${NC}"
echo -e "${YELLOW}3.${NC} Vérifier les données: ${GREEN}python src/verify_data.py --sample${NC}"
echo -e "${YELLOW}4.${NC} Configurer Databricks pour accéder à: ${GREEN}$BUCKET_BASE${NC}"

# Commandes utiles
echo -e "\n${BLUE}💡 Commandes utiles:${NC}"
echo -e "${YELLOW}# Lister la structure complète:${NC}"
echo -e "${GREEN}gcloud storage ls --recursive $BUCKET_BASE/${NC}"
echo -e "\n${YELLOW}# Vérifier la taille des dossiers:${NC}"
echo -e "${GREEN}gcloud storage du $BUCKET_BASE/raw/${NC}"
echo -e "\n${YELLOW}# Supprimer toute la structure (si nécessaire):${NC}"
echo -e "${GREEN}gcloud storage rm --recursive $BUCKET_BASE/${NC}"

echo -e "\n${GREEN}🎉 Script terminé avec succès!${NC}" 