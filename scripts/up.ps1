$ErrorActionPreference = "Stop"

$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $root

function Write-Section($title) {
  Write-Host ""
  Write-Host ("=" * 72)
  Write-Host $title
  Write-Host ("=" * 72)
}

function Get-ContainerHealth([string]$containerName) {
  try {
    $health = docker inspect -f '{{.State.Health.Status}}' $containerName 2>$null
    if ($LASTEXITCODE -ne 0) { return $null }
    $health = ($health | Out-String).Trim()
    if (-not $health) { return $null }
    return $health
  } catch {
    return $null
  }
}

function Get-ContainerStatus([string]$containerName) {
  try {
    $status = docker inspect -f '{{.State.Status}}' $containerName 2>$null
    if ($LASTEXITCODE -ne 0) { return $null }
    $status = ($status | Out-String).Trim()
    if (-not $status) { return $null }
    return $status
  } catch {
    return $null
  }
}

Write-Section "WD Gateway TTS - docker compose up (with friendly errors)"
Write-Host "root: $root"

Get-Command docker -ErrorAction Stop | Out-Null

Write-Host ""
Write-Host "-> docker compose up -d --build"
docker compose up -d --build
if ($LASTEXITCODE -ne 0) {
  throw "docker compose up failed (exit=$LASTEXITCODE)"
}

$containerName = "sglang-server"
$timeoutS = 240
$pollS = 5
$deadline = (Get-Date).AddSeconds($timeoutS)

Write-Host ""
Write-Host "waiting for '$containerName' health (timeout=${timeoutS}s)..."

while ((Get-Date) -lt $deadline) {
  $status = Get-ContainerStatus $containerName
  $health = Get-ContainerHealth $containerName

  if ($status -eq "running" -and $health -eq "healthy") {
    Write-Host "ok: $containerName is healthy"
    Write-Section "Endpoints"
    Write-Host "- web:         http://localhost:8080/"
    Write-Host "- sglang:       http://localhost:8082/ (health: /health)"
    Write-Host "- orchestrator: http://localhost:9100/healthz (ws: ws://localhost:9100/chat)"
    Write-Host "- ws_tts:       http://localhost:9000/healthz (ws: ws://localhost:9000/tts)"
    Write-Host ""
    Write-Host "done"
    exit 0
  }

  if ($health -eq "unhealthy" -or $status -eq "exited") {
    break
  }

  Start-Sleep -Seconds $pollS
}

Write-Section "ERROR: container sglang-server is unhealthy"
Write-Host "這通常代表 SGLang 未通過 healthcheck。docker compose CLI 可能會顯示："
Write-Host "  dependency failed to start: container sglang-server is unhealthy"
Write-Host ""
Write-Host "立即排查（請直接複製執行）："
Write-Host "  docker compose ps"
Write-Host "  docker compose logs --tail 200 sglang"
Write-Host "  curl -i http://localhost:8082/health"
Write-Host "  curl http://localhost:8082/v1/models -H `"Authorization: Bearer <SGLANG_API_KEY>`""
Write-Host ""
Write-Host "常見原因："
Write-Host "- HF_TOKEN 缺失/無權限 → HuggingFace 模型下載失敗（尤其是 Llama/Gemma）"
Write-Host "- SGLANG_MODEL 指到不存在或需要授權的 repo"
Write-Host "- GPU VRAM 不足 / OOM（請看 logs 關鍵字：OOM, CUDA out of memory）"

Write-Section "docker compose ps"
docker compose ps | Out-Host

Write-Section "docker compose logs (tail 200) - sglang"
$logs = (docker compose logs --tail 300 sglang | Out-String)
$logs | Out-Host

Write-Section "Hints"
if ($logs -match "Invalid user token|401 Client Error|Please log in") {
  Write-Host "看起來是 Hugging Face token 無效或未生效（401 / Invalid token）。"
  Write-Host "- 到 Hugging Face -> Settings -> Access Tokens 重新建立一個 token（至少 read 權限）"
  Write-Host "- 把 token 填入 .env 的 HF_TOKEN（不要加引號/空白）"
  Write-Host "- 重啟：docker compose up -d --build --force-recreate sglang"
}
elseif ($logs -match "gated repo|Access to model .* is restricted|403 Client Error") {
  Write-Host "看起來是 Hugging Face gated repo 權限不足（403）。"
  Write-Host "- 到模型頁面點選 Request access/同意條款"
  Write-Host "- 重新產生/使用具備 read 權限的 HF_TOKEN，填入 .env"
  Write-Host "- 重啟：docker compose up -d --build --force-recreate sglang"
}
elseif ($logs -match "CUDA out of memory|OutOfMemoryError|OOM") {
  Write-Host "看起來是 GPU VRAM 不足（OOM）。"
  Write-Host "- 先換小模型（修改 .env 的 SGLANG_MODEL）"
  Write-Host "- 或調整 sglang 啟動參數（mem-fraction/context-length）"
}
elseif ($logs -match "HFValidationError|Repository Not Found|404 Client Error") {
  Write-Host "看起來是模型名稱錯誤或 repo 不存在/無法存取。"
  Write-Host "- 檢查 .env 的 SGLANG_MODEL 是否拼字正確"
}
else {
  Write-Host "請先從上方 logs 找第一個 traceback / ERROR 關鍵字（通常在最上面那段）。"
}

exit 1
