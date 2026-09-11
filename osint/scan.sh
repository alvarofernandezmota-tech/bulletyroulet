#!/usr/bin/env bash
# Lanza recon.sh en una maquina remota dentro de tmux y se desconecta.
# Uso: ./scan.sh <host-ssh> <dominio>
set -euo pipefail

HOST="${1:-}"
DOMAIN="${2:-}"

if [ -z "$HOST" ] || [ -z "$DOMAIN" ]; then
    echo "Uso: $0 <host-ssh> <dominio>" >&2
    echo "Ejemplo: $0 madre ejemplo.com" >&2
    exit 1
fi

SESSION="osint-${DOMAIN//./-}"

ssh "$HOST" "command -v tmux >/dev/null" || {
    echo "tmux no esta instalado en $HOST. Instalalo con: ssh $HOST sudo pacman -S tmux" >&2
    exit 1
}

if ssh "$HOST" "tmux has-session -t '$SESSION' 2>/dev/null"; then
    echo "Ya hay un escaneo de $DOMAIN en marcha en $HOST."
else
    ssh "$HOST" "tmux new-session -d -s '$SESSION' 'cd ~/osint-toolkit && ./recon.sh $DOMAIN'"
    echo "Escaneo de $DOMAIN lanzado en $HOST."
fi

cat <<EOF

Ver el progreso:   ssh $HOST -t tmux attach -t $SESSION
Salir sin cortar:  Ctrl+b, luego d
Traer resultados:  rsync -avz $HOST:~/osint-toolkit/resultados/ ~/resultados-osint/
EOF
