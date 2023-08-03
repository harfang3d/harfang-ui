del /s /f /q build\*.*
for /f %%f in ('dir /ad /b build\') do rd /s /q build\%%f
del /s /f /q HarfangGUI.egg-info\*.*
for /f %%f in ('dir /ad /b HarfangGUI.egg-info\') do rd /s /q HarfangGUI.egg-info\%%f

python setup.py bdist_wheel
@REM pip uninstall -y HarfangGUI
@REM pip install .\dist\HarfangGUI-2.0.0-py3-none-win_amd64.whl
