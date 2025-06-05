# Rapport Technique : Génération de Données Synthétiques pour GCP/Databricks

**Projet :** Pipeline de génération de données financières synthétiques  
**Objectif :** 10M de transactions financières (~2GB) pour analyse Databricks  
**Date de Rédaction :** 05 Juin 2025  
**Auteurs :** Sanda ANDRIA & Celia HADJI  
**Environnement :** GCP (Europe-West1), Python 3.12, Ubuntu WSL2

---

## 📋 **Introduction et Contexte**

Bienvenue dans ce rapport technique ! Nous sommes Sanda ANDRIA et Celia HADJI, et nous allons vous présenter le travail que nous avons accompli lors de notre première journée sur le projet de génération de données synthétiques. L'objectif principal était de mettre en place un pipeline robuste pour créer un volume conséquent de données financières (10 millions de lignes) destinées à des analyses ultérieures sur Databricks.

Initialement, nous avions envisagé une approche avec Apache Beam et Dataflow. Cependant, au fil de nos expérimentations et des défis rencontrés, nous avons pivoté vers une solution locale optimisée en multi-threading. Ce changement s'est avéré crucial, nous permettant de réduire drastiquement les temps de génération (de plus de 30 minutes à seulement 3-5 minutes) tout en simplifiant la gestion des ressources cloud.

**Ce que nous avons accompli aujourd'hui :**
- ✅ **Performance Améliorée** : Génération de 10M lignes en 3-5 minutes.
- ✅ **Fiabilité Accrue** : Taux de réussite de 100% pour la génération.
- ✅ **Optimisation des Coûts** : Suppression des coûts liés aux VMs Dataflow temporaires.
- ✅ **Richesse des Données** : Création de 19 types d'opérations financières réalistes.

---

## 🗓️ **Déroulement de la Première Journée de Travail (05/06/2025)**

Notre journée a été rythmée par plusieurs phases clés, allant de la configuration initiale de l'infrastructure à l'optimisation finale du processus de génération.

### **Matin : Configuration & Premiers Tests avec Apache Beam/Dataflow**

#### **1. Mise en Place de l'Infrastructure GCP**

Nous avons commencé par définir l'architecture cible de notre Data Lake sur Google Cloud Storage :

**Structure du Data Lake :**
```
gs://supdevinci_bucket/sanda_celia/
├── tmp/           # Fichiers temporaires pour Dataflow
├── raw/           # Données CSV brutes (notre output)
├── staging/       # Espace pour données optimisées (Parquet, via Databricks)
└── delta/         # Espace pour tables Delta finales (via Databricks)
```

Nous avons utilisé les technologies suivantes :
- **Compute :** Google Cloud Dataflow (via Apache Beam)
- **Storage :** Google Cloud Storage
- **Analytics :** Databricks (pour la suite du projet)
- **IAM :** Un Service Account dédié pour sécuriser les accès
- **Région :** `europe-west1` pour être en accord avec les normes RGPD.

La création du Service Account s'est faite via gcloud :
```bash
gcloud iam service-accounts create dataflow-generator \
    --display-name="Dataflow Data Generator" \
    --description="Service account pour la génération de données"
```
Et nous lui avons attribué les rôles nécessaires : `roles/dataflow.admin`, `roles/dataflow.worker`, `roles/storage.admin`, et `roles/iam.serviceAccountUser`.

Le bucket GCS a également été configuré :
```bash
gsutil mb -p biforaplatform -l europe-west1 gs://supdevinci_bucket
```
Avec des politiques de cycle de vie pour gérer les fichiers temporaires et archiver les données.

#### **2. Développement du Pipeline Apache Beam Initial**

Ensuite, nous avons structuré notre code pour le pipeline Apache Beam :
```
src/  # Ancien emplacement, maintenant simplifié
├── config.py
├── generate_to_gcs.py  # Notre script Beam principal
└── utils/
    └── data_generator.py
```

Le pipeline Beam était conçu pour :
1. Générer une série d'indices (`Create(range(1, 10_000_000))`).
2. Utiliser une transformation `DoFn` pour générer chaque ligne CSV avec sa logique métier.
3. Écrire les données sur GCS avec `WriteToText`, en shardant automatiquement les fichiers.

Nous avons implémenté la logique pour 19 types d'opérations financières (cotisations, remboursements, provisions, etc.) avec des montants générés de manière réaliste. Par exemple :
```python
def get_montant_by_operation_type(type_op: str) -> float:
    if type_op in ["cotisation", "prime_exceptionnelle"]:
        return round(random.uniform(50.0, 2500.0), 2)
    # ... et ainsi de suite pour les 19 types.
```

La configuration du pipeline incluait des paramètres comme le nombre de shards, la taille cible et le type de machine pour les workers.

### **Après-midi : Défis, Debugging et Pivot Stratégique**

#### **3. Challenges Rencontrés avec Dataflow**

Rapidement, nous avons fait face à plusieurs obstacles :

