import os
import json
import glob
import csv

from functools import wraps
from flask import Flask, jsonify, request
import pandas as pd

from dotenv import load_dotenv
import os

load_dotenv(dotenv_path=".env")

app = Flask(__name__)

# Token de autenticación predefinido (puedes configurarlo como gustes)
AUTH_TOKEN = os.getenv("AUTH_TOKEN")
# Ruta al archivo Excel con la información de torneos/competiciones
TOURNAMENT_FILE = "tournaments.xlsx"
# Ruta al archivo CSV con la información de los partidos
MATCHES_CSV = "matches.csv"
# Directorio donde se encuentran los archivos JSON de los partidos
PARTIDOS_DIR = "partidos"

def token_required(f):
    """Decorador para requerir token en los endpoints."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", None)
        if not auth_header:
            return jsonify({"mensaje": "Falta el token de autenticación"}), 401

        try:
            token_type, token = auth_header.split()
            if token_type.lower() != "bearer":
                return jsonify({"mensaje": "Tipo de token inválido. Se espera 'Bearer'"}), 401
        except ValueError:
            return jsonify({"mensaje": "Formato de token inválido"}), 401

        if token != AUTH_TOKEN:
            return jsonify({"mensaje": "Token inválido"}), 401

        return f(*args, **kwargs)
    return decorated

@app.route("/competitions", methods=["GET"])
@token_required
def get_competitions():
    """
    Endpoint que devuelve las competiciones.
    
    Parámetros opcionales en la query:
      - tournamentId: (numérico) para filtrar por torneo.
      - seasonId: (numérico) para filtrar también por temporada.
    
    Si no se reciben parámetros, se devuelve la lista completa de competiciones.
    """
    try:
        df = pd.read_excel(TOURNAMENT_FILE)
    except Exception as e:
        return jsonify({"mensaje": "Error al leer el archivo tournament.xlsx", "error": str(e)}), 500

    # Recuperamos los parámetros de la query (si se pasan, serán strings)
    tournament_id = request.args.get("tournamentId")
    season_id = request.args.get("seasonId")

    # Si se recibe tournamentId, filtramos por él (convertido a entero)
    if tournament_id:
        try:
            tournament_id = int(tournament_id)
            df = df[df["tournamentId"] == tournament_id]
        except ValueError:
            return jsonify({"mensaje": "tournamentId debe ser un número entero"}), 400

    # Si se recibe seasonId, filtramos por él también
    if season_id:
        try:
            season_id = int(season_id)
            df = df[df["seasonId"] == season_id]
        except ValueError:
            return jsonify({"mensaje": "seasonId debe ser un número entero"}), 400

    # Construimos la información a retornar.
    # Suponiendo que queremos formar la cadena de competición en el formato:
    # "{regionName}-{tournamentName (sin espacios)}-{seasonName (con / reemplazado por -)}"
    competitions = []
    for _, row in df.iterrows():
        region_name = row.get("regionName", "").strip()
        tournament_name = row.get("tournamentName", "").strip()
        season_name = row.get("seasonName", "").strip()
        # Formateamos:
        tournament_name_formatted = tournament_name.replace(" ", "-")
        season_name_formatted = season_name.replace("/", "-")
        competition_str = f"{region_name}-{tournament_name_formatted}-{season_name_formatted}"

        # Armamos un diccionario con la info que queramos retornar:
        competition_data = {
            "tournamentId": row.get("tournamentId"),
            "seasonId": row.get("seasonId"),
            "stageId": row.get("stageId"),
            "stageName": row.get("stageName"),
            "regionId": row.get("regionId"),
            "tournamentName": tournament_name,
            "seasonName": season_name,
            "competition": competition_str,
        }
        competitions.append(competition_data)

    # Si no se encontró nada, se informa
    if competitions == []:
        return jsonify({"mensaje": "No se encontraron competiciones con los parámetros indicados"}), 404

    return jsonify(competitions)

def read_matches():
    """
    Función auxiliar que lee el archivo CSV de partidos y retorna una lista de diccionarios.
    """
    matches = []
    try:
        with open(MATCHES_CSV, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                matches.append(row)
    except FileNotFoundError:
        # Se podría lanzar un error o retornar lista vacía
        print(f"El archivo {MATCHES_CSV} no se encontró.")
    except Exception as e:
        print("Error al leer el CSV:", str(e))
    return matches

# 1. Endpoint que trae todos los partidos
@app.route("/matches", methods=["GET"])
@token_required
def get_all_matches():
    matches = read_matches()
    return jsonify(matches)

# 2. Endpoint que trae los partidos de una competición específica
@app.route("/matches/competition/<competition>", methods=["GET"])
@token_required
def get_matches_by_competition(competition):
    matches = read_matches()
    # Se hace una comparación en minúsculas para evitar problemas con mayúsculas/minúsculas
    filtered = [m for m in matches if m.get("competition", "").lower() == competition.lower()]
    if not filtered:
        return jsonify({"mensaje": f"No se encontraron partidos para la competición '{competition}'"}), 404
    return jsonify(filtered)

# 3. Endpoint que trae los partidos de una competición y una temporada específicas
@app.route("/matches/competition/<competition>/season/<season>", methods=["GET"])
@token_required
def get_matches_by_competition_and_season(competition, season):
    matches = read_matches()
    filtered = [
        m for m in matches 
        if m.get("competition", "").lower() == competition.lower() and m.get("season", "") == season
    ]
    if not filtered:
        return jsonify({"mensaje": f"No se encontraron partidos para la competición '{competition}' y la temporada '{season}'"}), 404
    return jsonify(filtered)

# 4. Endpoint que trae un partido en particular según su id
@app.route("/matches/id/<match_id>", methods=["GET"])
@token_required
def get_match_by_id(match_id):
    matches = read_matches()
    for match in matches:
        if match.get("match_id") == match_id:
            return jsonify(match)
    return jsonify({"mensaje": f"No se encontró el partido con id '{match_id}'"}), 404

@app.route("/match/<match_id>", methods=["GET"])
@token_required
def get_match_json(match_id):
    """
    Endpoint que recibe el match id y devuelve el contenido del archivo JSON
    que tenga ese id en su nombre.
    
    Se asume que los archivos siguen el formato:
      <fecha>_<home_team>_<away_team>_<match_id>.json
    """
    # Usamos glob para buscar archivos que terminen en _<match_id>.json
    pattern = os.path.join(PARTIDOS_DIR, f"*_{match_id}.json")
    files = glob.glob(pattern)

    if not files:
        return jsonify({"mensaje": f"No se encontró el partido con id '{match_id}'"}), 404

    # Suponemos que existe un solo archivo por match_id
    file_path = files[0]

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        return jsonify({"mensaje": "Error al leer el archivo JSON", "error": str(e)}), 500

@app.route("/match/base/<match_id>", methods=["GET"])
@token_required
def get_match_base(match_id):
    """
    Endpoint que devuelve la información base del partido con la siguiente estructura:
    
    {
      "matchId": 1734855,
      "timeStamp": "2024-01-08 15:14:11",
      "attendance": 11204,
      "venueName": "Cívitas Metropolitano",
      "referee_officialId": 4159,
      "referee_name": "Jorge Figueroa Vázquez",
      "weatherCode": "",
      "elapsed": "F",
      "startTime": "2024-01-02T17:00:00",
      "startDate": "2024-01-02T00:00:00",
      "score": "0 : 2",
      "htScore": "0 : 1",
      "ftScore": "0 : 2",
      "etScore": "",
      "statusCode": 6,
      "periodCode": 7,
      "maxMinute": 93,
      "minuteExpanded": 96,
      "maxPeriod": 2,
      "expandedMaxMinute": 96,
      "periodEndMinutes_1": 47,
      "periodEndMinutes_2": 93,
      "timeoutInSeconds": 0,
      "home_id": 819,
      "home_name": "Getafe",
      "home_countryName": "España",
      "home_managerName": "José Bordalás",
      "home_averageAge": 28.4,
      "away_id": 64,
      "away_name": "Rayo Vallecano",
      "away_countryName": "España",
      "away_managerName": "Francisco Rodríguez",
      "away_averageAge": 28.9
    }
    
    Se busca en el directorio PARTIDOS_DIR un archivo cuyo nombre termine en _<match_id>.json.
    """
    # Buscamos el archivo cuyo nombre contenga el match_id
    pattern = os.path.join(PARTIDOS_DIR, f"*_{match_id}.json")
    files = glob.glob(pattern)
    if not files:
        return jsonify({"mensaje": f"No se encontró el partido con id '{match_id}'"}), 404

    file_path = files[0]
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            match_data = json.load(f)
    except Exception as e:
        return jsonify({"mensaje": "Error al leer el archivo JSON", "error": str(e)}), 500

    # Extraemos la información general que se encuentra en el nodo matchCentreData
    match_centre = match_data.get("matchCentreData", {})
    referee = match_centre.get("referee", {})
    
    # Datos generales
    base_info = {
        "matchId": match_data.get("matchId"),
        "timeStamp": match_centre.get("timeStamp"),
        "attendance": match_centre.get("attendance"),
        "venueName": match_centre.get("venueName"),
        "referee_officialId": referee.get("officialId"),
        "referee_name": referee.get("name"),
        "weatherCode": match_centre.get("weatherCode"),
        "elapsed": match_centre.get("elapsed"),
        "startTime": match_centre.get("startTime"),
        "startDate": match_centre.get("startDate"),
        "score": match_centre.get("score"),
        "htScore": match_centre.get("htScore"),
        "ftScore": match_centre.get("ftScore"),
        "etScore": match_centre.get("etScore"),
        "statusCode": match_centre.get("statusCode"),
        "periodCode": match_centre.get("periodCode"),
        # Datos a nivel raíz
        "maxMinute": match_data.get("maxMinute"),
        "minuteExpanded": match_data.get("minuteExpanded"),
        "maxPeriod": match_data.get("maxPeriod"),
        "expandedMaxMinute": match_data.get("expandedMaxMinute"),
        "periodEndMinutes_1": match_data.get("periodEndMinutes", {}).get("1"),
        "periodEndMinutes_2": match_data.get("periodEndMinutes", {}).get("2"),
        "timeoutInSeconds": match_data.get("timeoutInSeconds")
    }

    # Datos del equipo local (home) (dentro de matchCentreData)
    home = match_centre.get("home", {})
    base_info["home_id"] = home.get("teamId")
    base_info["home_name"] = home.get("name")
    base_info["home_countryName"] = home.get("countryName")
    base_info["home_managerName"] = home.get("managerName")
    base_info["home_averageAge"] = home.get("averageAge")
    
    # Datos del equipo visitante (away) (a nivel raíz)
    away = match_data.get("away", {})
    base_info["away_id"] = away.get("teamId")
    base_info["away_name"] = away.get("name")
    base_info["away_countryName"] = away.get("countryName")
    base_info["away_managerName"] = away.get("managerName")
    base_info["away_averageAge"] = away.get("averageAge")
    
    return jsonify(base_info)

@app.route("/match/stats/<match_id>", methods=["GET"])
@token_required
def get_match_stats(match_id):
    """
    Endpoint que devuelve los stats del equipo local y visitante.
    
    Se busca en el directorio PARTIDOS_DIR un archivo que cumpla
    con el patrón: *_<match_id>.json
    y se extraen los stats de las claves:
      - matchCentreData > home > stats
      - matchCentreData > away > stats
    """
    # Buscamos el archivo cuyo nombre termine en _<match_id>.json
    pattern = os.path.join(PARTIDOS_DIR, f"*_{match_id}.json")
    files = glob.glob(pattern)
    if not files:
        return jsonify({"mensaje": f"No se encontró el partido con id '{match_id}'"}), 404

    file_path = files[0]
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            match_data = json.load(f)
    except Exception as e:
        return jsonify({"mensaje": "Error al leer el archivo JSON", "error": str(e)}), 500

    # Extraemos la información de los stats desde "matchCentreData"
    match_centre = match_data.get("matchCentreData", {})
    home_stats = match_centre.get("home", {}).get("stats", {})
    away_stats = match_centre.get("away", {}).get("stats", {})

    result = {
        "matchId": match_data.get("matchId"),
        "homeStats": home_stats,
        "awayStats": away_stats
    }
    return jsonify(result)

@app.route("/match/incidentEvents/<match_id>", methods=["GET"])
@token_required
def get_match_incident_events(match_id):
    """
    Endpoint que devuelve los incidentEvents filtrados por equipo:
      - homeIncidentEvents: eventos cuyo "teamId" coincide con el del equipo local.
      - awayIncidentEvents: eventos cuyo "teamId" coincide con el del equipo visitante.
      
    Se busca en el directorio PARTIDOS_DIR un archivo cuyo nombre termine en _<match_id>.json.
    """
    # Buscamos el archivo que tenga el match_id en su nombre
    pattern = os.path.join(PARTIDOS_DIR, f"*_{match_id}.json")
    files = glob.glob(pattern)
    if not files:
        return jsonify({"mensaje": f"No se encontró el partido con id '{match_id}'"}), 404

    file_path = files[0]
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            match_data = json.load(f)
    except Exception as e:
        return jsonify({"mensaje": "Error al leer el archivo JSON", "error": str(e)}), 500

    # Obtenemos la información de los equipos desde "matchCentreData"
    match_centre = match_data.get("matchCentreData", {})
    home = match_centre.get("home", {})
    away = match_centre.get("away", {})
    home_team_id = home.get("teamId")
    away_team_id = away.get("teamId")

    # Extraemos la lista de incidentEvents (si existe, de lo contrario usamos lista vacía)
    incident_events = match_data.get("incidentEvents", [])
    
    # Filtramos los eventos por equipo
    home_incident_events = [event for event in incident_events if event.get("teamId") == home_team_id]
    away_incident_events = [event for event in incident_events if event.get("teamId") == away_team_id]

    result = {
        "matchId": match_data.get("matchId"),
        "homeIncidentEvents": home_incident_events,
        "awayIncidentEvents": away_incident_events
    }
    return jsonify(result)

def process_team(formations, team_id):
    """
    Procesa la lista de formaciones de un equipo y devuelve un diccionario (por playerId)
    con la siguiente información para cada jugador:
      - teamId
      - playerId
      - jerseyNumber
      - matchStart (1 para titulares, 0 para suplentes)
      - formationSlot (valor de la primera formación; para suplentes se asigna None)
    """
    players = {}
    if not formations:
        return players
    # Procesar la primera formación: se asume inicialmente que son titulares.
    first_formation = formations[0]
    pids = first_formation.get("playerIds", [])
    jerseys = first_formation.get("jerseyNumbers", [])
    slots = first_formation.get("formationSlots", [])
    for i, pid in enumerate(pids):
        players[pid] = {
            "teamId": team_id,
            "playerId": pid,
            "jerseyNumber": jerseys[i] if i < len(jerseys) else None,
            "matchStart": 1,  # inicialmente titulares
            "formationSlot": slots[i] if i < len(slots) else None
        }
    # Corrección: si en la primera formación formationSlot es 0 o None, se marca como suplente.
    for pid, info in players.items():
        if not info.get("formationSlot"):
            info["matchStart"] = 0

    # Procesar las formaciones restantes: se consideran suplentes.
    for formation in formations[1:]:
        pids_sub = formation.get("playerIds", [])
        jerseys_sub = formation.get("jerseyNumbers", [])
        for i, pid in enumerate(pids_sub):
            if pid in players:
                continue  # Ya incluido como titular
            players[pid] = {
                "teamId": team_id,
                "playerId": pid,
                "jerseyNumber": jerseys_sub[i] if i < len(jerseys_sub) else None,
                "matchStart": 0,
                "formationSlot": None
            }
    return players

@app.route("/match/players/<match_id>", methods=["GET"])
@token_required
def get_match_players(match_id):
    """
    Endpoint que devuelve la lista de jugadores que participaron en el partido,
    junto con el matchId y el nombre de cada equipo.

    La respuesta tendrá la siguiente estructura:
    {
      "matchId": <matchId>,
      "homeTeamName": <nombre del equipo local>,
      "awayTeamName": <nombre del equipo visitante>,
      "homePlayers": [ {teamId, playerId, playerName, jerseyNumber, matchStart, formationSlot}, ... ],
      "awayPlayers": [ {teamId, playerId, playerName, jerseyNumber, matchStart, formationSlot}, ... ]
    }
    """
    # Buscar el archivo cuyo nombre contenga el match_id
    pattern = os.path.join(PARTIDOS_DIR, f"*_{match_id}.json")
    files = glob.glob(pattern)
    if not files:
        return jsonify({"mensaje": f"No se encontró el partido con id '{match_id}'"}), 404

    file_path = files[0]
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            match_data = json.load(f)
    except Exception as e:
        return jsonify({"mensaje": "Error al leer el archivo JSON", "error": str(e)}), 500

    # Extraer el diccionario de nombres de jugadores (playerIdNameDictionary)
    player_dict = match_data.get("matchCentreData", {}).get("playerIdNameDictionary", {})

    # Procesar equipo HOME (información dentro de matchCentreData["home"])
    home_data = match_data.get("matchCentreData", {}).get("home", {})
    home_team_id = home_data.get("teamId")
    home_formations = home_data.get("formations", [])
    home_players_dict = process_team(home_formations, home_team_id)
    home_players = list(home_players_dict.values())
    for rec in home_players:
        rec["playerName"] = player_dict.get(str(rec["playerId"]), "N/A")
    home_team_name = home_data.get("name", "N/A")

    # Procesar equipo AWAY
    # Intentar primero obtener away_data desde match_data["away"]
    away_data = match_data.get("away", {})
    if not away_data or not away_data.get("formations"):
        # Fallback: intentar desde matchCentreData["away"]
        away_data = match_data.get("matchCentreData", {}).get("away", {})
    away_team_id = away_data.get("teamId")
    away_formations = away_data.get("formations", [])
    away_players_dict = process_team(away_formations, away_team_id)
    away_players = list(away_players_dict.values())
    for rec in away_players:
        rec["playerName"] = player_dict.get(str(rec["playerId"]), "N/A")
    away_team_name = away_data.get("name", "N/A")

    result = {
        "matchId": match_data.get("matchId"),
        "homeTeamName": home_team_name,
        "awayTeamName": away_team_name,
        "homePlayers": home_players,
        "awayPlayers": away_players
    }
    return jsonify(result)

@app.route("/match/formations/<match_id>", methods=["GET"])
@token_required
def get_match_formations(match_id):
    """
    Endpoint que devuelve todas las formaciones del equipo local y del equipo visitante para un partido dado.
    
    Se busca el archivo en el directorio PARTIDOS_DIR cuyo nombre contenga el match_id
    (por ejemplo: "20240102_Getafe_Rayo Vallecano_1734855.json").

    La respuesta tendrá la siguiente estructura:
    
    {
      "matchId": 1734855,
      "homeFormations": [ ... ],
      "awayFormations": [ ... ]
    }
    """
    # Buscar el archivo que contenga el match_id en el nombre
    pattern = os.path.join(PARTIDOS_DIR, f"*_{match_id}.json")
    files = glob.glob(pattern)
    if not files:
        return jsonify({"mensaje": f"No se encontró el partido con id '{match_id}'"}), 404

    file_path = files[0]
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            match_data = json.load(f)
    except Exception as e:
        return jsonify({"mensaje": "Error al leer el archivo JSON", "error": str(e)}), 500

    # Obtener el matchId (a nivel raíz)
    match_id_val = match_data.get("matchId")
    
    # Formaciones del equipo local (home) se encuentran en matchCentreData["home"]["formations"]
    home_formations = match_data.get("matchCentreData", {}).get("home", {}).get("formations", [])
    
    # Formaciones del equipo visitante (away): se intenta obtener desde match_data["away"]["formations"]
    away_formations = match_data.get("away", {}).get("formations", [])
    if not away_formations:
        # Fallback: buscar en matchCentreData["away"]["formations"]
        away_formations = match_data.get("matchCentreData", {}).get("away", {}).get("formations", [])
    
    result = {
        "matchId": match_id_val,
        "homeFormations": home_formations,
        "awayFormations": away_formations
    }
    return jsonify(result)

@app.route("/match/events/<match_id>", methods=["GET"])
@token_required
def get_match_events(match_id):
    """
    Endpoint que devuelve todos los eventos del partido.
    
    Se asume que los eventos se encuentran en:
      match_data["matchCentreData"]["events"]
    
    La respuesta tendrá la siguiente estructura:
    
    {
      "matchId": <matchId>,
      "events": [ ... ]
    }
    """
    # Buscar el archivo cuyo nombre contenga el match_id
    pattern = os.path.join(PARTIDOS_DIR, f"*_{match_id}.json")
    files = glob.glob(pattern)
    if not files:
        return jsonify({"mensaje": f"No se encontró el partido con id '{match_id}'"}), 404

    file_path = files[0]
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            match_data = json.load(f)
    except Exception as e:
        return jsonify({"mensaje": "Error al leer el archivo JSON", "error": str(e)}), 500

    # Extraer los eventos desde matchCentreData["events"]
    events = match_data.get("matchCentreData", {}).get("events", [])
    
    result = {
        "matchId": match_data.get("matchId"),
        "events": events
    }
    return jsonify(result)

@app.route("/match/matchCentreEventTypeJson/<match_id>", methods=["GET"])
@token_required
def get_match_event_types(match_id):
    """
    Endpoint que devuelve la lista de matchCentreEventTypeJson para el partido.
    
    Se asume que la estructura del archivo JSON es similar a:
    
    {
       "matchId": 1734855,
       "matchCentreEventTypeJson": { ... },
       ...
    }
    
    La respuesta tendrá la siguiente estructura:
    {
      "matchId": 1734855,
      "matchCentreEventTypeJson": { ... }
    }
    """
    # Buscar el archivo cuyo nombre contenga el match_id
    pattern = os.path.join(PARTIDOS_DIR, f"*_{match_id}.json")
    files = glob.glob(pattern)
    if not files:
        return jsonify({"mensaje": f"No se encontró el partido con id '{match_id}'"}), 404

    file_path = files[0]
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            match_data = json.load(f)
    except Exception as e:
        return jsonify({"mensaje": "Error al leer el archivo JSON", "error": str(e)}), 500

    result = {
        "matchId": match_data.get("matchId"),
        "matchCentreEventTypeJson": match_data.get("matchCentreEventTypeJson", {})
    }
    return jsonify(result)

@app.route("/match/formationIdNameMappings/<match_id>", methods=["GET"])
@token_required
def get_formation_id_name_mappings(match_id):
    """
    Endpoint que devuelve la lista de formationIdNameMappings para el partido.
    
    Se asume que la estructura del archivo JSON es similar a:
    
    {
       "matchId": 1734855,
       "formationIdNameMappings": { ... },
       ...
    }
    
    La respuesta tendrá la siguiente estructura:
    {
      "matchId": 1734855,
      "formationIdNameMappings": { ... }
    }
    """
    # Buscar el archivo cuyo nombre contenga el match_id
    pattern = os.path.join(PARTIDOS_DIR, f"*_{match_id}.json")
    files = glob.glob(pattern)
    if not files:
        return jsonify({"mensaje": f"No se encontró el partido con id '{match_id}'"}), 404

    file_path = files[0]
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            match_data = json.load(f)
    except Exception as e:
        return jsonify({"mensaje": "Error al leer el archivo JSON", "error": str(e)}), 500

    result = {
        "matchId": match_data.get("matchId"),
        "formationIdNameMappings": match_data.get("formationIdNameMappings", {})
    }
    return jsonify(result)

@app.route("/opta/qualifiers", methods=["GET"])
@token_required
def get_opta_qualifiers():
    """
    Devuelve la lista de qualifiers extraída del archivo Opta_qualifiers.csv.
    Ejemplo de salida:
    [
      {"qualifierId": "1", "QUALIFIER NAME": "Long ball", ...},
      {"qualifierId": "2", "QUALIFIER NAME": "Cross", ...},
      {"qualifierId": "3", "QUALIFIER NAME": "Head pass", ...}
    ]
    """
    filename = "Opta_qualifiers.csv"
    qualifiers = []
    try:
        with open(filename, encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile, delimiter=";")
            for row in reader:
                qualifiers.append(row)
    except Exception as e:
        return jsonify({"mensaje": "Error al leer el archivo Opta_qualifiers.csv", "error": str(e)}), 500

    return jsonify(qualifiers)

@app.route("/opta/typeId", methods=["GET"])
@token_required
def get_opta_typeId():
    """
    Devuelve la lista de registros extraída del archivo Opta_typeId.csv.
    Ejemplo de salida:
    [
      {
        "typeId": "1",
        "EVENT NAME": "Pass",
        "DESCRIPTION": "The attempted delivery of the ball ...",
        "ASSOCIATED qualifierId VALUES": "1, 2, 3, ..."
      },
      {
        "typeId": "2",
        "EVENT NAME": "Offside Pass",
        "DESCRIPTION": "A pass attempt where the intended ...",
        "ASSOCIATED qualifierId VALUES": "1, 2, 3, ..."
      }
    ]
    """
    filename = "Opta_typeId.csv"
    type_ids = []
    try:
        with open(filename, encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile, delimiter=";")
            for row in reader:
                type_ids.append(row)
    except Exception as e:
        return jsonify({"mensaje": "Error al leer el archivo Opta_typeId.csv", "error": str(e)}), 500

    return jsonify(type_ids)

@app.route("/teams", methods=["GET"])
@token_required
def get_teams():
    """
    Devuelve la lista de equipos extraída del archivo teams.csv.
    Ejemplo de salida:
    [
      {
         "matchId": "1866220",
         "teamId": "361",
         "teamName": "Salzburg",
         "countryCode": "at",
         "countryName": "Austria",
         "imageUrl": "https://d2zywfiolv4f83.cloudfront.net/img/teams/361.png"
      },
      ...
    ]
    Nota: La primera columna del CSV puede estar vacía.
    """
    filename = "teams.csv"
    teams = []
    try:
        with open(filename, encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile, delimiter=";")
            for row in reader:
                teams.append(row)
    except Exception as e:
        return jsonify({"mensaje": "Error al leer el archivo teams.csv", "error": str(e)}), 500

    return jsonify(teams)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
