# osint-toolkit

Instalación y scripts de reconocimiento OSINT para **Arch Linux**.

> ⚠️ Úsalo únicamente sobre objetivos propios o con autorización escrita.
> Varias de estas herramientas hacen consultas activas contra la infraestructura
> del objetivo y quedan registradas en sus logs.

## Instalación

```bash
git clone <url-de-este-repo> osint-toolkit
cd osint-toolkit
./install.sh
```

El script es idempotente: puedes relanzarlo cuando quieras para actualizar.
Al terminar imprime qué herramientas quedaron instaladas y cuáles fallaron.

Abre una terminal nueva después (añade `~/go/bin` al `PATH`).

## Uso rápido

```bash
./recon.sh ejemplo.com
```

Encadena whois → DNS → subfinder → httpx → theHarvester → dnstwist y deja todo
en `resultados/ejemplo.com-<fecha>/`.

## Claves de API

```bash
cp .env.example .env
$EDITOR .env
```

Opcionales, pero Shodan, Censys, SecurityTrails y Hunter.io amplían bastante los
resultados de subfinder y theHarvester. `.env` está en `.gitignore`.

## Herramientas incluidas

### Personas e identidades
| Herramienta | Qué hace |
|---|---|
| `sherlock` | Busca un nombre de usuario en ~400 redes sociales |
| `maigret` | Como sherlock pero más amplio, y extrae datos del perfil |
| `holehe` | Dice en qué webs está registrado un email (sin avisar al dueño) |
| `socialscan` | Comprueba si un email/usuario está libre o cogido |
| `h8mail` | Busca un email en volcados de brechas (requiere claves) |

### Dominios e infraestructura
| Herramienta | Qué hace |
|---|---|
| `subfinder` | Enumeración pasiva de subdominios |
| `amass` | Mapeo de superficie de ataque, pasivo y activo |
| `httpx` | Sondea qué hosts responden, con código, título y tecnologías |
| `dnsx` | Resolución DNS masiva |
| `theHarvester` | Emails, hosts y subdominios desde buscadores y crt.sh |
| `dnstwist` | Dominios parecidos registrados (phishing, typosquatting) |
| `whois` / `dig` | Consultas básicas de registro y DNS |
| `nmap` | Escaneo de puertos y servicios |

## Ejemplos

```bash
sherlock usuario123
maigret usuario123 --html
holehe correo@ejemplo.com
subfinder -d ejemplo.com -silent | httpx -silent -title -tech-detect
dnstwist --registered mibanco.com
theHarvester -d ejemplo.com -b duckduckgo,crtsh
nmap -sV -Pn ejemplo.com          # solo con autorización
```

## Notas

- `install.sh` no aborta si una herramienta falla: sigue y lo reporta al final.
- Los resultados (`resultados/`) están ignorados por git — suelen contener
  datos personales.
- Alternativa para varias de estas: el AUR (`yay -S spiderfoot recon-ng`).

## Ejecutar en una máquina remota

Los escaneos largos conviene lanzarlos en una máquina fija y consultarlos desde
otra. Define el atajo en `~/.ssh/config` del cliente:

```
Host servidor
    HostName <ip>
    User <usuario>
    IdentityFile ~/.ssh/id_ed25519
```

Instala allí el toolkit y usa `tmux` para que el escaneo sobreviva a que se
corte la conexión:

```bash
ssh servidor
tmux new -s osint
./recon.sh ejemplo.com
# Ctrl+b, luego d   -> te desconectas y el escaneo sigue
exit
```

Para retomarlo más tarde:

```bash
ssh servidor
tmux attach -t osint
```

Y para traerte los resultados:

```bash
rsync -avz servidor:~/osint-toolkit/resultados/ ~/resultados-osint/
```

El script `scan.sh` automatiza todo eso desde el cliente:

```bash
./scan.sh servidor ejemplo.com
```
