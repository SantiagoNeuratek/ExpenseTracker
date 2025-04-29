import http from 'k6/http';
import { sleep, check, group } from 'k6';
import { Counter, Trend } from 'k6/metrics';
import { htmlReport } from "https://raw.githubusercontent.com/benc-uk/k6-reporter/main/dist/bundle.js";
import { textSummary } from "https://jslib.k6.io/k6-summary/0.0.1/index.js";

// Métricas personalizadas
const topCategoriesRPS = new Counter('top_categories_rps');
const topCategoriesHistoryRPS = new Counter('top_categories_history_rps');
const categoriesExpensesRPS = new Counter('categories_expenses_rps');
const topCategoriesResponseTime = new Trend('top_categories_response_time');
const topCategoriesHistoryResponseTime = new Trend('top_categories_history_response_time');
const categoriesExpensesResponseTime = new Trend('categories_expenses_response_time');

// Contador para errores
const errors = new Counter('errors');

// Configuración de la prueba
export const options = {
    scenarios: {
        average_load: {
            executor: 'ramping-vus',
            startVUs: 1,
            stages: [
                { duration: '30s', target: 5 },   // Ramp-up a 5 VUs
                { duration: '30s', target: 10 },  // Incremento a 10 VUs
                { duration: '30s', target: 20 },  // Incremento a 20 VUs 
                { duration: '2m', target: 20 },   // Mantener 20 VUs (1200 req/min)
                { duration: '30s', target: 0 },   // Ramp-down
            ],
            gracefulRampDown: '30s',
        },
    },
    thresholds: {
        'http_req_duration{endpoint:top-categories-history}': ['p(95)<300'],  // RF8
        'http_req_duration{endpoint:by-category}': ['p(95)<300'],            // RF9
        'http_req_failed': ['rate<0.01'],    // Menos del 1% de errores
    },
    userAgent: 'K6LoadTest/1.0',
};

// Variables globales
const BASE_URL = 'http://localhost:8000';
let authToken = '';
let apiKey = '';
let companyId = 1; // Empresa ORT
let apiKeyId = null;
let categories = [];

// Función de setup - se ejecuta una vez al inicio de la prueba
export function setup() {
    console.log('Iniciando setup: login y creación de API key');
    
    // Login como usuario regular en lugar de admin (tiene company_id asignado)
    const formData = {
        username: 'usuario@ort.com',
        password: 'Password1',
    };
    
    const loginRes = http.post(
        `${BASE_URL}/api/v1/auth/login`,
        formData,  // k6 automáticamente lo codifica como form-urlencoded
        {
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
        }
    );

    check(loginRes, {
        'login successful': (r) => r.status === 200,
    });

    if (loginRes.status !== 200) {
        console.error('Error en login:', loginRes.body);
        throw new Error('Falló login');
    }

    authToken = JSON.parse(loginRes.body).access_token;
    console.log('Login exitoso, token obtenido');

    // Crear API Key
    const createApiKeyRes = http.post(
        `${BASE_URL}/api/v1/apikeys`,
        JSON.stringify({
            name: 'k6 test key'
        }),
        {
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            }
        }
    );

    check(createApiKeyRes, {
        'API Key creation status is 200': (r) => r.status === 200,
        'API Key response has key': (r) => {
            try {
                const data = JSON.parse(r.body);
                return data.key && data.key.length > 0;
            } catch (e) {
                console.error('Error parsing API key response:', e);
                return false;
            }
        }
    });

    if (createApiKeyRes.status !== 200) {
        console.error('Error creating API key:', createApiKeyRes.body);
        throw new Error('Failed to create API key');
    }

    // Extraer la API key del response
    const apiKeyData = JSON.parse(createApiKeyRes.body);
    apiKey = apiKeyData.key;

    // Verificar que tenemos una API key válida
    if (!apiKey) {
        console.error('No API key received in response');
        throw new Error('No API key received');
    }

    console.log('API key created successfully');

    // Obtener lista de categorías para probar el endpoint RF9
    const categoriesRes = http.get(
        `${BASE_URL}/api/v1/categories`,
        {
            headers: {
                'Authorization': `Bearer ${authToken}`,
            },
        }
    );

    if (categoriesRes.status === 200) {
        categories = JSON.parse(categoriesRes.body);
        console.log(`Obtenidas ${categories.length} categorías para pruebas`);
    } else {
        console.error('Error obteniendo categorías:', categoriesRes.body);
    }

    return { authToken, apiKey, companyId, categories };
}

