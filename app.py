import os
import json
import glob 
import csv

from flasgger import Swagger # documentacion automatica

from functools import wraps
from flask import Flask, jsonify, request
import pandas as pd

from dotenv import load_dotenv
import os

load_dotenv(dotenv_path=".env")

app = Flask(__name__)

# Configuración de Swagger
app.config['SWAGGER_UI_CONFIG'] = {
    "title": "MPAD Cafecito API by Sports Data Campus",
    "docExpansion": "none",
    "defaultModelExpandDepth": 2,
    "defaultModelsExpandDepth": 1,
    "displayRequestDuration": True,
    "deepLinking": True,
    "persistAuthorization": True,
}

swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "MPAD Cafecito API by Sports Data Campus",
        "description": "<h3>Descargo de responsabilidad y Aviso Legal </h3><p>La información y los datos presentados a través de esta API han sido obtenidos de fuentes disponibles públicamente en Internet. Esta aplicación se ha desarrollado únicamente con fines educativos, en el marco de los programas de Maestría de Sports Data Campus (SDC) y no tiene ningún propósito comercial.</br>Se pone a disposición de los usuarios <b>tal cual</b>, sin ninguna garantía expresa o implícita de ningún tipo, incluyendo pero no limitándose a garantías de idoneidad para un propósito particular, exactitud, integridad o disponibilidad. Los derechos de autor, marcas y demás derechos de propiedad intelectual pertenecen a sus respectivos titulares. El uso de la información contenida en esta API se realiza bajo el principio del <b>uso justo</b> y para fines de enseñanza, investigación y análisis académico.</br></br><b>IMPORTANTE:</b></br><ul><li>El usuario es responsable de cumplir con todas las leyes y regulaciones aplicables en su jurisdicción en relación con el uso de los datos.</li></br><li>Se recomienda que, en caso de querer utilizar estos datos para otros fines (por ejemplo, publicaciones, proyectos comerciales o difusión pública), se consulte primero con los titulares de los derechos de la información original y se obtengan las autorizaciones correspondientes.</li></br><li>La administración de este proyecto no asume responsabilidad alguna por daños o perjuicios derivados del uso de la información aquí dispuesta.</li></ul></p>",
        "version": "1.0.1"
    },
    "host": "https://api-cafecito.onrender.com",  # Opcional: define el host
    "basePath": "/",                      # Opcional: define el path base
    "schemes": [
        "https"
    ],
    "securityDefinitions": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": "Token de acceso en formato Bearer: 'Bearer YOUR_AUTH_TOKEN'"
        }
    },
    "security": [
        {"Bearer": []}
    ]
}

swagger = Swagger(app, template=swagger_template)

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
    Endpoint que devuelve todas las competiciones disponibles.
    
    Parámetros opcionales en la query:
      - tournamentId: (numérico) para filtrar por torneo.
      - seasonId: (numérico) para filtrar también por temporada.
    
    Si no se reciben parámetros, se devuelve la lista completa de competiciones.

    <h3 class="code-line" data-line-start=0 data-line-end=1 >Ejemplo de uso con Python</h3>
    <pre><code class="has-line-data" data-line-start="3" data-line-end="14" color="#ffe">import requests

    base_url = &quot;https://api-cafecito.onrender.com&quot;
    headers = {&quot;Authorization&quot;: &quot;Bearer YOUR_AUTH_TOKEN&quot;}</br>
    
    # 1. Obtener la lista completa de competiciones (sin parámetros)
    url = f&quot;{base_url}/competitions&quot;
    response = requests.get(url, headers=headers)</br>
    print(&quot;Lista completa de competiciones:&quot;)
    print(response.json())

    # 2. Obtener la competición para tournamentId = 12
    params = {&quot;tournamentId&quot;: 12}
    response = requests.get(url, headers=headers, params=params)</br>
    print(&quot;Competiciones para tournamentId=12: &quot;)
    print(response.json())
        
    # 3. Obtener la competición para tournamentId = 12 y seasonId = 10456
    params = {&quot;tournamentId&quot;: 12, &quot;seasonId&quot;: 10456}
    response = requests.get(url, headers=headers, params=params)</br>
    print(&quot;Competición para tournamentId=12 y seasonId=10456:&quot;)
    print(response.json())

    </code></pre>
    ---
    tags:
      - Competiciones
    parameters:
      - name: tournamentId
        in: query
        type: integer
        required: false
        description: Filtrar competiciones por ID de torneo.
      - name: seasonId
        in: query
        type: integer
        required: false
        description: Filtrar competiciones por ID de temporada.
    responses:
      200:
        description: Lista completa de competiciones.
        schema:
          type: array
          items:
            type: object
            properties:
              tournamentId:
                type: integer
                example: 12
              seasonId:
                type: integer
                example: 10456
              stageId:
                type: integer
                example: 23663
              stageName:
                type: string
                example: "Champions League"
              regionId:
                type: integer
                example: 250
              tournamentName:
                type: string
                example: "Champions League"
              seasonName:
                type: string
                example: "2024/2025"
              competition:
                type: string
                example: "Europe-Champions-League-2024-2025"
      400:
        description: Error en los parámetros de entrada.
        schema:
          type: object
          properties:
            mensaje:
              type: string
              example: "tournamentId debe ser un número entero"
      404:
        description: No se encontraron competiciones con los parámetros indicados.
        schema:
          type: object
          properties:
            mensaje:
              type: string
              example: "No se encontraron competiciones con los parámetros indicados"
      500:
        description: Error interno al leer el archivo tournament.xlsx.
        schema:
          type: object
          properties:
            mensaje:
              type: string
              example: "Error al leer el archivo tournament.xlsx"
            error:
              type: string
              example: "Error de lectura..." 
    x-codeSamples:
      - lang: python
        source: |
          import requests
          base_url = "https://api-cafecito.onrender.com"
          headers = {"Authorization": "Bearer YOUR_AUTH_TOKEN"}
          
          # Ejemplo con parámetros
          url_params = f"{base_url}/competitions?tournamentId=12&seasonId=10456"
          response = requests.get(url_params, headers=headers)
          print(response.json())
          
          # Ejemplo sin parámetros
          response_all = requests.get(f"{base_url}/competitions", headers=headers)
          print(response_all.json())   
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
    
    #Función auxiliar que lee el archivo CSV de partidos y retorna una lista de diccionarios.

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
    """
    Endpoint que trae todos los partidos disponibles.
    
    <h3 class="code-line" data-line-start=0 data-line-end=1 >Ejemplo de uso con Python</h3>
    <pre><code class="has-line-data" data-line-start="3" data-line-end="14" color="#ffe">import requests

    base_url = &quot;https://api-cafecito.onrender.com&quot;
    headers = {&quot;Authorization&quot;: &quot;Bearer YOUR_AUTH_TOKEN&quot;}</br>
    
    url = f&quot;{base_url}/matches&quot;
    response = requests.get(url, headers=headers)</br>
    print(&quot;Todos los partidos:&quot;)
    print(response.json())
        
    </code></pre>
    ---
    tags:
      - Partidos
    responses:
      200:
        description: Lista completa de partidos.
        schema:
          type: array
          items:
            type: object
            properties:
              match_id:
                type: string
                example: "1866175"
              home_team:
                type: string
                example: "Atalanta"
              home_score:
                type: string
                example: "5"
              away_team:
                type: string
                example: "Sturm Graz"
              away_score:
                type: string
                example: "0"
              date:
                type: string
                example: "Tuesday, Jan 21 2025"
              time_or_status:
                type: string
                example: "FT"
              region:
                type: string
                example: "250"
              season:
                type: string
                example: "10456"
              stage:
                type: string
                example: "23663"
              tournament:
                type: string
                example: "12"
              competition:
                type: string
                example: "Europe-Champions-League-2024-2025"
              home_odds:
                type: string
                example: "N/A"
              draw_odds:
                type: string
                example: "N/A"
              away_odds:
                type: string
                example: "N/A"
      500:
        description: Error al leer el archivo CSV de partidos.
        schema:
          type: object
          properties:
            mensaje:
              type: string
              example: "Error al leer el archivo MATCHES_CSV"
    """
    matches = read_matches()
    return jsonify(matches)

