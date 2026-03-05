import boto3
import json
import urllib.parse
import csv
from decimal import Decimal
from datetime import datetime

s3 = boto3.resource('s3')
dynamodb = boto3.resource('dynamodb')

table_raw = dynamodb.Table('Datos-Crudos')

def lambda_handler(event, context):
    # Registramos el evento que activa la función Lambda
    print("Evento recibido por la función Lambda: " + json.dumps(event, indent=2))

    # Extraemos el nombre del bucket y la clave del archivo desde el evento
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'])
    local_filename = '/tmp/data.csv'  # Especificamos una ubicación temporal para el archivo

    # Intentamos descargar el archivo CSV desde el bucket de S3
    try:
        s3.meta.client.download_file(bucket, key, local_filename)
        print(f'Archivo {key} descargado desde el bucket {bucket}')
    except Exception as e:
        print(f'Error al descargar el archivo: {e}')
        raise e  # Detenemos la ejecución si no podemos descargar el archivo

    # Leemos y procesamos el archivo CSV para cargar datos en DynamoDB
    try:
        with open(local_filename, encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)  # Leemos cada fila del archivo como un diccionario
            with table_raw.batch_writer() as batch:
                for row in reader:
                    try:
                        # Registramos la fila que estamos procesando
                        print(f"Procesamos la fila: {row['Fecha']}")

                        # Transformamos y preparamos los datos necesarios
                        date = datetime.strptime(row['Fecha'], '%Y/%m/%d')
                        month_year = date.strftime('%Y-%m')
                        media = Decimal(row['Medias'])
                        deviation = Decimal(row['Desviaciones'])

                        # Construimos el ítem que vamos a cargar en DynamoDB
                        raw_item = {
                            'Fecha': row['Fecha'],
                            'MonthYear': month_year,
                            'Media': media,
                            'Deviation': deviation,
                        }

                        # Insertamos el ítem en la tabla de DynamoDB
                        batch.put_item(Item=raw_item)
                        print(f"Ítem añadido: {raw_item}")

                    except Exception as e:
                        # Registramos cualquier error al procesar una fila y continuamos
                        print(f"Error al procesar la fila {row['Fecha']}: {e}")
                        continue

        print("¡Datos cargados exitosamente en DynamoDB!")
    except Exception as e:
        # Registramos cualquier error al procesar el archivo CSV
        print(f"Error al procesar el archivo CSV: {e}")
        raise e
