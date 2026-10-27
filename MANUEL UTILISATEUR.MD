# Manuel utilisateur — SQL Runner Oracle

## 1. Présentation

SQL Runner Oracle exécute, dans l’ordre, des scripts SQL Oracle déclarés dans un fichier de configuration JSON. Chaque script est lancé par `sqlplus`. Le programme sait traiter quatre types d’opérations :

- `SELECT` : exécuter une requête et enregistrer sa sortie dans un fichier ;
- `INSERT` : insérer des données ;
- `UPDATE` : modifier des données ;
- `DELETE` : supprimer des données.

Le projet comprend le programme `oracle_sql_runner.py`, sa configuration `oracle_sql_runner.json` et quatre scripts dans `sql/`.

Le fichier de configuration au format JSON `oracle_sql_runner.json` définit les traitements et leurs paramètres.

Les scripts SQL fournis sont des exemples : les tables et colonnes utilisées doivent exister dans votre base Oracle, ou être adaptées à votre schéma avant exécution.

## 2. Prérequis

Avant le lancement, vérifiez que :

1. Python est installé et accessible avec la commande `python`.
2. Oracle SQL*Plus est installé et la commande `sqlplus` est accessible depuis le terminal.
3. Le poste peut joindre la base Oracle.
4. Les comptes définis dans les variables d’environnement ont les droits nécessaires.
5. La configuration et les scripts sont placés aux chemins attendus.

Le script utilise `SET MARKUP CSV`, une fonction SQL*Plus disponible dans les versions récentes d’Oracle Client. Si cette commande est inconnue, vérifiez la version de SQL*Plus utilisée.

## 3. Fichiers et chemins

Structure du projet :

```text
SQL_runner/
├── oracle_sql_runner.py
├── oracle_sql_runner.json
├── MANUEL UTILISATEUR.MD
└── sql/
    ├── export_clients.sql
    ├── insert_historique.sql
    ├── update_clients.sql
    └── delete_tmp.sql
```

Le programme détermine le nom de configuration à partir du nom du script Python. Comme le script s’appelle `oracle_sql_runner.py`, il cherche le fichier :

```text
<REP_UTIL>\data\oracle_sql_runner.json
```

La variable d’environnement `REP_UTIL` doit donc pointer vers un répertoire contenant un sous-répertoire `data`. Par exemple, avec `REP_UTIL` défini sur le répertoire du projet, placez la configuration à :

```text
<répertoire du projet>\data\oracle_sql_runner.json
```

Les chemins des scripts SQL du JSON (`sql/export_clients.sql`, etc.) sont relatifs au répertoire courant du terminal. Lancez donc le programme depuis la racine du projet, ou adaptez ces chemins si vous le lancez depuis un autre répertoire.

Le paramètre `log.file` indique le chemin du journal. Dans la configuration fournie, il vaut `/var/log/generic-sql.log`, chemin de style Linux qui n’est généralement pas adapté sous Windows. Remplacez-le par un chemin Windows accessible en écriture, par exemple :

```json
"log": {
  "file": "C:\\Users\\VotreNom\\Documents\\SQL_runner\\traces\\oracle_sql_runner.log"
}
```

Le programme crée le dossier parent du journal s’il n’existe pas.

## 4. Configuration JSON

Le fichier fourni déclare les quatre traitements suivants :

| Nom | Type | Script SQL | Connexion | Fichier de sortie |
|---|---|---|---|---|
| Export clients | `SELECT` | `sql/export_clients.sql` | `CLIENTS_CONNECTION` | `data/clients.csv` |
| Ajout historiques | `INSERT` | `sql/insert_historique.sql` | `ADMIN_CONNECTION` | — |
| Mise à jour clients | `UPDATE` | `sql/update_clients.sql` | `CLIENTS_CONNECTION` | — |
| Purge temporaire | `DELETE` | `sql/delete_tmp.sql` | `ADMIN_CONNECTION` | — |

Les principales propriétés sont :

