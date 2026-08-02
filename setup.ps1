$ErrorActionPreference = "Stop"

Write-Host "Setting up Postgres + Docker Compose environment..." -ForegroundColor Cyan

# 1. Create directory
if (-not (Test-Path "init-scripts")) {
    New-Item -ItemType Directory -Path "init-scripts" | Out-Null
}

# 2. Create init-scripts/schema.sql
$schemaContent = @"
CREATE TABLE IF NOT EXISTS items (
    id VARCHAR(36) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
"@
[System.IO.File]::WriteAllText("$PWD\init-scripts\schema.sql", $schemaContent)
Write-Host "  [+] Created init-scripts/schema.sql" -ForegroundColor Green

# 3. Create .env.example
$envExampleContent = @"
POSTGRES_USER=app_user
POSTGRES_PASSWORD=app_password
POSTGRES_DB=app_db
POSTGRES_PORT=5432
DATABASE_URL=postgres://app_user:app_password@db:5432/app_db
"@
[System.IO.File]::WriteAllText("$PWD\.env.example", $envExampleContent)
Write-Host "  [+] Created .env.example" -ForegroundColor Green

# 4. Create .env if missing
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "  [+] Created .env (copied from .env.example)" -ForegroundColor Green
} else {
    Write-Host "  [!] .env already exists, keeping existing file." -ForegroundColor Yellow
}

# 5. Create or update .gitignore
if (Test-Path ".gitignore") {
    $gitignore = Get-Content ".gitignore"
    if ($gitignore -notcontains ".env") {
        Add-Content -Path ".gitignore" -Value "`n.env"
        Write-Host "  [+] Added .env to .gitignore" -ForegroundColor Green
    }
} else {
    [System.IO.File]::WriteAllText("$PWD\.gitignore", ".env")
    Write-Host "  [+] Created .gitignore with .env" -ForegroundColor Green
}

# 6. Create docker-compose.yml
$composeContent = @"
version: '3.8'

services:
  db:
    image: postgres:16-alpine
    container_name: postgres_db
    restart: always
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-app_user}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-app_password}
      POSTGRES_DB: ${POSTGRES_DB:-app_db}
    ports:
      - "${POSTGRES_PORT:-5432}:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init-scripts/schema.sql:/docker-entrypoint-initdb.d/schema.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-app_user} -d ${POSTGRES_DB:-app_db}"]
      interval: 3s
      timeout: 3s
      retries: 5

  app:
    build: .
    container_name: web_app
    restart: always
    ports:
      - "8080:8080"
    environment:
      DATABASE_URL: ${DATABASE_URL:-postgres://app_user:app_password@db:5432/app_db}
    depends_on:
      db:
        condition: service_healthy

volumes:
  postgres_data:
"@
[System.IO.File]::WriteAllText("$PWD\docker-compose.yml", $composeContent)
Write-Host "  [+] Created docker-compose.yml" -ForegroundColor Green

# 7. Create test_persistence.ps1
$testContent = @"
Write-Host 'Testing Persistence...' -ForegroundColor Cyan

Write-Host '1. Creating test row in API...' -ForegroundColor Yellow
`$body = @{
    id = 'item-123'
    title = 'Persistent Item'
    description = 'Survives restarts'
} | ConvertTo-Json

Invoke-RestMethod -Uri 'http://localhost:8080/items' -Method Post -Body `$body -ContentType 'application/json'
Write-Host '  [+] POST complete.' -ForegroundColor Green

Write-Host '2. Reading test row...' -ForegroundColor Yellow
`$response = Invoke-RestMethod -Uri 'http://localhost:8080/items/item-123' -Method Get
Write-Host '  [+] Initial read successful.' -ForegroundColor Green

Write-Host '3. Stopping and removing containers (keeping volume)...' -ForegroundColor Yellow
docker compose down

Write-Host '4. Restarting stack...' -ForegroundColor Yellow
docker compose up -d

Write-Host '5. Waiting 3 seconds for app startup...' -ForegroundColor Yellow
Start-Sleep -Seconds 3

Write-Host '6. Verifying data survived restart...' -ForegroundColor Yellow
`$verify = Invoke-RestMethod -Uri 'http://localhost:8080/items/item-123' -Method Get

if (`$verify -match 'item-123' -or `$verify.id -eq 'item-123') {
    Write-Host 'SUCCESS: PERSISTENCE PROVEN! Data survived full stack restart.' -ForegroundColor Green
} else {
    Write-Host 'FAILED: PERSISTENCE TEST FAILED. Check logs using docker compose logs app.' -ForegroundColor Red
}
"@
[System.IO.File]::WriteAllText("$PWD\test_persistence.ps1", $testContent)
Write-Host "  [+] Created test_persistence.ps1" -ForegroundColor Green

Write-Host "`nSetup files generated successfully!" -ForegroundColor Cyan