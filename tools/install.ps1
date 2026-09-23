# 易 · 环境安装与自检（PowerShell 5+，仓库根执行）
#
#   powershell -ExecutionPolicy Bypass -File tools/install.ps1
#   powershell -ExecutionPolicy Bypass -File tools/install.ps1 -Check   # 装完跑全仓库质量门
#   powershell -ExecutionPolicy Bypass -File tools/install.ps1 -Demo   # 装完跑全科演示
#
# 依赖：Python 3.10+（主计算只用标准库；lunar-python/matplotlib 均为可选）
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

function Test-PythonVersion {
    $py = Get-Command python -ErrorAction SilentlyContinue
    if (-not $py) { Write-Host "× 未找到 python，请先安装 Python 3.10+" -ForegroundColor Red; exit 1 }
    $ver = & python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
    $major, $minor = $ver.Split(".")
    if ([int]$major -lt 3 -or ([int]$major -eq 3 -and [int]$minor -lt 10)) {
        Write-Host "× 需要 Python 3.10+，当前 $ver" -ForegroundColor Red; exit 1
    }
    Write-Host "√ Python $ver"
}

function Install-Kernel {
    Push-Location $Root
    try {
        & python -m pip install -e . --quiet
        if ($LASTEXITCODE -ne 0) { throw "pip install -e . 失败" }
    } finally { Pop-Location }
    & python -c "import sys; sys.path.insert(0, r'$Root\core'); import yishu_core; print('√ 内核 yishu_core', yishu_core.__version__, '可导入')"
}

function Main {
    param(
        [switch]$Check,
        [switch]$Demo
    )
    Write-Host "== 易 · 环境安装 ==" -ForegroundColor Cyan
    Test-PythonVersion
    Install-Kernel
    if ($Check) {
        Write-Host "== 全仓库质量门 ==" -ForegroundColor Cyan
        & python "$Root\tools\check.py"
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    }
    if ($Demo) {
        Write-Host "== 全科演示 ==" -ForegroundColor Cyan
        & python "$Root\tools\demo.py"
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    }
    Write-Host "完成。快速自检：python tools/check.py --fast" -ForegroundColor Green
}

Main -Check:$Check -Demo:$Demo
