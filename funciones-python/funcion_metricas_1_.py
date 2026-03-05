import boto3
import json
from datetime import datetime, timedelta
from decimal import Decimal
from boto3.dynamodb.conditions import Key

# Conectamos con los recursos de DynamoDB
dynamodb = boto3.resource('dynamodb')
table_raw = dynamodb.Table('Datos-Crudos')  # Tabla que contiene los datos crudos
table_metrics = dynamodb.Table('Metrics')  # Tabla que almacenará las métricas calculadas

def lambda_handler(event, context):
    # Registramos el evento recibido por la función Lambda
    print("Evento recibido por la función Lambda: " + json.dumps(event, indent=2))

    # Utilizamos un `batch_writer` para realizar escrituras por lotes en DynamoDB
    with table_metrics.batch_writer() as batch:
        processed_month_years = set()  # Conjunto para evitar procesar duplicados del mismo mes-año

        try:
            # Iteramos sobre los registros del evento
            for record in event['Records']:
                newImage = record['dynamodb'].get('NewImage', None)  # Verificamos si existe una nueva imagen
                if newImage: 
                    # Extraemos los datos del registro
                    new_item = record['dynamodb']['NewImage']
                    month_year = new_item['MonthYear']['S']  # Obtenemos el mes-año del registro

                    # Saltamos el procesamiento si ya hemos manejado este mes-año
                    if month_year in processed_month_years:
                        continue
                    
                    processed_month_years.add(month_year)  # Marcamos este mes-año como procesado

                    # Consultamos los datos del mes-año en la tabla `Datos-Crudos`
                    response = table_raw.query(
                        IndexName='MonthYear-index',  # Índice secundario que permite buscar por MonthYear
                        KeyConditionExpression=Key('MonthYear').eq(month_year)
                    )
                    monthly_data = response['Items']  # Obtenemos los ítems de la consulta

                    # Calculamos las métricas del mes actual
                    total_media = sum(Decimal(item['Media']) for item in monthly_data)  # Suma total de las medias
                    max_deviation = max(Decimal(item['Deviation']) for item in monthly_data)  # Máxima desviación
                    max_temperature = max(Decimal(item['Media']) for item in monthly_data)  # Máxima temperatura
                    record_count = len(monthly_data)  # Contamos los registros del mes
                    average_media = total_media / record_count if record_count > 0 else 0  # Calculamos el promedio

                    # Calculamos el mes-año anterior
                    current_date = datetime.strptime(month_year + '-01', '%Y-%m-%d')  # Convertimos el mes-año a fecha
                    previous_month_year = (current_date.replace(day=1) - timedelta(days=1)).strftime('%Y-%m')  # Mes anterior

                    # Consultamos los datos del mes-año anterior
                    previous_response = table_raw.query(
                        IndexName='MonthYear-index',
                        KeyConditionExpression=Key('MonthYear').eq(previous_month_year)
                    )
                    previous_month_data = previous_response['Items']
                    
                    # Calculamos la temperatura máxima del mes anterior (si existen datos)
                    max_temperature_previous = max(
                        Decimal(item['Media']) for item in previous_month_data
                    ) if previous_month_data else None

                    # Calculamos la diferencia de temperatura entre el mes actual y el anterior
                    temperature_difference = (
                        max_temperature - max_temperature_previous
                        if max_temperature_previous is not None
                        else None
                    )

                    # Construimos el ítem para la tabla `Metrics`
                    metrics_item = {
                        'MonthYear': month_year,
                        'AverageMedia': round(average_media, 2),  # Promedio de las medias
                        'MaxDeviation': round(max_deviation, 2),  # Máxima desviación
                        'TemperatureDifference': round(temperature_difference, 2) if temperature_difference is not None else None,  # Diferencia de temperatura
                    }

                    # Insertamos el ítem en la tabla `Metrics`
                    batch.put_item(Item=metrics_item)
                    print(f'Datos mensuales actualizados en Metrics: {metrics_item}')

        except Exception as e:
            # Registramos el error si ocurre algún problema durante el procesamiento
            print(e)
            print("Error al procesar el evento del trigger de DynamoDB.")
            raise e
