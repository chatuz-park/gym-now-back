from django.core.management.base import BaseCommand
from django.test import RequestFactory
from django.urls import reverse
import requests
import json
import os

class Command(BaseCommand):
    help = 'Actualizar el archivo swagger.json con la documentación más reciente de la API'

    def add_arguments(self, parser):
        parser.add_argument(
            '--host',
            type=str,
            default='localhost:8000',
            help='Host y puerto del servidor Django (default: localhost:8000)'
        )
        parser.add_argument(
            '--protocol',
            type=str,
            default='http',
            help='Protocolo a usar (default: http)'
        )
        parser.add_argument(
            '--output',
            type=str,
            default='swagger.json',
            help='Archivo de salida (default: swagger.json)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forzar la actualización incluso si el servidor no está ejecutándose'
        )

    def handle(self, *args, **options):
        host = options['host']
        protocol = options['protocol']
        output_file = options['output']
        force = options['force']

        self.stdout.write('🔄 Actualizando documentación Swagger...')

        # URL del endpoint de Swagger
        swagger_url = f"{protocol}://{host}/swagger/?format=openapi"

        try:
            # Intentar obtener la documentación Swagger
            self.stdout.write(f'📡 Conectando a {swagger_url}...')
            
            response = requests.get(swagger_url, timeout=10)
            response.raise_for_status()

            # Parsear el JSON
            swagger_data = response.json()

            # Actualizar la información del host en el JSON
            swagger_data['host'] = host
            swagger_data['schemes'] = [protocol]

            # Guardar el archivo
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(swagger_data, f, indent=2, ensure_ascii=False)

            # Estadísticas
            paths_count = len(swagger_data.get('paths', {}))
            definitions_count = len(swagger_data.get('definitions', {}))
            file_size = os.path.getsize(output_file)

            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Swagger actualizado exitosamente!\n'
                    f'📁 Archivo: {output_file}\n'
                    f'📊 Endpoints: {paths_count}\n'
                    f'📋 Definiciones: {definitions_count}\n'
                    f'💾 Tamaño: {file_size:,} bytes'
                )
            )

            # Mostrar algunos endpoints como ejemplo
            self.stdout.write('\n🔗 Endpoints disponibles:')
            paths = list(swagger_data.get('paths', {}).keys())
            for path in paths[:10]:
                self.stdout.write(f'   {path}')
            
            if len(paths) > 10:
                remaining = len(paths) - 10
                self.stdout.write(f'   ... y {remaining} más')

        except requests.exceptions.ConnectionError:
            if force:
                self.stdout.write(
                    self.style.WARNING(
                        '⚠️  No se pudo conectar al servidor, pero continuando con --force...'
                    )
                )
                self.create_empty_swagger(output_file, host, protocol)
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f'❌ Error: No se pudo conectar a {swagger_url}\n'
                        f'💡 Asegúrate de que el servidor Django esté ejecutándose:\n'
                        f'   pipenv run python manage.py runserver\n\n'
                        f'🔧 O usa --force para crear un archivo vacío'
                    )
                )
        except requests.exceptions.Timeout:
            self.stdout.write(
                self.style.ERROR(
                    '❌ Error: Timeout al conectar con el servidor'
                )
            )
        except requests.exceptions.HTTPError as e:
            self.stdout.write(
                self.style.ERROR(
                    f'❌ Error HTTP: {e.response.status_code} - {e.response.reason}'
                )
            )
        except json.JSONDecodeError:
            self.stdout.write(
                self.style.ERROR(
                    '❌ Error: La respuesta no es un JSON válido'
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f'❌ Error inesperado: {str(e)}'
                )
            )

    def create_empty_swagger(self, output_file, host, protocol):
        """Crear un archivo Swagger vacío con la estructura básica"""
        empty_swagger = {
            "swagger": "2.0",
            "info": {
                "title": "GymNow API",
                "description": "API para gestión de gimnasio con clientes, ejercicios, rutinas y seguimiento de progreso",
                "version": "v1",
                "contact": {
                    "email": "contact@gymnow.com"
                },
                "license": {
                    "name": "BSD License"
                }
            },
            "host": host,
            "schemes": [protocol],
            "basePath": "/api",
            "consumes": ["application/json"],
            "produces": ["application/json"],
            "paths": {},
            "definitions": {}
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(empty_swagger, f, indent=2, ensure_ascii=False)

        self.stdout.write(
            self.style.WARNING(
                f'⚠️  Archivo Swagger vacío creado: {output_file}\n'
                f'💡 Ejecuta el servidor y vuelve a ejecutar este comando para obtener la documentación completa'
            )
        ) 