#!/usr/bin/env bash
# Reconocimiento pasivo/activo sobre un dominio.
# Uso: ./recon.sh ejemplo.com [directorio-salida]
set -euo pipefail

DOMAIN="${1:-}"
OUT="${2:-resultados/$DOMAIN-$(date +%Y%m%d-%H%M%S)}"

if [ -z "$DOMAIN" ]; then
    echo "Uso: $0 <dominio> [directorio-salida]" >&2
    exit 1
fi

export PATH="$PATH:$(go env GOPATH 2>/dev/null)/bin"
mkdir -p "$OUT"

step() { printf '\n\033[1;34m== %s\033[0m\n' "$*"; }
have() { command -v "$1" >/dev/null; }

step "WHOIS"
have whois && whois "$DOMAIN" | tee "$OUT/whois.txt" >/dev/null || echo "whois no disponible"

step "Registros DNS"
if have dig; then
    for r in A AAAA MX NS TXT SOA CAA; do
        echo "--- $r"
        dig +short "$DOMAIN" "$r"
    done | tee "$OUT/dns.txt"
fi

step "Subdominios (subfinder)"
if have subfinder; then
    subfinder -silent -d "$DOMAIN" -o "$OUT/subdominios.txt"
    echo "$(wc -l < "$OUT/subdominios.txt") subdominios encontrados"
else
    echo "subfinder no instalado; ejecuta ./install.sh"
fi

step "Hosts vivos (httpx)"
if have httpx && [ -s "$OUT/subdominios.txt" ]; then
    httpx -silent -l "$OUT/subdominios.txt" \
        -status-code -title -tech-detect \
        -o "$OUT/hosts-vivos.txt"
    cat "$OUT/hosts-vivos.txt"
fi

step "Emails y hosts (theHarvester)"
if have theHarvester; then
    theHarvester -d "$DOMAIN" -b duckduckgo,crtsh,bing -f "$OUT/harvester" \
        > "$OUT/harvester.log" 2>&1 || echo "theHarvester terminó con errores, mira harvester.log"
fi

step "Typosquatting (dnstwist)"
have dnstwist && dnstwist --registered --format csv "$DOMAIN" > "$OUT/typosquatting.csv" 2>/dev/null || true

printf '\n\033[1;32mListo.\033[0m Resultados en: %s\n' "$OUT"
