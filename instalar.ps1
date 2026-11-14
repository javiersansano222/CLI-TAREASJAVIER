# instalar.ps1 — instala la CLI «tareas» desde GitHub en Windows.
#
# Uso en una sola línea (PowerShell):
#   powershell -c "irm https://raw.githubusercontent.com/javiersansano222/CLI-TAREASJAVIER/main/instalar.ps1 | iex"
#
# O desde una copia del repo:
#   powershell -ExecutionPolicy Bypass -File instalar.ps1
#
# Lo que toca: la carpeta de herramientas de uv (~\.local\bin), el PATH de
# usuario (uv tool update-shell) y, solo si faltan, .env y acciones.json en tu
# carpeta de inicio. Nunca pisa un .env que ya exista ni tu código.

function Instalar-Tareas {

    $repo = 'https://github.com/javiersansano222/CLI-TAREASJAVIER'
    $crudo = 'https://raw.githubusercontent.com/javiersansano222/CLI-TAREASJAVIER/main'
    $bin = Join-Path $HOME '.local\bin'

    # PowerShell 5.1 necesita TLS 1.2 para bajar ficheros
    try { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 } catch { }

    function Bajar([string]$url, [string]$destino) {
        if (Get-Command curl.exe -ErrorAction SilentlyContinue) {
            & curl.exe -fsSL -o $destino $url
            if ($LASTEXITCODE -ne 0) { throw "no he podido bajar $url" }
        } else {
            try { Invoke-WebRequest -UseBasicParsing -Uri $url -OutFile $destino }
            catch { throw "no he podido bajar $url" }
        }
    }

    Write-Host "[1/6] Comprobando uv (el gestor de paquetes)..." -ForegroundColor Cyan
    if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
        Write-Host "      uv no está: lo instalo desde astral.sh"
        try { Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force } catch { }
        $instalador = Join-Path $env:TEMP 'uv-instalar.ps1'
        Bajar 'https://astral.sh/uv/install.ps1' $instalador
        & powershell -NoProfile -ExecutionPolicy Bypass -File $instalador
        if ($LASTEXITCODE -ne 0) { throw "la instalación de uv ha fallado" }
        Remove-Item $instalador -ErrorAction SilentlyContinue
        if ($env:Path -notlike "*$bin*") { $env:Path = "$bin;$env:Path" }
    }
    if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
        throw "uv sigue sin verse en el PATH. Cierra y vuelve a abrir PowerShell y repite el comando."
    }

    Write-Host "[2/6] Preparando Python 3.12..." -ForegroundColor Cyan
    & uv python install 3.12
    if ($LASTEXITCODE -ne 0) { throw "no he podido preparar Python 3.12" }

    Write-Host "[3/6] Instalando la CLI tareas desde GitHub..." -ForegroundColor Cyan
    & uv tool install "$repo/archive/refs/heads/main.tar.gz" --force
    if ($LASTEXITCODE -ne 0) { throw "uv tool install ha fallado" }

    Write-Host "[4/6] Poniendo tareas en el PATH..." -ForegroundColor Cyan
    & uv tool update-shell
    if ($env:Path -notlike "*$bin*") { $env:Path = "$bin;$env:Path" }

    Write-Host "[5/6] Ficheros de configuración en $HOME..." -ForegroundColor Cyan
    $rutaEnv = Join-Path $HOME '.env'
    if (Test-Path $rutaEnv) {
        Write-Host "      .env ya existía: no lo toco."
    } else {
        Bajar "$crudo/.env.example" $rutaEnv
        Write-Host "      He creado .env con la plantilla: rellénalo con tu clave."
    }
    $rutaAcciones = Join-Path $HOME 'acciones.json'
    if (Test-Path $rutaAcciones) {
        Write-Host "      acciones.json ya existía: no lo toco."
    } else {
        Bajar "$crudo/acciones-win.json" $rutaAcciones
        Write-Host "      He creado acciones.json con las rutas de Windows."
    }

    Write-Host "[6/6] Creando la carpeta de pruebas de la IA..." -ForegroundColor Cyan
    $pruebas = Join-Path $HOME 'pruebas-tareas'
    foreach ($carpeta in 'Apuntes', 'Resúmenes', 'Clasificados') {
        New-Item -ItemType Directory -Force -Path (Join-Path $pruebas $carpeta) | Out-Null
    }
    Write-Host "      $pruebas"

    # Comprobación con la ruta completa: el PATH de esta sesión puede estar viejo
    $tareas = Join-Path $bin 'tareas.exe'
    if (-not (Test-Path $tareas)) { throw "no encuentro el ejecutable en $tareas" }
    & $tareas version
    if ($LASTEXITCODE -ne 0) { throw "tareas no arranca (código $LASTEXITCODE)" }
    & $tareas --config $rutaAcciones validar
    if ($LASTEXITCODE -ne 0) {
        Write-Host "      Aviso: el acciones.json de tu home no valida; mira el mensaje de arriba." -ForegroundColor Yellow
    }

    Write-Host ""
    Write-Host "Listo. Abre una terminal NUEVA y escribe:" -ForegroundColor Green
    Write-Host "    tareas --help"
    Write-Host "    hola"
    Write-Host "    tareas validar"
    Write-Host ""
    Write-Host "Si no has rellenado .env, las órdenes de IA salen con código 4."
}

Instalar-Tareas