- `log.file` : destination du journal d’exécution ;
- `general.stop_on_error` : si `true`, le programme s’arrête à la première erreur ; si `false`, il journalise l’erreur et poursuit les autres traitements ;
- `queries` : liste ordonnée des traitements ;
- `name` : nom lisible du traitement, affiché dans les journaux ;
- `type` : type d’opération pris en charge (`SELECT`, `INSERT`, `UPDATE` ou `DELETE`) ;
- `file` : chemin du script SQL à exécuter ;
- `connection_env` : nom de la variable d’environnement qui contient la chaîne de connexion SQL*Plus ;
- `output_file` : fichier de sortie obligatoire pour une opération `SELECT`.

Pour ajouter un traitement, ajoutez un objet à `queries` avec ces propriétés. Utilisez un chemin SQL relatif à la racine du projet si le programme est lancé depuis celle-ci. Une requête de type `SELECT` doit également fournir `output_file`.

## 5. Préparer les connexions

Chaque traitement utilise la variable désignée par `connection_env`. La configuration fournie nécessite donc les variables `CLIENTS_CONNECTION` et `ADMIN_CONNECTION`.

Exemple PowerShell (remplacez les valeurs par celles de votre environnement) :

```powershell
$env:CLIENTS_CONNECTION = "utilisateur_clients/mot_de_passe@//serveur:1521/service"
$env:ADMIN_CONNECTION = "utilisateur_admin/mot_de_passe@//serveur:1521/service"
```

Les exemples ci-dessus illustrent le format habituel SQL*Plus `utilisateur/mot_de_passe@//hôte:port/service`. Ne stockez pas de vrais mots de passe dans le fichier JSON, dans le code ou dans un fichier versionné. Pour un usage réel, privilégiez le mécanisme de coffre-fort ou d’authentification sécurisé recommandé par votre environnement Oracle, tel qu’Oracle Wallet.

Ces variables ne sont disponibles que dans le terminal où elles ont été définies. Une variable absente provoque une erreur explicite lors du traitement qui en a besoin.

## 6. Lancer le programme

Exemple de préparation et de lancement dans PowerShell, depuis la racine du projet. La copie initiale est ensuite le fichier à modifier pour les exécutions :

```powershell
$project = "C:\chemin\vers\SQL_runner"
$env:REP_UTIL = $project

New-Item -ItemType Directory -Force -Path "$project\data" | Out-Null
Copy-Item "$project\oracle_sql_runner.json" "$project\data\oracle_sql_runner.json"

# Définir les connexions dans ce même terminal.
$env:CLIENTS_CONNECTION = "utilisateur_clients/mot_de_passe@//serveur:1521/service"
$env:ADMIN_CONNECTION = "utilisateur_admin/mot_de_passe@//serveur:1521/service"

Set-Location $project
python .\oracle_sql_runner.py
```

Avec `stop_on_error: true`, le code de sortie est `0` si tous les traitements réussissent et `1` si une erreur remonte au programme principal. En cas d’erreur, un message est écrit sur la sortie d’erreur et les détails sont enregistrés dans le journal, lorsqu’il a pu être initialisé. Avec `stop_on_error: false`, le programme continue après une erreur de requête ; il peut alors terminer avec le code `0` même si une erreur a été inscrite dans le journal. Consultez donc toujours le journal lorsque ce mode est activé.

Le programme lance chaque script par un appel SQL*Plus distinct. L’ordre d’exécution est l’ordre des objets dans `queries` : export, insertion, mise à jour, puis purge.

## 7. Détail des scripts SQL fournis

### 7.1 Export des clients — `sql/export_clients.sql`

Ce script sélectionne `ID_CLIENT`, `NOM` et `EMAIL` dans la table `CLIENTS`, puis trie les résultats par identifiant. Les commandes SQL*Plus configurent la sortie en CSV.

La sortie standard de SQL*Plus est écrite dans le fichier défini par `output_file`, soit `data/clients.csv` dans la configuration. Le programme crée le dossier parent s’il n’existe pas et remplace le fichier à chaque exécution.

Exemple de contenu attendu, selon les données de la base :

```csv
ID_CLIENT,NOM,EMAIL
101,Dupont,dupont@example.com
102,Martin,martin@example.com
```

L’exemple suppose que `CLIENTS` contient les colonnes indiquées.

### 7.2 Ajout à l’historique — `sql/insert_historique.sql`

