Write-Host "Testing Persistence..." -ForegroundColor Cyan

# 1. Create a task via API
Write-Host "1. Creating test task in API..."
$body = @{ 
    title = "Test Task"
    description = "Persistence Check" 
} | ConvertTo-Json

$postResponse = Invoke-RestMethod -Uri 'http://localhost:8080/tasks' -Method Post -Body $body -ContentType 'application/json'
$taskId = $postResponse.id
Write-Host "   Created Task ID: $taskId" -ForegroundColor Green

# 2. Read task back
Write-Host "2. Reading created task..."
$response = Invoke-RestMethod -Uri "http://localhost:8080/tasks/$taskId"
Write-Host "   Read Successful: $($response.title)" -ForegroundColor Green

# 3. Destroy container stack (keeping the persistent volume)
Write-Host "3. Stopping and removing containers (keeping volume)..."
docker compose down

# 4. Restart stack
Write-Host "4. Restarting stack..."
docker compose up -d

# 5. Wait for app + DB health check
Start-Sleep -Seconds 5

# 6. Verify data survived
Write-Host "5. Verifying data survived restart..."
$verify = Invoke-RestMethod -Uri "http://localhost:8080/tasks/$taskId"

if ($verify.id -eq $taskId) {
    Write-Host "`nSUCCESS: PERSISTENCE PROVEN! Task survived full stack restart." -ForegroundColor Green
} else {
    Write-Host "`nFAILED: PERSISTENCE TEST FAILED." -ForegroundColor Red
}