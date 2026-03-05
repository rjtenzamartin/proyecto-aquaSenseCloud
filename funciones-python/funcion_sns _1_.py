import json
import boto3
import os

def lambda_handler(event, context):
    # Registramos el evento recibido por la función Lambda
    print("Evento recibido por la función Lambda:", json.dumps(event, indent=2))

    # Inicializamos el cliente de SNS
    sns = boto3.client('sns')
    sns_topic_arn = 

    # Creamos una lista para acumular las alertas encontradas
    alerts = []

    try:
        # Iteramos sobre los registros recibidos en el evento
        for record in event['Records']:
            # Extraemos la nueva imagen del registro
            new_image = record['dynamodb'].get('NewImage', None)

            # Verificamos si la nueva imagen contiene los campos 'Deviation' y 'Fecha'
            if new_image and 'Deviation' in new_image and 'Fecha' in new_image:
                try:
                    # Convertimos la desviación a tipo float y extraemos la fecha
                    deviation = float(new_image['Deviation']['N'])
                    fecha = new_image['Fecha']['S']

                    # Verificamos si la desviación excede el umbral de 0.5
                    if deviation > 0.5:
                        # Agregamos una alerta a la lista
                        alerts.append(f"Fecha: {fecha}, Desviación: {deviation}")
                
                except ValueError:
                    # Registramos un error si no podemos convertir la desviación a float
                    print("Error: No se pudo convertir el valor de 'Deviation' a float.")
            else:
                # Registramos una advertencia si no se encuentran los campos necesarios
                print("Advertencia: No se encontró 'Deviation' o 'Fecha' en la nueva imagen.")

        # Si encontramos alertas, construimos y enviamos un mensaje consolidado
        if alerts:
            message = (
                "¡Alerta de Temperatura!\n\n"
                "Se han detectado desviaciones semanales que exceden el umbral de 0.5:\n\n"
                + "\n".join(alerts)
            )

            # Registramos el mensaje que vamos a enviar
            print("Enviando alerta consolidada:", message)

            # Publicamos el mensaje en el tópico de SNS
            sns.publish(
                TopicArn=sns_topic_arn,
                Message=message,
                Subject='Resumen de Alertas de Temperatura',
            )

        # Devolvemos una respuesta con el número de registros procesados y alertas encontradas
        return {
            'statusCode': 200,
            'body': f'Se procesaron exitosamente {len(event["Records"])} registros. '
                    f'Se encontraron {len(alerts)} desviaciones que exceden el umbral.'
        }

    except Exception as e:
        # Registramos cualquier error que ocurra durante el procesamiento
        print(f"Error al procesar los registros: {str(e)}")
        return {
            'statusCode': 500,
            'body': f"Error al procesar el evento: {str(e)}"
        }
