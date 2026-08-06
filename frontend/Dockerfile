FROM node:20-alpine

WORKDIR /app

# Copia los archivos de configuración primero para aprovechar la caché de Docker
COPY package*.json ./

# Instala dependencias si package.json existe
RUN if [ -f "package.json" ]; then npm install; fi

# Expone el puerto 3000 de Vite
EXPOSE 3000

# El comando por defecto asegura que las dependencias estén instaladas en caso 
# de que el volumen haya sobreescrito la carpeta y arranca la app Vite.
CMD npm install && npm run dev -- --host 0.0.0.0 --port 3000