// Función principal
export default function (data) {
    const authToken = data.authToken;
    const apiKey = data.apiKey;
    const companyId = data.companyId;
    const categories = data.categories;

    // Formato para fechas
    const today = new Date();
    const oneMonthAgo = new Date();
    oneMonthAgo.setMonth(oneMonthAgo.getMonth() - 1);
    const startDate = oneMonthAgo.toISOString().split('T')[0];
    const endDate = today.toISOString().split('T')[0];

    // Aún incluyo este endpoint para mantener compatibilidad con pruebas anteriores
    group('Top Categories by Date Range', function () {
        const startTime = new Date().getTime();
        const topCategoriesRes = http.get(
            `${BASE_URL}/api/v1/expenses/top-categories?start_date=${startDate}&end_date=${endDate}`,
            {
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                },
                tags: { name: 'top-categories' },
            }
        );
        const duration = new Date().getTime() - startTime;

        // Registrar métricas personalizadas
        topCategoriesRPS.add(1);
        topCategoriesResponseTime.add(duration);

        check(topCategoriesRes, {
            'top categories status is 200': (r) => r.status === 200,
            'top categories response time < 300ms': (r) => r.timings.duration < 300,
        });
    });

    group('RF8: Top 3 Categories History', function () {
        // Prueba de rendimiento del endpoint de top 3 categorías históricas (RF8)
        const startTime = new Date().getTime();
        const topCategoriesHistoryRes = http.get(
            `${BASE_URL}/api/v1/expenses/top-categories-history?start_date=${startDate}&end_date=${endDate}`,
            {
                headers: {
                    'API-Key': apiKey,
                    'Content-Type': 'application/json'
                },
                tags: { endpoint: 'top-categories-history' },
            }
        );
        const duration = new Date().getTime() - startTime;

        // Registrar métricas personalizadas
        topCategoriesHistoryRPS.add(1);
        topCategoriesHistoryResponseTime.add(duration);

        check(topCategoriesHistoryRes, {
            'top categories history status is 200': (r) => r.status === 200,
            'top categories history response time < 300ms': (r) => r.timings.duration < 300,
            'returns array with 3 categories': (r) => {
                try {
                    const data = JSON.parse(r.body);
                    return Array.isArray(data) && data.length <= 3;
                } catch (e) {
                    console.error('Error parsing response:', e);
                    return false;
                }
            }
        });
    });

    group('RF9: Expenses by Category', function () {
        // Seleccionar una categoría aleatoria para distribuir la carga
        if (!categories || categories.length === 0) {
            console.error('No hay categorías disponibles para probar RF9');
            return;
        }
        
        const randomIndex = Math.floor(Math.random() * categories.length);
        const categoryId = categories[randomIndex].id;
        
        // Prueba de rendimiento del endpoint de gastos por categoría (RF9) con API Key
        const startTime = new Date().getTime();
        const expensesByCategoryRes = http.get(
            `${BASE_URL}/api/v1/expenses/by-category?category_id=${categoryId}&start_date=${startDate}&end_date=${endDate}`,
            {
                headers: {
                    'API-Key': apiKey,
                    'Content-Type': 'application/json'
                },
                tags: { endpoint: 'by-category' },
            }
        );
        const duration = new Date().getTime() - startTime;

        // Registrar métricas personalizadas
        categoriesExpensesRPS.add(1);
        categoriesExpensesResponseTime.add(duration);

        check(expensesByCategoryRes, {
            'expenses by category status is 200': (r) => r.status === 200,
            'expenses by category response time < 300ms': (r) => r.timings.duration < 300,
        });
    });

    // Tiempo de espera para ajustar la tasa de solicitudes
    // Con 20 usuarios y 1s de espera, alcanzamos aproximadamente 20 RPS = 1200 RPM
    sleep(1);
}

// Función de teardown - se ejecuta una vez al final de la prueba
export function teardown(data) {
    console.log('Ejecutando teardown: limpieza de API keys de prueba');
    
    // Obtener todas las API keys
    const getApiKeysRes = http.get(
        `${BASE_URL}/api/v1/apikeys`,
        {
            headers: {
                'Authorization': `Bearer ${data.authToken}`,
            },
        }
    );
    
    if (getApiKeysRes.status === 200) {
        const apiKeys = JSON.parse(getApiKeysRes.body);
        
        // Eliminar las API keys con nombre 'k6 test key'
        for (const key of apiKeys) {
            if (key.name === 'k6 test key') {
                console.log(`Eliminando API key: ${key.id}`);
                http.del(
                    `${BASE_URL}/api/v1/apikeys/${key.id}`,
                    null,
                    {
                        headers: {
                            'Authorization': `Bearer ${data.authToken}`,
                        },
                    }
                );
            }
        }
    } else {
        console.error('Error obteniendo API keys para limpieza:', getApiKeysRes.body);
    }
    
    console.log('Teardown completado');
}

export function handleSummary(data) {
    return {
        "k6/summary.html": htmlReport(data),
        stdout: textSummary(data, { indent: " ", enableColors: true }),
    };
}