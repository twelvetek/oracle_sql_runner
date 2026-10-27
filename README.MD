# SQL Runner Oracle

## Objectif

Ce programme automatise l’exécution de scripts SQL Oracle. Il lit une configuration au format JSON, lance les scripts déclarés avec SQL*Plus, puis consigne le déroulement dans un journal. Les requêtes `SELECT` peuvent également enregistrer leur résultat dans un fichier, comme un export CSV.

Les scripts SQL présents dans le projet sont des exemples. Ils supposent l’existence de tables et de colonnes qui devront être adaptées au schéma de votre base Oracle.

## Organisation du projet

```text
SQL_runner/
├── oracle_sql_runner.py          # Orchestrateur Python
├── oracle_sql_runner.json        # Exemple de configuration
├── README.MD                     # Présentation et fonctionnement
├── MANUEL UTILISATEUR.MD         # Prérequis, installation, utilisation et dépannage
└── sql/
    ├── export_clients.sql        # SELECT et export des clients
    ├── insert_historique.sql     # INSERT dans l’historique
    ├── update_clients.sql        # UPDATE des clients
    └── delete_tmp.sql            # DELETE des données temporaires
```

### Rôle des composants

- **`oracle_sql_runner.py`** charge la configuration, initialise le journal, parcourt les traitements et choisit le traitement correspondant à chaque type SQL. Il délègue l’exécution SQL à SQL*Plus.
- **`oracle_sql_runner.json`** définit le journal, le comportement en cas d’erreur et la liste ordonnée des scripts à lancer, avec leurs connexions et éventuels fichiers de sortie.
- **`sql/*.sql`** contient les instructions Oracle elles-mêmes. Cette séparation permet de modifier les requêtes sans changer l’orchestrateur Python.

## Fonctionnement

Lorsqu’il est lancé, le programme :

1. Lit la variable d’environnement `REP_UTIL`.
2. Charge la configuration dans `<REP_UTIL>\data\oracle_sql_runner.json`. Le nom du fichier est construit à partir de celui du programme Python.
3. Configure le journal au chemin défini par `log.file`.
4. Parcourt les objets de `queries` dans l’ordre où ils apparaissent.
5. Pour chaque objet, récupère la connexion nommée par `connection_env` dans les variables d’environnement et lance le fichier SQL indiqué par `file` avec `sqlplus -S`.
6. Pour un `SELECT`, écrit la sortie standard SQL*Plus dans `output_file`. Pour un `INSERT`, `UPDATE` ou `DELETE`, consigne la fin du traitement et la sortie éventuelle dans le journal.
7. En cas d’erreur, inscrit les détails dans le journal. Si `general.stop_on_error` vaut `true`, l’erreur interrompt le traitement ; sinon, le programme poursuit avec la requête suivante.

Chaque script est lancé dans un processus SQL*Plus distinct. Les `COMMIT` des scripts d’écriture valident les changements dans Oracle ; le programme ne regroupe pas toute la séquence dans une transaction unique.

## Traitements configurés en exemple

La configuration fournie contient les opérations suivantes :

| Ordre | Nom | Type | Script | Connexion | Résultat |
|---:|---|---|---|---|---|
| 1 | Export clients | `SELECT` | `sql/export_clients.sql` | `CLIENTS_CONNECTION` | `data/clients.csv` |
| 2 | Ajout historiques | `INSERT` | `sql/insert_historique.sql` | `ADMIN_CONNECTION` | Journal |
| 3 | Mise à jour clients | `UPDATE` | `sql/update_clients.sql` | `CLIENTS_CONNECTION` | Journal |
| 4 | Purge temporaire | `DELETE` | `sql/delete_tmp.sql` | `ADMIN_CONNECTION` | Journal |

Le contenu des scripts d’exemple :

- **Export clients** sélectionne `ID_CLIENT`, `NOM` et `EMAIL` dans `CLIENTS`, les trie par identifiant et configure SQL*Plus pour une sortie CSV.
- **Ajout historiques** ajoute à `HISTORIQUE_CLIENTS` une entrée de type `IMPORT` pour chaque client dont `ACTIF = 'O'`.
- **Mise à jour clients** attribue `SYSDATE` à `DATE_MODIFICATION` pour les clients actifs dont cette colonne est `NULL`.
- **Purge temporaire** supprime de `TMP_IMPORT_CLIENTS` les lignes dont `DATE_CREATION` remonte à plus de 30 jours.

Les trois derniers scripts exécutent un `COMMIT`. La purge est définitive après validation : contrôlez les filtres et testez ces exemples sur une base de développement avant tout usage réel.

## Configuration et lancement

Le script ne charge pas directement le fichier JSON à la racine du dépôt. Pour un lancement depuis PowerShell, préparez l’emplacement attendu et lancez depuis la racine du projet :

```powershell
$project = "C:\chemin\vers\SQL_runner"
$env:REP_UTIL = $project

New-Item -ItemType Directory -Force -Path "$project\data" | Out-Null
Copy-Item "$project\oracle_sql_runner.json" "$project\data\oracle_sql_runner.json"

# Définir les connexions dans ce terminal à l'aide de votre mécanisme sécurisé.
$env:CLIENTS_CONNECTION = "<connexion Oracle pour les clients>"
$env:ADMIN_CONNECTION = "<connexion Oracle pour l'administration>"

Set-Location $project
python .\oracle_sql_runner.py
```

Python 3.7 ou une version ultérieure est requis par le code actuel. SQL*Plus doit aussi être installé, accessible par la commande `sqlplus` et compatible avec les commandes des scripts (notamment `SET MARKUP CSV` dans l’export).

Avant le lancement, vérifiez le paramètre `log.file` dans la configuration copiée : sa valeur d’exemple, `/var/log/generic-sql.log`, est un chemin Linux. Sous Windows, remplacez-la par un chemin approprié et accessible en écriture. Les variables de connexion illustrées ci-dessus sont des exemples de noms ; ne placez pas de mots de passe réels dans le JSON ou dans un fichier versionné.

Les chemins SQL (`file`) et de sortie (`output_file`) sont résolus relativement au répertoire courant. L’exemple ci-dessus lance le programme depuis la racine du projet.

## Documentation détaillée

Consultez le [manuel utilisateur](./MANUEL%20UTILISATEUR.MD) pour les détails des paramètres, la préparation des connexions, les journaux, les précautions d’utilisation et le dépannage.
