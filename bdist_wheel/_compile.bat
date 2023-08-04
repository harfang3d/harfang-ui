del /s /f /q build\*.*
for /f %%f in ('dir /ad /b build\') do rd /s /q build\%%f
del /s /f /q harfangui.egg-info\*.*
for /f %%f in ('dir /ad /b harfangui.egg-info\') do rd /s /q harfangui.egg-info\%%f

python setup.py bdist_wheel
@REM pip uninstall -y harfangui
@REM pip install .\dist\harfangui-2.0.0-py3-none-win_amd64.whl

del /s /f /q build\*.*
for /f %%f in ('dir /ad /b build\') do rd /s /q build\%%f
del /s /f /q harfangui.egg-info\*.*
for /f %%f in ('dir /ad /b harfangui.egg-info\') do rd /s /q harfangui.egg-info\%%f
rmdir build
rmdir harfangui.egg-info

pause
