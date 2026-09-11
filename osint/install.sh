#!/usr/bin/env bash
# Instalador de herramientas OSINT para Arch Linux.
# Idempotente: se puede relanzar sin romper nada.
set -euo pipefail

info() { printf '\033[1;34m::\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m!!\033[0m %s\n' "$*"; }
ok()   { printf '\033[1;32mok\033[0m %s\n' "$*"; }

if ! command -v pacman >/dev/null; then
    warn "Esto es un instalador para Arch Linux (necesita pacman). Abortando."
    exit 1
fi

PACMAN_PKGS=(python python-pip python-pipx git go jq curl whois bind nmap openssh)
PIPX_PKGS=(sherlock-project holehe theHarvester maigret socialscan dnstwist h8mail)
GO_PKGS=(
    github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
    github.com/projectdiscovery/httpx/cmd/httpx@latest
    github.com/projectdiscovery/dnsx/cmd/dnsx@latest
    github.com/owasp-amass/amass/v4/...@master
)

info "Paquetes del sistema"
sudo pacman -S --needed --noconfirm "${PACMAN_PKGS[@]}"

info "Herramientas Python (pipx)"
pipx ensurepath >/dev/null
for pkg in "${PIPX_PKGS[@]}"; do
    if pipx list --short 2>/dev/null | grep -q "^${pkg} "; then
        ok "$pkg ya instalado"
    else
        pipx install "$pkg" || warn "fallo instalando $pkg (se continúa)"
    fi
done

info "Herramientas Go"
for pkg in "${GO_PKGS[@]}"; do
    go install -v "$pkg" || warn "fallo instalando $pkg (se continúa)"
done

GOBIN="$(go env GOPATH)/bin"
if ! grep -qs "$GOBIN" "$HOME/.bashrc"; then
    echo "export PATH=\$PATH:$GOBIN" >> "$HOME/.bashrc"
    info "Añadido $GOBIN al PATH en ~/.bashrc (abre una terminal nueva)"
fi

info "Comprobación final"
MISSING=0
for t in sherlock holehe theHarvester maigret dnstwist subfinder httpx dnsx amass nmap whois dig; do
    if command -v "$t" >/dev/null || [ -x "$GOBIN/$t" ]; then
        ok "$t"
    else
        warn "FALTA $t"
        MISSING=1
    fi
done

[ "$MISSING" -eq 0 ] && info "Todo listo." || warn "Algunas herramientas faltan; revisa los avisos de arriba."
