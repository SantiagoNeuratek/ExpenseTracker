# Expense Tracker SaaS

Un sistema de gestión de gastos empresariales desarrollado como parte del Obligatorio de Arquitectura de Software en la Práctica.

## Características

- Registro de empresas cliente
- Gestión de usuarios mediante invitación
- Autenticación y autorización basada en roles
- Gestión de categorías de gastos
- Registro y seguimiento de gastos
- API REST para integración con otros sistemas
- Visualización de datos mediante gráficos
- Multi-tenancy con aislamiento de datos por empresa

## Tecnologías Utilizadas

### Backend
- FastAPI: Framework web de alto rendimiento para Python
- SQLAlchemy: ORM para interactuar con la base de datos
- PostgreSQL: Base de datos relacional
- JWT: Para autenticación y autorización
- Alembic: Para migraciones de base de datos
- Docker: Para contenedorización y despliegue

### Frontend
- Streamlit: Framework para crear aplicaciones web con Python
- Plotly: Librería para visualizaciones interactivas
- Pandas: Para manipulación y análisis de datos

## Arquitectura

El sistema está desarrollado como una aplicación monolítica cloud-native, siguiendo los principios de 12-factor app:

1. **Codebase**: Un repositorio Git para todo el código
2. **Dependencies**: Gestión de dependencias explícita con pyproject.toml y requirements.txt
3. **Config**: Configuración en variables de entorno
4. **Backing services**: Base de datos como recurso adjunto
5. **Build, release, run**: Separación clara de etapas con Docker
6. **Processes**: Procesos stateless
7. **Port binding**: Exposición a través de puertos (8000 para API, 8501 para frontend)
8. **Concurrency**: Escalado horizontal mediante replicación de contenedores
9. **Disposability**: Arranque rápido y cierre elegante
10. **Dev/prod parity**: Entornos de desarrollo y producción similares gracias a Docker
11. **Logs**: Como flujos de eventos
12. **Admin processes**: Herramientas de administración como parte del código

## Estructura del Proyecto

```
expense-tracker-saas/
├── backend/         # API FastAPI
├── frontend/        # Aplicación Streamlit
├── k6/              # Pruebas de carga
└── docker-compose.yml  # Configuración Docker Compose
```

## Requisitos

- Docker y Docker Compose
- Python 3.9+
- PostgreSQL 13+

## Instalación y Ejecución

1. Clonar el repositorio:
```bash
git clone https://github.com/tu-usuario/expense-tracker-saas.git
cd expense-tracker-saas
```

2. Iniciar los servicios con Docker Compose:
```bash
docker-compose up
```

3. Acceder a la aplicación:
   - Backend API: http://localhost:8000
   - Frontend: http://localhost:8501

## Usuarios de Prueba

El sistema se inicializa con dos usuarios de prueba:

- Administrador:
  - Email: admin@saas.com
  - Contraseña: Password1

- Usuario Regular:
  - Email: usuario@ort.com
  - Contraseña: Password1

## Documentación API

La documentación de la API está disponible en:
- http://localhost:8000/api/docs

## Desarrollo

### Backend

Para ejecutar el backend en modo desarrollo:

```bash
cd backend
pip install poetry
poetry install
poetry run uvicorn app.main:app --reload
```

### Frontend

Para ejecutar el frontend en modo desarrollo:

```bash
cd frontend
pip install -r requirements.txt
streamlit run Home.py
```

## Pruebas de Carga

Para ejecutar las pruebas de carga con k6:

```bash
cd k6
k6 run load_tests.js
```

## Licencia

Este proyecto está licenciado bajo la Licencia MIT.