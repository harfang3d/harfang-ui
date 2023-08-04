del /s /f /q build\*.*
for /f %%f in ('dir /ad /b build\') do rd /s /q build\%%f
del /s /f /q HarfangUI.egg-info\*.*
for /f %%f in ('dir /ad /b HarfangUI.egg-info\') do rd /s /q HarfangUI.egg-info\%%f

python setup.py bdist_wheel
@REM pip uninstall -y HarfangUI
@REM pip install .\dist\HarfangUI-2.0.0-py3-none-win_amd64.whl

pause