*   **Problèmes IAM Critiques :**
    L'erreur `constraints/dataflow.enforceComputeDefaultServiceAccountCheck` nous a bloqués. Une politique organisationnelle nous empêchait d'utiliser le service account par défaut comme Dataflow le souhaitait. Les tentatives de modification de cette politique via `gcloud org-policies` ont échoué faute de permissions suffisantes au niveau de l'organisation (notre projet n'ayant pas d'organisation parente directe).
    *   **Résolution (partielle) :** Nous avons dû configurer manuellement les rôles via la console GCP, en ajoutant `roles/iam.serviceAccountUser` à notre compte utilisateur et `roles/dataflow.worker` au service account, puis en spécifiant explicitement ce dernier dans le code.

*   **Épuisement des Ressources Compute :**
    L'erreur `ZONE_RESOURCE_POOL_EXHAUSTED` dans `europe-west1-d` était fréquente. Après investigation, nous avons constaté que trois grosses instances Databricks (`n2-highmem-4`) monopolisaient les ressources de cette zone.
    *   **Solutions testées :**
        1.  Arrêter les instances Databricks pour libérer les ressources :
            ```bash
            gcloud compute instances stop databricks-* --zone=europe-west1-d --discard-local-ssd=false
            ```
        2.  Modifier la `worker_zone` du pipeline Dataflow pour `europe-west1-c`.
        3.  Utiliser des `worker_machine_type` plus petits comme `n1-standard-1`.

*   **Difficultés avec les Dépendances et Imports :**
    Des `ModuleNotFoundError` (par exemple, pour `generate_to_gcs`) sont apparus. Ces erreurs étaient dues à des incompatibilités entre les imports relatifs de notre structure de projet locale et la manière dont Dataflow exécute le code sur ses workers, ainsi qu'à des conflits de versions de dépendances.
    *   **Solutions appliquées (pour Dataflow) :** Nous avons dû unifier le code en un seul fichier, éliminer les imports relatifs et synchroniser les versions des dépendances (ex: `faker==19.13.0`, `apache-beam[gcp]==2.65.0`).

#### **4. Vers une Solution Optimisée : Génération Locale Multi-Thread**

Face à ces défis persistants avec Dataflow (temps de démarrage longs, gestion complexe des dépendances et des ressources pour notre cas d'usage somme toute simple de génération de CSV), nous avons décidé d'explorer une alternative.

*   **Analyse Critique de Dataflow pour ce Cas :**
    L'overhead de Dataflow (5-10 minutes juste pour le setup des VMs et des dépendances) et la complexité du scaling automatique n'étaient pas justifiés. Le rapport coût/performance n'était pas optimal. Un benchmark rapide nous a montré que Dataflow prenait plus de 30 minutes pour la tâche (quand il ne rencontrait pas d'erreur).

*   **Conception de la Solution Alternative :**
    Nous avons opté pour un script Python local utilisant le multi-threading (`ThreadPoolExecutor`) pour générer les données en parallèle.
    ```python
    # Exemple de configuration pour 12 CPUs
    NUM_THREADS = 10          # Utilisation à ~83% des CPUs
    CHUNK_SIZE = 250_000      # Bon équilibre mémoire/performance
    NUM_FILES = 5             # Pour paralléliser l'upload avec gsutil
    ```
    Le pipeline simplifié est devenu :
    1.  Génération parallèle des lignes par plusieurs threads.
    2.  Écriture directe des fichiers CSV finaux (sans consolidation intermédiaire complexe).
    3.  Upload parallèle vers GCS en utilisant `gsutil -m cp`.

*   **Implémentation et Debugging Final :**
    La fonction de génération a été adaptée :
    ```python
    def generate_file_direct(file_index: int, rows_per_file: int) -> str:
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile, quoting=csv.QUOTE_MINIMAL)
            # ... logique de génération ...
    ```
    L'upload s'est simplifié à :
    ```python
    cmd = ["gsutil", "-m", "cp"] + local_files + [gcs_destination]
    subprocess.run(cmd, check=True)
    ```
    Un dernier souci d'encodage UTF-8 (erreur `byte 0xc3`) a été résolu en :
    1.  Simplifiant les données générées (ex: "santé" → "sante").
    2.  Forçant l'encodage `utf-8` partout.
    3.  Convertissant explicitement les montants en `str()`.
    4.  Générant directement les fichiers finaux, éliminant une étape de consolidation source d'erreurs.

---

## 📊 **Résultats de la Journée et Comparaison des Performances**

Cette réorientation stratégique a porté ses fruits de manière spectaculaire.

### **Métriques de Performance Clés**

| **Méthode**              | **Temps Total** | **Fiabilité**             | **Coût GCP**      | **Complexité** |
| ------------------------ | --------------- | ------------------------- | ----------------- | -------------- |
| **Apache Beam/Dataflow** | 30+ min         | ~60% (erreurs fréquentes) | €5-10/run         | Élevée         |
| **Multi-thread local**   | **3-5 min**     | **100%**                  | €0 (storage seul) | **Faible**     |

