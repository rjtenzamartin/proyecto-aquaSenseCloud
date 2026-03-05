from flask import Flask, request, jsonify
import boto3
from boto3.dynamodb.conditions import Key
import os
from ec2_metadata import ec2_metadata 

app = Flask(__name__)

# Configurar DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table_name = 'Metricas'
table = dynamodb.Table(table_name)
instanceid = ec2_metadata.instance_id

@app.route('/maxdiff', methods=['GET'])
def maxdiff():
    # Leemos parámetros de la solicitud
    month = request.args.get('month')
    year = request.args.get('year')
    
    if not month or not year:
        return jsonify({'error': 'Parámetros month y year son obligatorios'}), 400
    
    
    year_month = f"{year}-{int(month):02d}"  # Cambiado a MM-YYYY
    
    # Consultmos DynamoDB para obtener los datos del mes y año
    response = table.query(
        KeyConditionExpression=Key('MonthYear').eq(year_month)
    )
    
    # Obtenemos los items y entre ellos el correspondiente a la diferencia de temperatura
    items = response.get('Items', [])
    if not items:
        return jsonify({'error': 'No se encontraron datos para el mes y año especificados'}), 404
    
    temperature_difference = items[0].get('TemperatureDifference')
    if temperature_difference is None:
        return jsonify({'error': 'El atributo TemperatureDifference no se encontró en los datos'}), 500
    
    return jsonify({'year': year, 'month': month, 'maxdiff': temperature_difference, 'instancia':instanceid})

@app.route('/sd', methods=['GET'])
def sd():
    # Leemos parámetros de la solicitud
    month = request.args.get('month')
    year = request.args.get('year')
    
    if not month or not year:
        return jsonify({'error': 'Parámetros month y year son obligatorios'}), 400
    
    
    year_month = f"{year}-{int(month):02d}"
    
    # Consultamos DynamoDB para obtener los datos del mes y año
    response = table.query(
        KeyConditionExpression=Key('MonthYear').eq(year_month)
    )
    
    # Obtenemos los items y entre ellos el correspondiente a la máxima desviación
    items = response.get('Items', [])
    if not items:
        return jsonify({'error': 'No se encontraron datos para el mes y año especificados'}), 404
    
    desviacion = items[0].get('MaxDeviation')
    if desviacion is None:
        return jsonify({'error': 'El atributo MaxDeviation no se encontró en los datos'}), 500
    
    return jsonify({'year': year, 'month': month, 'max_sd': desviacion, 'instancia':instanceid})

@app.route('/temp', methods=['GET'])
def temp():
    # Leemos parámetros de la solicitud
    month = request.args.get('month')
    year = request.args.get('year')
    
    if not month or not year:
        return jsonify({'error': 'Parámetros month y year son obligatorios'}), 400
    
    
    year_month = f"{year}-{int(month):02d}"
    
    # Consultamos DynamoDB para obtener los datos del mes y año
    response = table.query(
        KeyConditionExpression=Key('MonthYear').eq(year_month)
    )
    
    # Obtenemos los items y entre ellos el correspondiente a la media de temperatura
    items = response.get('Items', [])
    if not items:
        return jsonify({'error': 'No se encontraron datos para el mes y año especificados'}), 404
    
    media = items[0].get('AverageTemperature')
    if media is None:
        return jsonify({'error': 'El atributo AverageTemperature no se encontró en los datos'}), 500
    
    return jsonify({'year': year, 'month': month, 'avg_temp': media, 'instancia':instanceid})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000)) 
    app.run(debug=True, host='0.0.0.0', port=port)