# 2. Endpoint que trae los partidos de una competición específica
@app.route("/matches/competition/<competition>", methods=["GET"])
@token_required
def get_matches_by_competition(competition):
    """
    Endpoint que devuelve los partidos filtrados por competición.
    
    <h3 class="code-line" data-line-start=0 data-line-end=1 >Ejemplo de uso con Python</h3>
    <pre><code class="has-line-data" data-line-start="3" data-line-end="14" color="#ffe">import requests

    base_url = &quot;https://api-cafecito.onrender.com&quot;
    headers = {&quot;Authorization&quot;: &quot;Bearer YOUR_AUTH_TOKEN&quot;}</br>
   
    competition = &quot;Europe-Champions-League-2024-2025&quot;
    url = f&quot;{base_url}/matches/competition/{competition}&quot;
    response = requests.get(url, headers=headers)</br>
    print(f&quot;Partidos de la competición {competition}:&quot;)
    print(response.json())
        
    </code></pre>
    ---
    tags:
      - Partidos
    parameters:
      - name: competition
        in: path
        type: string
        required: true
        description: Nombre de la competición a filtrar, por ejemplo "Europe-Champions-League-2024-2025".
    responses:
      200:
        description: Lista de partidos para la competición indicada.
        schema:
          type: array
          items:
            type: object
            properties:
              match_id:
                type: string
                example: "1866175"
              home_team:
                type: string
                example: "Atalanta"
              home_score:
                type: string
                example: "5"
              away_team:
                type: string
                example: "Sturm Graz"
              away_score:
                type: string
                example: "0"
              date:
                type: string
                example: "Tuesday, Jan 21 2025"
              time_or_status:
                type: string
                example: "FT"
              region:
                type: string
                example: "250"
              season:
                type: string
                example: "10456"
              stage:
                type: string
                example: "23663"
              tournament:
                type: string
                example: "12"
              competition:
                type: string
                example: "Europe-Champions-League-2024-2025"
              home_odds:
                type: string
                example: "N/A"
              draw_odds:
                type: string
                example: "N/A"
              away_odds:
                type: string
                example: "N/A"
      404:
        description: No se encontraron partidos para la competición indicada.
        schema:
          type: object
          properties:
            mensaje:
              type: string
              example: "No se encontraron partidos para la competición 'Europe-Champions-League-2024-2025'"
    """
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
    """
    Endpoint que trae los partidos de una competición y una temporada específicas.
    
    <h3 class="code-line" data-line-start=0 data-line-end=1 >Ejemplo de uso con Python</h3>
    <pre><code class="has-line-data" data-line-start="3" data-line-end="14" color="#ffe">import requests

    base_url = &quot;https://api-cafecito.onrender.com&quot;
    headers = {&quot;Authorization&quot;: &quot;Bearer YOUR_AUTH_TOKEN&quot;}</br>
    
    season = &quot;10456&quot;
    competition = &quot;Europe-Champions-League-2024-2025&quot;
    response = requests.get(f&quot;{base_url}/matches/competition/{competition}/season/{season}&quot;, headers=headers)</br>
    print(f&quot;Partidos para la competición '{competition}' y la temporada '{season}':&quot;)
    print(response.json())
        
    </code></pre>
    ---
    tags:
      - Partidos
    parameters:
      - name: competition
        in: path
        type: string
        required: true
        description: >
          El nombre de la competición a filtrar. Por ejemplo, "Europe-Champions-League-2024-2025".
      - name: season
        in: path
        type: string
        required: true
        description: >
          La temporada a filtrar. Por ejemplo, "10456".
    responses:
      200:
        description: Lista de partidos para la competición y temporada especificadas.
        schema:
          type: array
          items:
            type: object
            properties:
              match_id:
                type: string
                example: "1866175"
              home_team:
                type: string
                example: "Atalanta"
              home_score:
                type: string
                example: "5"
              away_team:
                type: string
                example: "Sturm Graz"
              away_score:
                type: string
                example: "0"
              date:
                type: string
                example: "Tuesday, Jan 21 2025"
              time_or_status:
                type: string
                example: "FT"
              region:
                type: string
                example: "250"
              season:
                type: string
                example: "10456"
              stage:
                type: string
                example: "23663"
              tournament:
                type: string
                example: "12"
              competition:
                type: string
                example: "Europe-Champions-League-2024-2025"
              home_odds:
                type: string
                example: "N/A"
              draw_odds:
                type: string
                example: "N/A"
              away_odds:
                type: string
                example: "N/A"
      404:
        description: No se encontraron partidos para la competición y temporada indicadas.
        schema:
          type: object
          properties:
            mensaje:
              type: string
              example: "No se encontraron partidos para la competición 'Europe-Champions-League-2024-2025' y la temporada '10456'"
    """
    matches = read_matches()
    filtered = [
        m for m in matches 
        if m.get("competition", "").lower() == competition.lower() and m.get("season", "") == season
    ]
    if not filtered:
        return jsonify({"mensaje": f"No se encontraron partidos para la competición '{competition}' y la temporada '{season}'"}), 404
    return jsonify(filtered)

