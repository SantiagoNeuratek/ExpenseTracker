import http from 'k6/http';
import { sleep, check } from 'k6';

// Configuración de la prueba
export const options = {
    stages: [
        { duration: '30s', target: 20 }, // Ramp-up a 20 usuarios en 30 segundos
        { duration: '1m', target: 20 },  // Mantener 20 usuarios durante 1 minuto
        { duration: '30s', target: 0 },  // Ramp-down a 0 usuarios en 30 segundos
    ],
    thresholds: {
        'http_req_duration': ['p(95)<300'], // 95% de las peticiones deben responder en menos de 300ms
        'http_req_failed': ['rate<0.01'],    // Menos del 1% de fallos
    },
};

// Variables globales
const BASE_URL = 'http://localhost:8000';
let apiKey = '';
let authToken = '';

// Función de setup - se ejecuta una vez al inicio de la prueba
export function setup() {
    // Login para obtener token
    const loginRes = http.post(`${BASE_URL}/api/v1/auth/login`, {
        username: 'usuario@ort.com',
        password: 'Password1',
    });

    check(loginRes, {
        'login successful': (r) => r.status === 200,
    });

    authToken = JSON.parse(loginRes.body).access_token;

    // Crear API key
    const apiKeyRes = http.post(
        `${BASE_URL}/api/v1/apikeys`,
        JSON.stringify({ name: 'k6 test key' }),
        {
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`,
            },
        }
    );

    check(apiKeyRes, {
        'API key created': (r) => r.status === 200,
    });

    apiKey = JSON.parse(apiKeyRes.body).key;

    return { authToken, apiKey };
}

// Función principal
export default function (data) {
    const authToken = data.authToken;
    const apiKey = data.apiKey;

    // Test del endpoint de top categorías
    const topCategoriesRes = http.get(
        `${BASE_URL}/api/v1/expenses/top-categories`,
        {
            headers: {
                'X-API-Key': apiKey,
            },
        }
    );

    check(topCategoriesRes, {
        'top categories status is 200': (r) => r.status === 200,
        'top categories response time < 300ms': (r) => r.timings.duration < 300,
    });

    // Test del endpoint de gastos por categoría
    const today = new Date();
    const oneMonthAgo = new Date();
    oneMonthAgo.setMonth(oneMonthAgo.getMonth() - 1);

    const expensesByCategoryRes = http.get(
        `${BASE_URL}/api/v1/expenses/by-category?category_id=1&start_date=${oneMonthAgo.toISOString().split('T')[0]}&end_date=${today.toISOString().split('T')[0]}`,
        {
            headers: {
                'X-API-Key': apiKey,
            },
        }
    );

    check(expensesByCategoryRes, {
        'expenses by category status is 200': (r) => r.status === 200,
        'expenses by category response time < 300ms': (r) => r.timings.duration < 300,
    });

    // Añadir algo de tiempo de espera entre peticiones
    sleep(1);
}

// Función de teardown - se ejecuta una vez al final de la prueba
export function teardown(data) {
    // Eliminar la API key creada para la prueba
    http.delete(
        `${BASE_URL}/api/v1/apikeys/1`,
        null,
        {
            headers: {
                'Authorization': `Bearer ${data.authToken}`,
            },
        }
    );
}