# Expensia - Frontend React

Este proyecto es una reimplementación del frontend de la aplicación Expensia (Expense Tracker) utilizando React, TypeScript y Chakra UI.

## Características

- Autenticación de usuarios
- Dashboard con gráficos interactivos
- Gestión de categorías
- Gestión de gastos
- Administración de usuarios
- Administración de API Keys

## Requisitos

- Node.js 16.x o superior
- npm 8.x o superior

## Instalación

1. Clona el repositorio:
   ```
   git clone <url-del-repositorio>
   cd frontend-react
   ```

2. Instala las dependencias:
   ```
   npm install
   ```

3. Copia el archivo de variables de entorno y edítalo según tu configuración:
   ```
   cp .env.example .env
   ```

## Desarrollo

Para iniciar el servidor de desarrollo:

```
npm run dev
```

La aplicación estará disponible en `http://localhost:5173`

## Construcción para producción

Para compilar el proyecto para producción:

```
npm run build
```

Los archivos generados se ubicarán en el directorio `dist`.

## Tecnologías utilizadas

- React 18
- TypeScript
- Vite
- Chakra UI
- React Router v6
- Axios
- Recharts (gráficos)
- React Icons

## Estructura del proyecto

```
src/
├── assets/        # Imágenes, iconos y otros recursos estáticos
├── components/    # Componentes reutilizables
├── context/       # Contextos de React (Auth, Notificaciones)
├── hooks/         # Hooks personalizados
├── pages/         # Componentes de página
├── services/      # Servicios para comunicación con API
├── styles/        # Estilos globales y temas
├── types/         # Definiciones de tipos TypeScript
└── utils/         # Utilidades y funciones auxiliares
```

## Endpoints API

Este frontend se comunica con una API RESTful que debe estar disponible en la URL especificada en el archivo `.env` como `VITE_API_URL`.

## Licencia

Este proyecto está licenciado bajo la licencia MIT. Consulta el archivo LICENSE para más detalles.