# 4. Endpoint que trae un partido en particular según su id
# @app.route("/matches/id/<match_id>", methods=["GET"])
# @token_required
# def get_match_by_id(match_id):
#     """
#     Endpoint que trae un partido en particular según su id.
    
#     <h3 class="code-line" data-line-start=0 data-line-end=1 >Ejemplo de uso con Python</h3>
#     <pre><code class="has-line-data" data-line-start="3" data-line-end="14" color="#ffe">import requests

#     base_url = &quot;https://api-cafecito.onrender.com&quot;
#     headers = {&quot;Authorization&quot;: &quot;Bearer YOUR_AUTH_TOKEN&quot;}</br>
#     match_id = &quot;1734855&quot;
#     url = f&quot;{base_url}/match/events/{match_id}&quot;
#     response = requests.get(url, headers=headers)</br>
#     print(&quot;Eventos del partido:&quot;)
#     print(response.json())
        
#     </code></pre>
#     ---
#     tags:
#       - Partido
#     parameters:
#       - name: match_id
#         in: path
#         type: string
#         required: true
#         description: El identificador único del partido a buscar.
#     responses:
#       200:
#         description: Partido encontrado.
#         schema:
#           type: object
#           properties:
#             match_id:
#               type: string
#               example: "1866175"
#             home_team:
#               type: string
#               example: "Atalanta"
#             home_score:
#               type: string
#               example: "5"
#             away_team:
#               type: string
#               example: "Sturm Graz"
#             away_score:
#               type: string
#               example: "0"
#             date:
#               type: string
#               example: "Tuesday, Jan 21 2025"
#             time_or_status:
#               type: string
#               example: "FT"
#             region:
#               type: string
#               example: "250"
#             season:
#               type: string
#               example: "10456"
#             stage:
#               type: string
#               example: "23663"
#             tournament:
#               type: string
#               example: "12"
#             competition:
#               type: string
#               example: "Europe-Champions-League-2024-2025"
#             home_odds:
#               type: string
#               example: "N/A"
#             draw_odds:
#               type: string
#               example: "N/A"
#             away_odds:
#               type: string
#               example: "N/A"
#       404:
#         description: Partido no encontrado.
#         schema:
#           type: object
#           properties:
#             mensaje:
#               type: string
#               example: "No se encontró el partido con id '1866175'"
#     """
#     matches = read_matches()
#     for match in matches:
#         if match.get("match_id") == match_id:
#             return jsonify(match)
#     return jsonify({"mensaje": f"No se encontró el partido con id '{match_id}'"}), 404

