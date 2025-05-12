#!/bin/bash

echo "🔵 Deteniendo contenedores antiguos (si los hubiera)..."
docker-compose down

echo "🛠️  Construyendo y levantando contenedores..."
docker-compose up --build -d

echo ""
echo "✅ Contenedores levantados:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "🌟 ¡Todo listo! Puedes acceder a los servicios en sus respectivos puertos."