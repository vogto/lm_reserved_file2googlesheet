import os
import csv
from datetime import datetime
from dotenv import load_dotenv
import mysql.connector
import requests

print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starte Script ...")

load_dotenv()

LOCAL_PATH_TOURENPLAN = os.getenv("LOCAL_PATH_TOURENPLAN")
MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")


def send_error_notification(message):
    webhook_url = os.getenv("GOOGLE_CHAT_WEBHOOK_URL")
    if webhook_url:
        payload = {"text": f"❗ *Fehler beim lm_reserved_file-Skript*\n\n```{message}```"}
        try:
            response = requests.post(webhook_url, json=payload)
            if response.status_code != 200:
                print(f"Fehler beim Senden der Google Chat Nachricht: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Fehler beim Versenden der Benachrichtigung: {e}")
    else:
        print("GOOGLE_CHAT_WEBHOOK_URL ist nicht gesetzt.")


def get_latest_file():
    files = [f for f in os.listdir(LOCAL_PATH_TOURENPLAN) if f.lower().endswith('.csv')]
    if not files:
        raise FileNotFoundError("Keine CSV-Dateien im Verzeichnis gefunden.")

    latest_file = max(files, key=lambda f: os.path.getmtime(os.path.join(LOCAL_PATH_TOURENPLAN, f)))
    latest_file_path = os.path.join(LOCAL_PATH_TOURENPLAN, latest_file)
    print(f"Verwende neueste Datei: {latest_file} (geändert am {datetime.fromtimestamp(os.path.getmtime(latest_file_path))})")
    return latest_file_path


def import_reservedfile_csv_to_mysql(filepath):
    print(f"Lese Datei: {filepath}")
    connection = None

    try:
        connection = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE
        )
        cursor = connection.cursor()
        print("Leere Tabelle lm_reserved_file ...")
        cursor.execute("TRUNCATE TABLE lm_reserved_file")

        with open(filepath, mode='r', encoding='utf-8', newline='') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            header = next(reader)

            expected_header = [
                "ARTIKELID", "STANDORTID", "AUSLIEFERTERMIN", "MENGE", "VERSORGUNG",
                "BESTELLNUMMER", "BESTELLPOSITION", "MENGENEINHEIT", "AUSLIEFERUNG",
                "AUSLIEFERWERK", "MENGE_ST"
            ]
            if [h.strip().upper() for h in header] != expected_header:
                raise ValueError(f"CSV-Header stimmt nicht überein. Erwartet: {expected_header}, gefunden: {header}")
            print(f"Header: {header}")

            row_count = 0
            for row in reader:
                if len(row) != 11:
                    print(f"Überspringe fehlerhafte Zeile (nicht 11 Felder): {row}")
                    continue

                create_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                sql = """
                    INSERT INTO lm_reserved_file 
                    (CREATE_DATE, ARTIKELID, STANDORTID, AUSLIEFERTERMIN, MENGE, VERSORGUNG,
                     BESTELLNUMMER, BESTELLPOSITION, MENGENEINHEIT, AUSLIEFERUNG, AUSLIEFERWERK, MENGE_ST)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(sql, (create_date, *row))
                row_count += 1

        connection.commit()
        print(f"Import abgeschlossen. {row_count} Zeilen eingefügt.")

    except Exception as e:
        if connection:
            connection.rollback()
        raise e

    finally:
        if connection:
            cursor.close()
            connection.close()


# Hauptlogik starten
try:
    filepath = get_latest_file()
    import_reservedfile_csv_to_mysql(filepath)
except Exception as e:
    print(f"Fehler: {e}")
    send_error_notification(str(e))