Ce script insère une ligne dans `HISTORIQUE_CLIENTS` pour chaque ligne de `CLIENTS` dont `ACTIF` vaut `'O'`. Il copie `ID_CLIENT`, inscrit `'IMPORT'` comme type d’action, utilise `SYSDATE` comme date et ajoute le commentaire d’exemple.

Le script exécute `COMMIT` après l’insertion. Chaque exécution peut donc ajouter de nouvelles lignes pour les mêmes clients ; aucune vérification anti-doublon n’est incluse dans cet exemple.

### 7.3 Mise à jour des clients — `sql/update_clients.sql`

Ce script met `DATE_MODIFICATION` à `SYSDATE` pour les clients actifs (`ACTIF = 'O'`) dont la date de modification est actuellement `NULL`. Les autres lignes ne sont pas modifiées.

Le script valide les modifications avec `COMMIT`.

### 7.4 Purge temporaire — `sql/delete_tmp.sql`

Ce script supprime de `TMP_IMPORT_CLIENTS` les lignes dont `DATE_CREATION` est antérieure à la date courante moins 30 jours. Les lignes datées des 30 derniers jours ne sont pas concernées.

Le script exécute `COMMIT`. Vérifiez soigneusement la table et le critère de date avant d’utiliser cet exemple sur des données réelles : la suppression est définitive une fois validée.

### Gestion des erreurs SQL

Les quatre scripts utilisent :

```sql
WHENEVER OSERROR EXIT FAILURE
WHENEVER SQLERROR EXIT SQL.SQLCODE
```

Ces directives demandent à SQL*Plus de quitter avec un code d’erreur lorsqu’une erreur système ou SQL survient. Le programme intercepte les erreurs remontées, les journalise et applique ensuite le comportement défini par `stop_on_error`.

## 8. Journaux et résultats

Le journal contient les heures de début et de fin de chaque traitement, les erreurs, ainsi que des messages propres aux opérations. Pour l’export, il indique également le chemin du CSV et le nombre d’octets écrits.

Le CSV est créé à l’emplacement de `output_file` relatif au répertoire courant, ici `data/clients.csv`. Les opérations `INSERT`, `UPDATE` et `DELETE` ne produisent pas de fichier de sortie configuré ; leur sortie SQL*Plus éventuelle est consignée dans le journal.

## 9. Dépannage

| Symptôme | Vérifications |
|---|---|
| `Variable d'environnement REP_UTIL absente` | Définir `REP_UTIL` dans le terminal de lancement. |
| Configuration introuvable | Vérifier la présence de `<REP_UTIL>\data\oracle_sql_runner.json` et le nom du fichier. |
| `sqlplus` introuvable | Installer Oracle SQL*Plus ou ajouter son répertoire au `PATH`, puis vérifier avec `sqlplus -v`. |
| Variable `CLIENTS_CONNECTION` ou `ADMIN_CONNECTION` absente | Définir la variable correspondante dans le terminal courant. |
| Fichier SQL introuvable | Lancer depuis la racine du projet ou corriger les chemins `file` dans le JSON. |
| Échec de connexion | Vérifier le format de la chaîne de connexion, le réseau, le service Oracle et les droits du compte. |
| Erreur de table ou de colonne | Adapter les scripts aux tables et colonnes réellement présentes dans la base. |
| Impossible d’écrire le journal | Choisir dans `log.file` un chemin existant ou accessible en écriture. |
| CSV vide ou incorrect | Vérifier la requête, les données, la version de SQL*Plus et sa prise en charge de `SET MARKUP CSV`. |

## 10. Précautions d’utilisation

- Testez les scripts sur un environnement de développement avant toute exécution en production.
- Confirmez le schéma, les filtres et le nombre de lignes visées, en particulier pour `UPDATE` et `DELETE`.
- Les scripts d’écriture contiennent un `COMMIT` : les changements sont validés par Oracle à la fin de chaque script.
- Le traitement n’est pas une transaction globale : si un script échoue après que des scripts précédents ont terminé, leurs validations déjà effectuées ne sont pas annulées.
- Protégez les chaînes de connexion et le journal, qui peut contenir des informations opérationnelles.