@app.route("/match/<match_id>", methods=["GET"])
@token_required
def get_match_json(match_id):
    """
    Endpoint que recibe el match id y devuelve el contenido completo del partido en crudo.

    <h3 class="code-line" data-line-start=0 data-line-end=1 >Ejemplo de uso con Python</h3>
    <pre><code class="has-line-data" data-line-start="3" data-line-end="14" color="#ffe">import requests

    base_url = &quot;https://api-cafecito.onrender.com&quot;
    headers = {&quot;Authorization&quot;: &quot;Bearer YOUR_AUTH_TOKEN&quot;}</br>
    match_id = &quot;1734855&quot;
    url = f&quot;{base_url}/match/{match_id}&quot;
    response = requests.get(url, headers=headers)</br>

    if response.status_code == 200:
        print(&quot;Contenido del Partido:&quot;)
        print(response.json())
    else:
        print(&quot;Error:&quot;, response.status_code, response.json())

    </code></pre>
    ---
    tags:
      - Partido
    parameters:
      - name: match_id
        in: path
        type: string
        required: true
        description: El identificador único del partido a buscar.
    responses:
      200:
        description: El archivo JSON completo con todos los datos del partido.
        schema:
          type: object
          properties:
            matchId:
              type: integer
              example: 1866142
            matchCentreData:
              type: object
              properties:
                playerIdNameDictionary:
                  type: object
                  description: Diccionario de IDs de jugadores a nombres.
                  example: {"100962": "Berat Djimsiti", "386390": "Charles De Ketelaere", "...": "..."}
                periodMinuteLimits:
                  type: object
                  description: Límites de minutos por periodo.
                  example: {"1": 45, "2": 90, "3": 105, "4": 120}
                timeStamp:
                  type: string
                  example: "2024-12-11 05:49:57"
                attendance:
                  type: integer
                  example: 22967
                venueName:
                  type: string
                  example: "Gewiss Stadium"
                referee:
                  type: object
                  properties:
                    officialId:
                      type: integer
                      example: 1163
                    firstName:
                      type: string
                      example: "Szymon"
                    lastName:
                      type: string
                      example: "Marciniak"
                    hasParticipatedMatches:
                      type: boolean
                      example: false
                    name:
                      type: string
                      example: "Szymon Marciniak"
                weatherCode:
                  type: string
                  example: ""
                elapsed:
                  type: string
                  example: "F"
                startTime:
                  type: string
                  example: "2024-12-10T21:00:00"
                startDate:
                  type: string
                  example: "2024-12-10T00:00:00"
                score:
                  type: string
                  example: "2 : 3"
                htScore:
                  type: string
                  example: "1 : 1"
                ftScore:
                  type: string
                  example: "2 : 3"
                etScore:
                  type: string
                  example: ""
                pkScore:
                  type: string
                  example: ""
                statusCode:
                  type: integer
                  example: 6
                periodCode:
                  type: integer
                  example: 7
                home:
                  type: object
                  properties:
                    teamId:
                      type: integer
                      example: 300
                    formations:
                      type: array
                      items:
                        type: object
                    stats:
                      type: object
                    incidentEvents:
                      type: array
                      items:
                        type: object
                    shotZones:
                      type: object
                    name:
                      type: string
                      example: "Atalanta"
                    countryName:
                      type: string
                      example: "Italia"
                    players:
                      type: array
                      items:
                        type: object
                    managerName:
                      type: string
                      example: "Gian Piero Gasperini"
                    scores:
                      type: object
                      properties:
                        halftime:
                          type: integer
                          example: 1
                        fulltime:
                          type: integer
                          example: 2
                        running:
                          type: integer
                          example: 2
                    field:
                      type: string
                      example: "home"
                    averageAge:
                      type: number
                      example: 27.2
                away:
                  type: object
                  properties:
                    teamId:
                      type: integer
                      example: 52
                    formations:
                      type: array
                      items:
                        type: object
                    stats:
                      type: object
                    incidentEvents:
                      type: array
                      items:
                        type: object
                    shotZones:
                      type: object
                    name:
                      type: string
                      example: "Real Madrid"
                    countryName:
                      type: string
                      example: "España"
                    players:
                      type: array
                      items:
                        type: object
                    managerName:
                      type: string
                      example: "Carlo Ancelotti"
                    scores:
                      type: object
                      properties:
                        halftime:
                          type: integer
                          example: 1
                        fulltime:
                          type: integer
                          example: 3
                        running:
                          type: integer
                          example: 3
                    field:
                      type: string
                      example: "away"
                    averageAge:
                      type: number
                      example: 25.1
                maxMinute:
                  type: integer
                  example: 94
                minuteExpanded:
                  type: integer
                  example: 97
                maxPeriod:
                  type: integer
                  example: 2
                expandedMinutes:
                  type: object
                  example: {"1": {}, "2": {}}
                expandedMaxMinute:
                  type: integer
                  example: 97
                periodEndMinutes:
                  type: object
                  example: {"1": 47, "2": 94}
                commonEvents:
                  type: array
                  items:
                    type: object
                events:
                  type: array
                  items:
                    type: object
                    properties:
                      id:
                        type: number
                        example: 2757746379.0
                      eventId:
                        type: number
                        example: 2
                      minute:
                        type: number
                        example: 0
                      second:
                        type: number
                        example: 0
                      teamId:
                        type: number
                        example: 52
                      x:
                        type: number
                        example: 0.0
                      y:
                        type: number
                        example: 0.0
                      expandedMinute:
                        type: number
                        example: 0
                      period:
                        type: object
                        properties:
                          value:
                            type: number
                            example: 1
                          displayName:
                            type: string
                            example: "FirstHalf"
                      type:
                        type: object
                        properties:
                          value:
                            type: number
                            example: 32
                          displayName:
                            type: string
                            example: "Start"
                      outcomeType:
                        type: object
                        properties:
                          value:
                            type: number
                            example: 1
                          displayName:
                            type: string
                            example: "Successful"
                      qualifiers:
                        type: array
                        items:
                          type: object
                      satisfiedEventsTypes:
                        type: array
                        items:
                          type: number
                      isTouch:
                        type: boolean
                        example: false
                timeoutInSeconds:
                  type: number
                  example: 0
            matchCentreEventTypeJson:
              type: object
              description: Diccionario de tipos de eventos.
              example: {"shotSixYardBox": 0, "shotPenaltyArea": 1, "...": "..."}
            formationIdNameMappings:
              type: object
              description: Mapeo de id de formaciones a nombres.
              example: {"2": "442", "3": "41212", "...": "..."}
      404:
        description: No se encontró el partido con el id indicado.
        schema:
          type: object
          properties:
            mensaje:
              type: string
              example: "No se encontró el partido con id '1866142'"
      500:
        description: Error al leer el archivo JSON.
        schema:
          type: object
          properties:
            mensaje:
              type: string
              example: "Error al leer el archivo JSON"
            error:
              type: string
              example: "Error de lectura..."
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
    Endpoint que devuelve la información base del partido.

    La respuesta incluye datos generales del partido, información del árbitro, y datos de
    los equipos local y visitante. La estructura de la respuesta es la siguiente:

    {
        "matchId": 1866142,
        "timeStamp": "2024-12-11 05:49:57",
        "attendance": 22967,
        "venueName": "Gewiss Stadium",
        "referee_officialId": 1163,
        "referee_name": "Szymon Marciniak",
        "weatherCode": "",
        "elapsed": "F",
        "startTime": "2024-12-10T21:00:00",
        "startDate": "2024-12-10T00:00:00",
        "score": "2 : 3",
        "htScore": "1 : 1",
        "ftScore": "2 : 3",
        "etScore": "",
        "statusCode": 6,
        "periodCode": 7,
        "maxMinute": 94,
        "minuteExpanded": 97,
        "maxPeriod": 2,
        "expandedMaxMinute": 97,
        "periodEndMinutes_1": 47,
        "periodEndMinutes_2": 94,
        "timeoutInSeconds": 0,
        "home_id": 300,
        "home_name": "Atalanta",
        "home_countryName": "Italia",
        "home_managerName": "Gian Piero Gasperini",
        "home_averageAge": 27.2,
        "away_id": 52,
        "away_name": "Real Madrid",
        "away_countryName": "España",
        "away_managerName": "Carlo Ancelotti",
        "away_averageAge": 25.1
    }

    <h3 class="code-line" data-line-start=0 data-line-end=1 >Ejemplo de uso con Python</h3>
    <pre><code class="has-line-data" data-line-start="3" data-line-end="14" color="#ffe">import requests

    base_url = &quot;https://api-cafecito.onrender.com&quot;
    headers = {&quot;Authorization&quot;: &quot;Bearer YOUR_AUTH_TOKEN&quot;}</br>
    match_id = &quot;1734855&quot;
    url = f&quot;{base_url}/match/base/{match_id}&quot;
    response = requests.get(url, headers=headers)</br>

    if response.status_code == 200:
        base_info = response.json()
        print(&quot;Información base del partido:&quot;)
        print(base_info)
    else:
        print(&quot;Error:&quot;, response.status_code, response.json())
        
    </code></pre>
    ---
    tags:
      - Partido
    parameters:
      - name: match_id
        in: path
        type: string
        required: true
        description: El identificador único del partido a buscar.
    responses:
      200:
        description: Información base del partido.
        schema:
          type: object
          properties:
            matchId:
              type: integer
              example: 1866142
            timeStamp:
              type: string
              example: "2024-12-11 05:49:57"
            attendance:
              type: integer
              example: 22967
            venueName:
              type: string
              example: "Gewiss Stadium"
            referee_officialId:
              type: integer
              example: 1163
            referee_name:
              type: string
              example: "Szymon Marciniak"
            weatherCode:
              type: string
              example: ""
            elapsed:
              type: string
              example: "F"
            startTime:
              type: string
              example: "2024-12-10T21:00:00"
            startDate:
              type: string
              example: "2024-12-10T00:00:00"
            score:
              type: string
              example: "2 : 3"
            htScore:
              type: string
              example: "1 : 1"
            ftScore:
              type: string
              example: "2 : 3"
            etScore:
              type: string
              example: ""
            statusCode:
              type: integer
              example: 6
            periodCode:
              type: integer
              example: 7
            maxMinute:
              type: integer
              example: 94
            minuteExpanded:
              type: integer
              example: 97
            maxPeriod:
              type: integer
              example: 2
            expandedMaxMinute:
              type: integer
              example: 97
            periodEndMinutes_1:
              type: integer
              example: 47
            periodEndMinutes_2:
              type: integer
              example: 94
            timeoutInSeconds:
              type: integer
              example: 0
            home_id:
              type: integer
              example: 300
            home_name:
              type: string
              example: "Atalanta"
            home_countryName:
              type: string
              example: "Italia"
            home_managerName:
              type: string
              example: "Gian Piero Gasperini"
            home_averageAge:
              type: number
              example: 27.2
            away_id:
              type: integer
              example: 52
            away_name:
              type: string
              example: "Real Madrid"
            away_countryName:
              type: string
              example: "España"
            away_managerName:
              type: string
              example: "Carlo Ancelotti"
            away_averageAge:
              type: number
              example: 25.1
      404:
        description: No se encontró el partido con el id indicado.
        schema:
          type: object
          properties:
            mensaje:
              type: string
              example: "No se encontró el partido con id '1866142'"
      500:
        description: Error al leer el archivo JSON.
        schema:
          type: object
          properties:
            mensaje:
              type: string
              example: "Error al leer el archivo JSON"
            error:
              type: string
              example: "Error de lectura..."
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

    <h3 class="code-line" data-line-start=0 data-line-end=1 >Ejemplo de uso con Python</h3>
    <pre><code class="has-line-data" data-line-start="3" data-line-end="14" color="#ffe">import requests

    base_url = &quot;https://api-cafecito.onrender.com&quot;
    headers = {&quot;Authorization&quot;: &quot;Bearer YOUR_AUTH_TOKEN&quot;}</br>
    match_id = &quot;1734855&quot;
    url = f&quot;{base_url}/match/stats/{match_id}&quot;

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        stats = response.json()
        print(&quot;Stats del equipo local y visitante:&quot;)
        print(stats)
    else:
        print(&quot;Error:&quot;, response.status_code, response.json())
        
    </code></pre>
    ---
    tags:
      - Partido
    parameters:
      - name: match_id
        in: path
        type: string
        required: true
        description: El identificador único del partido.
    responses:
      200:
        description: Objeto JSON con los stats del equipo local y visitante.
        schema:
          type: object
          properties:
            matchId:
              type: integer
              example: 1866175
            homeStats:
              type: object
              description: Estadísticas del equipo local (contenidas en matchCentreData > home > stats).
              example: {"goals": 2, "shots": 15}
            awayStats:
              type: object
              description: Estadísticas del equipo visitante (contenidas en matchCentreData > away > stats).
              example: {"goals": 3, "shots": 18}
      404:
        description: No se encontró el partido con el id indicado.
        schema:
          type: object
          properties:
            mensaje:
              type: string
              example: "No se encontró el partido con id '1866175'"
      500:
        description: Error al leer el archivo JSON.
        schema:
          type: object
          properties:
            mensaje:
              type: string
              example: "Error al leer el archivo JSON"
            error:
              type: string
              example: "Error de lectura..."
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
    Endpoint que devuelve los incidentEvents del partido, obtenidos de cada equipo.
      
    <h3 class="code-line" data-line-start=0 data-line-end=1 >Ejemplo de uso con Python</h3>
    <pre><code class="has-line-data" data-line-start="3" data-line-end="14" color="#ffe">import requests

    base_url = &quot;https://api-cafecito.onrender.com&quot;
    headers = {&quot;Authorization&quot;: &quot;Bearer YOUR_AUTH_TOKEN&quot;}</br>
    match_id = &quot;1734855&quot;
    
    url = f&quot;{base_url}/match/incidentEvents/{match_id}&quot;

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        incident_events = response.json()
        print(&quot;Incident Events del equipo local:&quot;)
        print(incident_events.get(&quot;homeIncidentEvents&quot;))
        print(&quot;Incident Events del equipo visitante:&quot;)
        print(incident_events.get(&quot;awayIncidentEvents&quot;))
    else:
        print(&quot;Error:&quot;, response.status_code, response.json())
        
    </code></pre>
    ---
    tags:
      - Partido
    parameters:
      - name: match_id
        in: path
        type: string
        required: true
        description: El identificador único del partido.
    responses:
      200:
        description: Objeto JSON que contiene los incidentEvents del partido.
        schema:
          type: object
          properties:
            matchId:
              type: integer
              example: 1866142
            homeIncidentEvents:
              type: array
              items:
                type: object
              description: Lista de incidentEvents del equipo local (matchCentreData["home"]["incidentEvents"]).
            awayIncidentEvents:
              type: array
              items:
                type: object
              description: Lista de incidentEvents del equipo visitante (matchCentreData["away"]["incidentEvents"]).
      404:
        description: Partido no encontrado.
        schema:
          type: object
          properties:
            mensaje:
              type: string
              example: "No se encontró el partido con id '1866142'"
      500:
        description: Error al leer el archivo JSON.
        schema:
          type: object
          properties:
            mensaje:
              type: string
              example: "Error al leer el archivo JSON"
            error:
              type: string
              example: "Detalle del error"
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

    # Accedemos a matchCentreData
    match_centre = match_data.get("matchCentreData", {})

    # Extraemos los incidentEvents de cada equipo
    home_incident_events = match_centre.get("home", {}).get("incidentEvents", [])
    away_incident_events = match_centre.get("away", {}).get("incidentEvents", [])

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
    Devuelve la lista de jugadores que participaron en el partido, junto con el matchId y el nombre de cada equipo.

    La respuesta tendrá la siguiente estructura:
    {
      "matchId": <matchId>,
      "homeTeamName": <nombre del equipo local>,
      "awayTeamName": <nombre del equipo visitante>,
      "homePlayers": [
          {
              "teamId": <id del equipo>,
              "playerId": <id del jugador>,
              "playerName": <nombre del jugador>,
              "jerseyNumber": <número de camiseta>,
              "matchStart": <1 si es titular, 0 si es suplente>,
              "formationSlot": <posición asignada en la formación o None>
          },
          ...
      ],
      "awayPlayers": [ ... ]
    }

    <h3 class="code-line" data-line-start=0 data-line-end=1 >Ejemplo de uso con Python</h3>
    <pre><code class="has-line-data" data-line-start="3" data-line-end="14" color="#ffe">import requests

    base_url = &quot;https://api-cafecito.onrender.com&quot;
    headers = {&quot;Authorization&quot;: &quot;Bearer YOUR_AUTH_TOKEN&quot;}</br>
    match_id = &quot;1734855&quot;

    url = f&quot;{base_url}/match/players/{match_id}&quot;

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        players = response.json()
        print(&quot;Jugadores del equipo local:&quot;)
        for player in players.get(&quot;homePlayers&quot;, []):
            print(player)
        print(&quot;Jugadores del equipo visitante:&quot;)
        for player in players.get(&quot;awayPlayers&quot;, []):
            print(player)
    else:
        print(&quot;Error:&quot;, response.status_code, response.json())

    </code></pre>
    ---
    tags:
      - Partido
    parameters:
      - name: match_id
        in: path
        type: string
        required: true
        description: Identificador único del partido.
    responses:
      200:
        description: Objeto JSON con la información del partido y la lista de jugadores.
        schema:
          type: object
          properties:
            matchId:
              type: integer
              example: 1866142
            homeTeamName:
              type: string
              example: "Atalanta"
            awayTeamName:
              type: string
              example: "Real Madrid"
            homePlayers:
              type: array
              items:
                type: object
                properties:
                  teamId:
                    type: integer
                    example: 300
                  playerId:
                    type: integer
                    example: 383278
                  playerName:
                    type: string
                    example: "Marco Carnesecchi"
                  jerseyNumber:
                    type: string
                    example: "29"
                  matchStart:
                    type: integer
                    example: 1
                  formationSlot:
                    type: integer
                    example: 1
            awayPlayers:
              type: array
              items:
                type: object
                properties:
                  teamId:
                    type: integer
                    example: 52
                  playerId:
                    type: integer
                    example: 73798
                  playerName:
                    type: string
                    example: "Thibaut Courtois"
                  jerseyNumber:
                    type: string
                    example: "1"
                  matchStart:
                    type: integer
                    example: 1
                  formationSlot:
                    type: integer
                    example: 1
      404:
        description: Partido no encontrado.
        schema:
          type: object
          properties:
            mensaje:
              type: string
              example: "No se encontró el partido con id '1866142'"
      500:
        description: Error al leer el archivo JSON.
        schema:
          type: object
          properties:
            mensaje:
              type: string
              example: "Error al leer el archivo JSON"
            error:
              type: string
              example: "Detalle del error"
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
    Devuelve todas las formaciones del equipo local y del equipo visitante para un partido dado.

    La respuesta tendrá la siguiente estructura:

    {
      "matchId": <matchId>,
      "homeFormations": [ ... ],
      "awayFormations": [ ... ]
    }

    <h3 class="code-line" data-line-start=0 data-line-end=1 >Ejemplo de uso con Python</h3>
    <pre><code class="has-line-data" data-line-start="3" data-line-end="14" color="#ffe">import requests

    base_url = &quot;https://api-cafecito.onrender.com&quot;
    headers = {&quot;Authorization&quot;: &quot;Bearer YOUR_AUTH_TOKEN&quot;}</br>
    
    match_id = &quot;1866142&quot;  # Ejemplo de id de partido
    url = f&quot;{base_url}/match/formations/{match_id}&quot;

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        formations = response.json()
        print(&quot;Match ID:&quot;, formations.get(&quot;matchId&quot;))
        print(&quot;Formaciones del equipo local:&quot;)
        for formation in formations.get(&quot;homeFormations&quot;, []):
            print(formation)
        print(&quot;Formaciones del equipo visitante:&quot;)
        for formation in formations.get(&quot;awayFormations&quot;, []):
            print(formation)
    else:
        print(&quot;Error:&quot;, response.status_code, response.json())
        
    </code></pre>
    ---
    tags:
      - Partido
    parameters:
      - name: match_id
        in: path
        type: string
        required: true
        description: Identificador del partido.
    responses:
      200:
        description: Formaciones obtenidas exitosamente.
        schema:
          type: object
          properties:
            matchId:
              type: integer
              example: 1734855
            homeFormations:
              type: array
              items:
                type: object
              example: [
                {
                  "captainPlayerId": 85070,
                  "endMinuteExpanded": 60,
                  "formationId": 18,
                  "formationName": "3412",
                  "formationPositions": [
                    {"horizontal": 5.0, "vertical": 0.0},
                    {"horizontal": 1.0, "vertical": 5.0},
                    {"horizontal": 9.0, "vertical": 5.0}
                    
                  ],
                  "formationSlots": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 0, 0, ...],
                  "jerseyNumbers": [29, 16, 22, 23, 4, 19, 15, 13, 8, 17, 11, ...],
                  "period": 16,
                  "playerIds": [383278, 349184, 402046, ...],
                  "startMinuteExpanded": 0
                }
              ]
            awayFormations:
              type: array
              items:
                type: object
              example: [
                {
                  "captainPlayerId": 144511,
                  "endMinuteExpanded": 29,
                  "formationId": 8,
                  "formationName": "4231",
                  "formationPositions": [
                    {"horizontal": 5.0, "vertical": 0.0},
                    {"horizontal": 1.0, "vertical": 2.5},
                    {"horizontal": 9.0, "vertical": 2.5}
                    
                  ],
                  "formationSlots": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, ...],
                  "jerseyNumbers": [1, 17, 20, 8, 14, 22, 21, ...],
                  "period": 16,
                  "playerIds": [73798, 144511, 422957, ...],
                  "startMinuteExpanded": 0
                }
              ]
      404:
        description: Partido no encontrado.
        schema:
          type: object
          properties:
            mensaje:
              type: string
              example: "No se encontró el partido con id '1734855'"
      500:
        description: Error al leer el archivo JSON.
        schema:
          type: object
          properties:
            mensaje:
              type: string
              example: "Error al leer el archivo JSON"
            error:
              type: string
              example: "Detalle del error"
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
    Obtiene todos los eventos del partido.

    <h3 class="code-line" data-line-start=0 data-line-end=1 >Ejemplo de uso con Python</h3>
    <pre><code class="has-line-data" data-line-start="3" data-line-end="14" color="#ffe">import requests

    base_url = &quot;https://api-cafecito.onrender.com&quot;
    headers = {&quot;Authorization&quot;: &quot;Bearer YOUR_AUTH_TOKEN&quot;}</br>

    match_id = &quot;1866142&quot;  # Ejemplo de id de partido
    url = f&quot;{base_url}/match/events/{match_id}&quot;

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        result = response.json()
        print(&quot;Match ID:&quot;, result.get(&quot;matchId&quot;))
        print(&quot;Eventos:&quot;)
        for event in result.get(&quot;events&quot;, []):
            print(event)
    else:
        print(&quot;Error:&quot;, response.status_code, response.json())

    </code></pre>
    ---
    tags:
      - Partido
    parameters:
      - name: match_id
        in: path
        type: string
        required: true
        description: El ID del partido.
    responses:
      200:
        description: Una lista de eventos del partido.
        schema:
          type: object
          properties:
            matchId:
              type: integer
              example: 1734855
            events:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: number
                    example: 2757746379.0
                  eventId:
                    type: number
                    example: 2
                  minute:
                    type: number
                    example: 0
                  second:
                    type: number
                    example: 0
                  teamId:
                    type: number
                    example: 52
                  x:
                    type: number
                    example: 0.0
                  y:
                    type: number
                    example: 0.0
                  expandedMinute:
                    type: number
                    example: 0
                  period:
                    type: object
                    properties:
                      value:
                        type: number
                        example: 1
                      displayName:
                        type: string
                        example: "FirstHalf"
                  type:
                    type: object
                    properties:
                      value:
                        type: number
                        example: 32
                      displayName:
                        type: string
                        example: "Start"
                  outcomeType:
                    type: object
                    properties:
                      value:
                        type: number
                        example: 1
                      displayName:
                        type: string
                        example: "Successful"
                  qualifiers:
                    type: array
                    items:
                      type: object
                    example: []
                  satisfiedEventsTypes:
                    type: array
                    items:
                      type: number
                    example: []
                  isTouch:
                    type: boolean
                    example: false
      404:
        description: Partido no encontrado.
        schema:
          type: object
          properties:
            mensaje:
              type: string
              example: "No se encontró el partido con id '1734855'"
      500:
        description: Error al leer el archivo JSON.
        schema:
          type: object
          properties:
            mensaje:
              type: string
              example: "Error al leer el archivo JSON"
            error:
              type: string
              example: "Detalle del error"
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

    <h3 class="code-line" data-line-start=0 data-line-end=1 >Ejemplo de uso con Python</h3>
    <pre><code class="has-line-data" data-line-start="3" data-line-end="14" color="#ffe">import requests

    base_url = &quot;https://api-cafecito.onrender.com&quot;
    headers = {&quot;Authorization&quot;: &quot;Bearer YOUR_AUTH_TOKEN&quot;}</br>

    match_id = &quot;1866142&quot;  # Ejemplo de id de partido
    url = f&quot;{base_url}/match/matchCentreEventTypeJson/{match_id}&quot;
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        result = response.json()
        print(&quot;matchCentreEventTypeJson:&quot;)
        print(result)
    else:
        print(&quot;Error:&quot;, response.status_code, response.json())
        
    </code></pre>
    ---
    tags:
      - Partido
    parameters:
      - name: match_id
        in: path
        type: string
        required: true
        description: El ID del partido.
    responses:
      200:
        description: Objeto con el matchId y el diccionario matchCentreEventTypeJson.
        schema:
          type: object
          properties:
            matchId:
              type: integer
              example: 1734855
            matchCentreEventTypeJson:
              type: object
              description: Diccionario que mapea nombres de eventos a sus códigos.
              example:
                aerialSuccess: 196
                assist: 92
                assistCorner: 48
                assistCross: 47
                assistFreekick: 50
                # ... (otros mapeos)
      404:
        description: Partido no encontrado.
        schema:
          type: object
          properties:
            mensaje:
              type: string
              example: "No se encontró el partido con id '1734855'"
      500:
        description: Error al leer el archivo JSON.
        schema:
          type: object
          properties:
            mensaje:
              type: string
              example: "Error al leer el archivo JSON"
            error:
              type: string
              example: "Detalle del error"
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

    <h3 class="code-line" data-line-start=0 data-line-end=1 >Ejemplo de uso con Python</h3>
    <pre><code class="has-line-data" data-line-start="3" data-line-end="14" color="#ffe">import requests

    base_url = &quot;https://api-cafecito.onrender.com&quot;
    headers = {&quot;Authorization&quot;: &quot;Bearer YOUR_AUTH_TOKEN&quot;}</br>

    match_id = &quot;1866142&quot;  # Ejemplo de id de partido
    url = f&quot;{base_url}/match/formationIdNameMappings/{match_id}&quot;
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        result = response.json()
        print(&quot;formationIdNameMappings:&quot;)
        print(result)
    else:
        print(&quot;Error:&quot;, response.status_code, response.json())
        
    </code></pre>
    ---
    tags:
      - Partido
    parameters:
      - name: match_id
        in: path
        type: string
        required: true
        description: El ID del partido.
    responses:
      200:
        description: Objeto que contiene el matchId y el diccionario formationIdNameMappings.
        schema:
          type: object
          properties:
            matchId:
              type: integer
              example: 1734855
            formationIdNameMappings:
              type: object
              description: Diccionario que mapea los formation IDs a sus nombres.
              example:
                10: "532"
                11: "541"
                12: "352"
                13: "343"
                14: "31312"
                15: "4222"
                16: "3511"
                17: "3421"
                18: "3412"
                19: "3142"
                2: "442"
                20: "343d"
                21: "4132"
                22: "4240"
                23: "4312"
                24: "3241"
                25: "3331"
                3: "41212"
                4: "433"
                5: "451"
                6: "4411"
                7: "4141"
                8: "4231"
                9: "4321"
      404:
        description: Partido no encontrado.
        schema:
          type: object
          properties:
            mensaje:
              type: string
              example: "No se encontró el partido con id '1734855'"
      500:
        description: Error al leer el archivo JSON.
        schema:
          type: object
          properties:
            mensaje:
              type: string
              example: "Error al leer el archivo JSON"
            error:
              type: string
              example: "Detalle del error"
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

@app.route("/features/qualifiers", methods=["GET"])
@token_required
def get_qualifiers():
    """
    Devuelve la lista de qualifiers.

    <h3 class="code-line" data-line-start=0 data-line-end=1 >Ejemplo de uso con Python</h3>
    <pre><code class="has-line-data" data-line-start="3" data-line-end="14" color="#ffe">import requests

    base_url = &quot;https://api-cafecito.onrender.com&quot;
    headers = {&quot;Authorization&quot;: &quot;Bearer YOUR_AUTH_TOKEN&quot;}</br>
    
    url_qualifiers = f&quot;{base_url}/features/qualifiers&quot;
    response = requests.get(url_qualifiers, headers=headers)
    if response.status_code == 200:
        qualifiers = response.json()
        print(&quot;Qualifiers:&quot;)
        for q in qualifiers:
            print(q)
    else:
        print(&quot;Error:&quot;, response.status_code, response.json())

    </code></pre>
    ---
    tags:
      - Variables
    responses:
      200:
        description: Una lista de qualifiers extraída del archivo qualifiers.csv.
        schema:
          type: array
          items:
            type: object
            properties:
              qualifierId:
                type: string
                example: "1"
              QUALIFIER NAME:
                type: string
                example: "Long ball"
      500:
        description: Error al leer el archivo qualifiers.csv.
        schema:
          type: object
          properties:
            mensaje:
              type: string
              example: "Error al leer el archivo qualifiers.csv"
            error:
              type: string
              example: "Detalle del error"
    """
    filename = "qualifiers.csv"
    qualifiers = []
    try:
        with open(filename, encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile, delimiter=";")
            for row in reader:
                qualifiers.append(row)
    except Exception as e:
        return jsonify({"mensaje": "Error al leer el archivo qualifiers.csv", "error": str(e)}), 500

    return jsonify(qualifiers)

@app.route("/features/typeId", methods=["GET"])
@token_required
def get_typeId():
    """
    Devuelve la lista de registros extraída de typeId.

    <h3 class="code-line" data-line-start=0 data-line-end=1 >Ejemplo de uso con Python</h3>
    <pre><code class="has-line-data" data-line-start="3" data-line-end="14" color="#ffe">import requests

    base_url = &quot;https://api-cafecito.onrender.com&quot;
    headers = {&quot;Authorization&quot;: &quot;Bearer YOUR_AUTH_TOKEN&quot;}</br>
    
    url_typeid = f&quot;{base_url}/features/typeId&quot;
    response = requests.get(url_typeid, headers=headers)
    if response.status_code == 200:
        type_ids = response.json()
        print(&quot;TypeId:&quot;)
        for t in type_ids:
            print(t)
    else:
        print(&quot;Error:&quot;, response.status_code, response.json())
        
    </code></pre>
    ---
    tags:
      - Variables
    responses:
      200:
        description: Una lista de registros extraída del archivo typeId.csv.
        schema:
          type: array
          items:
            type: object
            properties:
              typeId:
                type: string
                example: "1"
              EVENT NAME:
                type: string
                example: "Pass"
              DESCRIPTION:
                type: string
                example: "The attempted delivery of the ball from one player to another player on the same team. A player can use any part of their body (permitted in the laws of the game) to execute a pass. Event categorization includes open play passes, goal kicks, corners and free kicks played as passes. Crosses, keeper throws, and throw ins do not count as passes. outcome: 0 = Unsuccessful pass = pass did not find teammate | 1 = Successful pass"
              ASSOCIATED qualifierId VALUES:
                type: string
                example: "1, 2, 3, 4, 5, 6, 15, 22, 23, 24, 25, 26, 29, 31, 55, 56, 74, 96, 97, 106, 107, 123, 124, 138, 140, 141, 152, 154, 155, 156, 157, 160, 168, 189, 195, 196, 198, 199, 210, 212, 213, 214, 218, 223, 224, 225, 233, 236, 237, 238, 240, 241, 266, 278, 279, 286, 287, 307, 345, 358, 359, 362, 459"
      500:
        description: Error al leer los datos typeId.
        schema:
          type: object
          properties:
            mensaje:
              type: string
              example: "Error al leer los datos de typeId"
            error:
              type: string
              example: "Detalle del error"
    """
    filename = "typeId.csv"
    type_ids = []
    try:
        with open(filename, encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile, delimiter=";")
            for row in reader:
                type_ids.append(row)
    except Exception as e:
        return jsonify({"mensaje": "Error al leer el archivo typeId.csv", "error": str(e)}), 500

    return jsonify(type_ids)

@app.route("/teams", methods=["GET"])
@token_required
def get_teams():
    """
    Devuelve la lista de equipos.

    <h3 class="code-line" data-line-start=0 data-line-end=1 >Ejemplo de uso con Python</h3>
    <pre><code class="has-line-data" data-line-start="3" data-line-end="14" color="#ffe">import requests

    base_url = &quot;https://api-cafecito.onrender.com&quot;
    headers = {&quot;Authorization&quot;: &quot;Bearer YOUR_AUTH_TOKEN&quot;}</br>
    
    url = f&quot;{base_url}/teams&quot;
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        teams = response.json()
        print(&quot;Teams:&quot;)
        for team in teams:
            print(team)
    else:
        print(&quot;Error:&quot;, response.status_code, response.json())
        
    </code></pre>
    ---
    tags:
      - Equipos
    responses:
      200:
        description: Lista de equipos extraída del archivo teams.csv.
        schema:
          type: array
          items:
            type: object
            properties:
              matchId:
                type: string
                example: "1866220"
              teamId:
                type: string
                example: "361"
              teamName:
                type: string
                example: "Salzburg"
              countryCode:
                type: string
                example: "at"
              countryName:
                type: string
                example: "Austria"
              imageUrl:
                type: string
                example: "https://d2zywfiolv4f83.cloudfront.net/img/teams/361.png"
      500:
        description: Error al leer el archivo teams.csv.
        schema:
          type: object
          properties:
            mensaje:
              type: string
              example: "Error al leer el archivo teams.csv"
            error:
              type: string
              example: "Detalle del error"
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

# if __name__ == "__main__":
#     app.run(debug=True)