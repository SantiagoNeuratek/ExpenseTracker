import http from 'k6/http';
import { check } from 'k6';

// URL base
const BASE_URL = 'http://localhost:8000';

// Opciones básicas
export const options = {
    vus: 1,
    iterations: 1,
    thresholds: {
        'checks': ['rate==1.0'],
    },
};

// Función principal
export default function() {
    console.log('Verificando credenciales de autenticación...');
    
    // Crear un objeto FormData para enviar como x-www-form-urlencoded
    const formData = {
        username: 'usuario@ort.com',
        password: 'Password1',
    };
    
    const loginRes = http.post(
        `${BASE_URL}/api/v1/auth/login`,
        formData, // k6 automáticamente lo codifica como form-urlencoded
        {
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
        }
    );

    // Verificar que la autenticación fue exitosa
    const success = check(loginRes, {
        'login successful': (r) => r.status === 200,
        'token received': (r) => JSON.parse(r.body).access_token !== undefined,
    });

    if (success) {
        console.log('✅ Autenticación exitosa: las credenciales son correctas');
        console.log('✅ La estructura de la solicitud es correcta');
        console.log('✅ Token recibido: ' + JSON.parse(loginRes.body).access_token.substring(0, 20) + '...');
    } else {
        console.log('❌ Error en la autenticación');
        console.log('Código de respuesta:', loginRes.status);
        console.log('Respuesta del servidor:', loginRes.body);
    }
} 