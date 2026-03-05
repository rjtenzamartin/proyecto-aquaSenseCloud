# Proyecto AquaSenseCloud ☁️💧

**AquaSenseCloud** es una infraestructura en la nube diseñada para la Computación de Altas Prestaciones, enfocada en el procesamiento automático, almacenamiento y exposición de datos climáticos y métricas de temperatura del agua.

Este proyecto implementa una arquitectura Serverless y de microservicios en AWS, automatizando desde la ingesta de archivos CSV hasta la notificación de anomalías y la consulta de datos mediante una API RESTful. Fue desarrollado por Rubén José Tenza Martín y Fernando Piñera Hervas.

## 🏗️ Arquitectura del Sistema

El flujo de trabajo del proyecto se divide en tres bloques principales:

### 1. Ingesta y Almacenamiento de Datos (Storage & Database)

* 
**Amazon S3:** Se utiliza un bucket (e.g., `bucket-proyecto-icap-grupo`) como punto de entrada para los archivos de datos crudos en formato `.csv`.


* **Amazon DynamoDB:** Actúa como la base de datos principal NoSQL, dividida en dos tablas:
* `Datos-Crudos`: Almacena los datos iniciales procesados. Utiliza `Fecha` como clave de partición y cuenta con un índice secundario global (`MonthYear-index`) para optimizar las consultas .


* 
`Metrics`: Almacena métricas agregadas mensualmente (Promedio de media, Desviación Máxima, etc.) utilizando `MonthYear` como clave principal .





### 2. Procesamiento Automatizado y Alertas (Serverless Compute)

Se emplean funciones **AWS Lambda** impulsadas por eventos (Event-Driven) para procesar la información de forma asíncrona:

* `funcion-datos`: Se activa automáticamente al subir un archivo `.csv` al bucket S3. Descarga el archivo, transforma los campos y carga los registros en la tabla `Datos-Crudos` .


* `funcion-metricas`: Se dispara mediante flujos de DynamoDB (Streams) cuando hay nuevos registros en `Datos-Crudos`. Calcula métricas mensuales y las guarda en la tabla `Metrics` .


* `funcion-sns` (o `funcion-notificacion`): Monitoriza los datos en tiempo real mediante DynamoDB Streams. Si detecta una desviación de temperatura que supera el umbral de `0.5`, genera una alerta .


* 
**Amazon SNS:** El tema `TemperatureAlert` recibe las notificaciones de la función Lambda y envía correos electrónicos automatizados a los administradores del sistema .



### 3. Servicio Web y Despliegue (API & Networking)

Para exponer los datos procesados, se implementó un servicio web contenedorizado:

* 
**Flask & Docker:** Una aplicación en Python (Flask) expone una API RESTful con endpoints como `/maxdiff`, `/sd`, y `/temp` para consultar las métricas de meses y años específicos directamente desde DynamoDB. La aplicación está empaquetada en una imagen Docker.


* 
**Amazon EC2:** El contenedor se ejecuta en una instancia EC2 (`t2.micro`) con un volumen EBS de 100 GB para almacenamiento persistente.


* 
**VPC & Security:** La instancia reside dentro de una red virtual privada (VPC) con subredes públicas, un Internet Gateway y Grupos de Seguridad (Security Groups) que restringen el tráfico únicamente a los puertos `22` (SSH) y `5000` (Flask) .



## ⚙️ Infraestructura como Código (IaC)

Para garantizar la escalabilidad, la reproducibilidad y el bajo coste, toda la infraestructura se despliega mediante plantillas de **AWS CloudFormation**. Esto permite levantar tanto la base de datos y las funciones Lambda, como la red virtual y el servidor web de manera completamente automatizada.

## 🚀 Requisitos y Despliegue

Para replicar este entorno, es necesario configurar:

1. Las plantillas de CloudFormation proporcionadas en el directorio del proyecto (`proyecto-iac-servicioweb-tenza-pinera.yaml` y la plantilla de base de datos).


2. Un par de claves SSH (`dockerInstance-keypair`) para el acceso a la instancia EC2.


3. Una suscripción de correo electrónico confirmada en el tema de SNS para recibir las alertas.


4. La construcción y ejecución de la imagen de Docker en la instancia EC2 utilizando los archivos `app_flask.py`, `requirements.txt` y `Dockerfile` .