Cela représente une **amélioration de performance de 600 à 1000%** !

### **Qualité et Scalabilité des Données**

Les données générées sont conformes à nos attentes :
```csv
id_mouvement,date_op,produit,type_op,montant,agence_id,pays
M0000001,2025-06-06,auto,provision_sinistre,8944.6,AG_007,FR
M0000002,2025-06-15,sante,cotisation,1250.75,AG_012,ES
```
Avec une distribution réaliste des 19 types d'opérations.

La solution locale est également scalable :
-   **10M lignes :** 3-5 minutes.
-   **50M lignes :** Estimé à 15-20 minutes.
-   **100M lignes :** Probablement réalisable en moins d'une heure sur une machine de développement correcte.
    Les limites principales sont le disque local, la bande passante pour l'upload, et les ressources CPU/RAM de la machine exécutant le script.

---

## 🔧 **Automatisation et Organisation du Projet**

Pour pérenniser notre travail, nous avons mis en place une infrastructure as code avec Terraform et organisé notre projet.

### **Infrastructure Terraform**

Un ensemble de fichiers Terraform (`infrastructure/terraform/main.tf`) de plus de 200 lignes permet de déployer automatiquement :
-   Le service account `dataflow-generator` avec les bonnes permissions.
-   Les rôles IAM nécessaires.
-   L'activation des APIs GCP (Dataflow, Storage, etc.).
-   La structure de dossiers sur GCS.
-   La gestion des politiques d'organisation problématiques.
-   Des règles de cycle de vie pour optimiser les coûts de stockage.

Un script `scripts/deploy.sh` orchestre ce déploiement.

### **Documentation et Maintenance**
Nous avons structuré le projet avec des dossiers clairs (`docs/`, `src/`, `scripts/`, `infrastructure/`) et créé plusieurs documents de support :
-   `README.md` : Guide d'utilisation principal.
-   `docs/GCP_GCLOUD_CHEATSHEET.md` : Aide-mémoire des commandes gcloud.
-   Ce `docs/RAPPORT_TECHNIQUE_GENERATION_DONNEES.md`.

---

## 🚀 **Recommandations et Prochaines Étapes (Pour la Suite)**

Forts de cette première journée intense, voici quelques recommandations pour la suite du projet et pour des contextes similaires.

### **Recommandations Techniques Immédiates**

1.  **Évaluer la Complexité vs. Solution :** Toujours se demander si un outil puissant comme Dataflow est réellement nécessaire pour la tâche à accomplir.
2.  **Simplicité d'Abord :** Privilégier les solutions simples et locales lorsque c'est possible, surtout pour la génération de données ou des ETLs basiques.
3.  **Tests Locaux Approfondis :** Tester autant que possible localement avant de déployer sur le cloud.
4.  **Vigilance IAM :** Les politiques IAM, surtout dans des environnements avec des contraintes organisationnelles, peuvent être un frein majeur.

Pour la génération de données, nous suggérons les seuils suivants comme point de départ :
-   **< 50M lignes :** Notre solution multi-thread locale est idéale.
-   **50M-500M lignes :** Envisager Cloud Run ou des instances Compute Engine dédiées.
-   **> 500M lignes :** Dataflow ou Spark deviennent alors plus pertinents.

### **Évolutions Futures pour Ce Projet**
-   Support de formats de sortie multiples (Parquet, Avro) directement depuis le générateur local.
-   Peut-être une petite interface web pour configurer les paramètres de génération.
-   Intégration plus poussée avec Databricks (déclenchement automatique post-upload, conversion Parquet/Delta).

### **Principaux Enseignements de la Journée**
1.  **La simplicité peut surpasser la complexité :** Notre script local est bien plus performant et fiable que Dataflow pour ce cas.
2.  **Les contraintes IAM organisationnelles sont un vrai défi.**
3.  **La gestion des imports Python par Dataflow est délicate.**
4.  **La disponibilité des ressources dans les zones GCP est un facteur à ne pas négliger.**

---

## 📈 **Conclusion de Notre Première Journée**

Cette première journée de travail a été riche en apprentissages. Nous avons réussi à mettre en place un système de génération de données synthétiques non seulement fonctionnel mais aussi extrêmement performant et fiable, en adaptant notre approche face aux défis rencontrés.

**Nos succès du jour :**
-   ✅ Objectif de 10M lignes atteint.
-   ✅ Performance multipliée par 10 par rapport à notre idée initiale.
-   ✅ Fiabilité de 100% pour la génération.
-   ✅ Infrastructure reproductible grâce à Terraform.

L'impact est significatif : un temps de génération réduit de plus de 30 minutes à moins de 5 minutes, des coûts cloud maîtrisés, et une meilleure fiabilité opérationnelle. Cette base solide nous permettra d'aborder sereinement les prochaines étapes du projet, notamment l'intégration avec Databricks.

---

**Rédigé par :** Sanda ANDRIA & Celia HADJI  
**Date :** 05 Juin 2025 