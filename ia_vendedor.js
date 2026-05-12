const axios = require('axios');

// El Prompt que definimos: La personalidad de Alex
const SYSTEM_PROMPT = `Actúa como Alex, cerrador experto de Alianza Indetenible. 
Misión: Vender 'Inglés de por Vida' ($47). 
Tono: Amigo experto, mensajes cortos, usa emojis. 
Protocolo: Empatía -> Detectar dolor -> Escasez -> Cierre.`;

async function obtenerRespuestaVendedor(mensajeUsuario, historialAnterior = []) {
    try {
        // Usamos la API de Google Gemini (Gratuita y potente para empezar)
        const API_KEY = process.env.GEMINI_API_KEY;
        const url = `https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=${API_KEY}`;

        // Construimos el contexto para que Alex no olvide nada
        const contents = [
            { role: "user", parts: [{ text: SYSTEM_PROMPT }] }, // Instrucción maestra
            ...historialAnterior, // Lo que ya se han dicho
            { role: "user", parts: [{ text: mensajeUsuario }] } // El mensaje nuevo
        ];

        const response = await axios.post(url, { contents });
        
        // Retornamos solo el texto de la respuesta humana
        return response.data.candidates[0].content.parts[0].text;
    } catch (error) {
        console.error("Error en Alex-IA:", error.response?.data || error.message);
        return "¡Hola! Dame un segundito que estoy atendiendo a otro alumno y ya te respondo bien. 😉"; // Fallback elegante
    }
}

module.exports = { obtenerRespuestaVendedor };

