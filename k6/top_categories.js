import http from 'k6/http';
import { sleep, check, group } from 'k6';
import { Counter, Trend } from 'k6/metrics';
import { randomIntBetween } from 'https://jslib.k6.io/k6-utils/1.2.0/index.js';

// Métricas personalizadas
const RequestsPerSecond = new Counter('requests_per_second');
const ResponseTime = new Trend('response_time_ms');

export const options = {
  stages: [
    { duration: '30s', target: 5 },    // Ramp-up a 5 usuarios
    { duration: '1m', target: 10 },    // Ramp-up a 10 usuarios (aprox. 600 RPM)
    { duration: '2m', target: 20 },    // Ramp-up a 20 usuarios (aprox. 1200 RPM)
    { duration: '1m', target: 10 },    // Ramp-down a 10 usuarios
    { duration: '30s', target: 0 },    // Ramp-down a 0 usuarios
  ],
  thresholds: {
    'http_req_duration': ['p(95)<300'], // 95% de las solicitudes deben completarse en menos de 300ms
    'http_req_failed': ['rate<0.01'],   // Menos del 1% de las solicitudes pueden fallar
  },
};

// Variables globales
const BASE_URL = 'http://localhost:8000/api/v1';
let apiKey = '';
let accessToken = '';

// Función de configuración - se ejecuta una vez al inicio de la prueba
export function setup() {
  console.log('Inicializando prueba de top-categories');
  
  // Login para obtener token
  const loginPayload = JSON.stringify({
    username: 'admin@example.com',
    password: 'admin',
  });
  
  const loginParams = {
    headers: {
      'Content-Type': 'application/json',
    },
  };
  
  const loginResponse = http.post(`${BASE_URL}/auth/login`, loginPayload, loginParams);
  
  if (!check(loginResponse, { 'Login exitoso': (r) => r.status === 200 })) {
    console.error('Error en login:', loginResponse.body);
    return;
  }
  
  accessToken = JSON.parse(loginResponse.body).access_token;
  
  // Crear API key para pruebas
  const apiKeyPayload = JSON.stringify({
    name: `k6_test_key_${Date.now()}`,
    scopes: ["expenses:read"],
  });
  
  const apiKeyParams = {
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${accessToken}`,
    },
  };
  
  const apiKeyResponse = http.post(`${BASE_URL}/apikeys/`, apiKeyPayload, apiKeyParams);
  
  if (!check(apiKeyResponse, { 'API key creada': (r) => r.status === 201 })) {
    console.error('Error al crear API key:', apiKeyResponse.body);
    return;
  }
  
  apiKey = JSON.parse(apiKeyResponse.body).api_key;
  
  return { apiKey, accessToken };
}

// Función principal de prueba
export default function(data) {
  const { apiKey, accessToken } = data;
  
  // Parámetros para probar el endpoint
  const startDate = '2023-01-01';
  const endDate = '2023-12-31';
  
  // Probar endpoint con JWT (Token de acceso)
  group('Probar top-categories con JWT', function() {
    const params = {
      headers: {
        'Authorization': `Bearer ${accessToken}`,
      },
    };
    
    const url = `${BASE_URL}/expenses/top-categories?start_date=${startDate}&end_date=${endDate}`;
    const startTime = new Date();
    const response = http.get(url, params);
    const endTime = new Date();
    const duration = endTime - startTime;
    
    // Registrar métricas personalizadas
    RequestsPerSecond.add(1);
    ResponseTime.add(duration);
    
    check(response, {
      'Status 200': (r) => r.status === 200,
      'Respuesta en formato JSON': (r) => r.headers['Content-Type'] && r.headers['Content-Type'].includes('application/json'),
      'Contiene datos de categorías': (r) => {
        const body = JSON.parse(r.body);
        return Array.isArray(body);
      },
    });
  });
  
  // Probar endpoint con API Key
  group('Probar top-categories con API Key', function() {
    const params = {
      headers: {
        'X-api-key': apiKey,
      },
    };
    
    const url = `${BASE_URL}/expenses/top-categories?start_date=${startDate}&end_date=${endDate}`;
    const startTime = new Date();
    const response = http.get(url, params);
    const endTime = new Date();
    const duration = endTime - startTime;
    
    // Registrar métricas personalizadas
    RequestsPerSecond.add(1);
    ResponseTime.add(duration);
    
    check(response, {
      'Status 200': (r) => r.status === 200,
      'Respuesta en formato JSON': (r) => r.headers['Content-Type'] && r.headers['Content-Type'].includes('application/json'),
      'Contiene datos de categorías': (r) => {
        const body = JSON.parse(r.body);
        return Array.isArray(body);
      },
    });
  });
  
  // Esperar entre 1 y 3 segundos entre cada iteración
  sleep(randomIntBetween(1, 3));
}

// Función de limpieza - se ejecuta una vez al finalizar la prueba
export function teardown(data) {
  console.log('Finalizando prueba de top-categories');
  
  if (apiKey) {
    const apiKeyName = apiKey.split('_')[0]; // Obtener el nombre de la API key
    
    // Buscar la API key por su nombre para obtener su ID
    const listParams = {
      headers: {
        'Authorization': `Bearer ${accessToken}`,
      },
    };
    
    const listResponse = http.get(`${BASE_URL}/apikeys/`, listParams);
    
    if (check(listResponse, { 'Lista de API keys obtenida': (r) => r.status === 200 })) {
      const apiKeys = JSON.parse(listResponse.body);
      const targetKey = apiKeys.find(k => k.name.includes('k6_test_key'));
      
      if (targetKey) {
        // Eliminar la API key
        const deleteParams = {
          headers: {
            'Authorization': `Bearer ${accessToken}`,
          },
        };
        
        const deleteResponse = http.del(`${BASE_URL}/apikeys/${targetKey.id}`, null, deleteParams);
        check(deleteResponse, { 'API key eliminada': (r) => r.status === 200 });
      }
    }
  }
} 