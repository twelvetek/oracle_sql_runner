#!/usr/bin/env python3

import json
import logging
import os
import subprocess
import sys

from pathlib import Path

# -----------------------------------------
# Récupération du fichier de configuration 
# -----------------------------------------
rep_util = os.getenv("REP_UTIL")
if rep_util is None:
    raise RuntimeError(
        "Variable d'environnement REP_UTIL absente"
    )

PROGRAM_NAME = Path(__file__).stem

CONFIG_FILE = (
    Path(rep_util)
    / "data"
    / f"{PROGRAM_NAME}.json"
)

LOG_FILE = (
    Path(rep_util)
    / "traces"
    / f"{PROGRAM_NAME}.log"
)


# -------------------------------
# Chargement de la configuration
# -------------------------------
def load_configuration():

    config_path = Path(CONFIG_FILE)

    if not config_path.exists():
        raise FileNotFoundError(
            f"Fichier de configuration introuvable : {CONFIG_FILE}"
        )

    with open(config_path, "r", encoding="utf-8") as file:
        return json.load(file)

#-------------------------------
# Initialisation du logger
#-------------------------------
def initialize_logger(config):

    logfile = config["log"]["file"]
    log_path = Path(logfile)
    log_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    logging.basicConfig(
        filename=logfile,
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )

    logging.info("========================================")
    logging.info("Démarrage du traitement")

# --------------------------------------------
# Exécution d'une requête SQL via sqlplus
# -------------------------------------------- 
def execute_sqlplus(sql_file, connection_env):

    connection = os.getenv(connection_env)
    if connection is None:
        raise RuntimeError(
            f"Variable d'environnement absente : {connection_env}"
        )

    sql_path = Path(sql_file)
    if not sql_path.exists():
        raise FileNotFoundError(
            f"Fichier SQL introuvable : {sql_file}"
        )

    result = subprocess.run(
        [
            "sqlplus",
            "-S",
            connection,
            f"@{sql_path}"
        ],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(
            result.stderr.strip()
        )

    return result.stdout.strip()

# --------------------------------------------
# Traitement d'une requête SQL de type SELECT
# --------------------------------------------
def process_select(query):

    output = execute_sqlplus(
        query["file"],
        query["connection_env"]
    )

    output_file = query.get("output_file")

    if not output_file:

        raise RuntimeError(
            f"output_file obligatoire pour {query['name']}"
        )

    output_path = Path(output_file)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        output_path,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(output)

    logging.info(
        "Export réalisé : %s",
        output_file
    )

    logging.info(
        "%d octets écrits",
        len(output)
    )

# --------------------------------------------
# Traitement d'une requête SQL de type INSERT
# --------------------------------------------
def process_insert(query):

    output = execute_sqlplus(
        query["file"],
        query["connection_env"]
    )

    logging.info(
        "INSERT terminé : %s",
        query["name"]
    )

    if output:
        logging.info(output)


def process_update(query):

    output = execute_sqlplus(
        query["file"],
        query["connection_env"]
    )

    logging.info(
        "UPDATE terminé : %s",
        query["name"]
    )

    if output:
        logging.info(output)

# --------------------------------------------
# Traitement d'une requête SQL de type DELETE
# --------------------------------------------
def process_delete(query):

    output = execute_sqlplus(
        query["file"],
        query["connection_env"]
    )

    logging.info(
        "DELETE terminé : %s",
        query["name"]
    )

    if output:
        logging.info(output)

# ----------------------------------------------------------
# Aiguillage du traitement d'une requête SQL selon son type
# ----------------------------------------------------------
def process_query(query):

    query_type = query["type"].upper()

    if query_type == "SELECT":
        process_select(query)
    elif query_type == "INSERT":
        process_insert(query)
    elif query_type == "UPDATE":
        process_update(query)
    elif query_type == "DELETE":
        process_delete(query)
    else:
        raise RuntimeError(
            f"Type inconnu : {query_type}"
        )


#----------------------------------------------------------
# PROGRAMME PRINCIPAL
#---------------------------------------------------------- 
def main():

    try:
        # Chargement de la configuration
        config = load_configuration()

        initialize_logger(config)

        stop_on_error = config["general"].get(
            "stop_on_error",
            True
        )

        # Traitement des requêtes SQL
        for query in config["queries"]:

            logging.info(
                "Début : %s",
                query["name"]
            )

            try:
                process_query(query)

                logging.info(
                    "Fin : %s",
                    query["name"]
                )
            except Exception:
                logging.exception(
                    "Erreur sur %s",
                    query["name"]
                )
                if stop_on_error:
                    raise

        logging.info(
            "Traitement terminé"
        )

    except Exception as error:

        print(
            f"ERREUR : {error}",
            file=sys.stderr
        )

        sys.exit(1)


if __name__ == "__main__":
    main()