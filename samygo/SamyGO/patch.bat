@echo off
SetLocal EnableDelayedExpansion
echo Searching for vermagic postion. Please wait...
for /L %%G in (700,1,3000) do (
	for /f "usebackq tokens=*"  %%A in (`cmd /c "dd.exe if=antysfd.ko of=- bs=1 skip=%%G count=9 conv=notrunc 2>nul"`) do ( 
			set test_value=%%A
		)
		
	if "!test_value!" == "vermagic=" (
		echo Found vermagic at: %%G
		set /A fPos=%%G + 9
		goto :loopBreak
	)
)
:loopBreak
echo Vermagic patch position is: %fPos%
call :checksize "vermagic.txt" 
set /a fSize = %errorlevel%
echo File size is %fSize%
set /a zeroPosition = %fSize% + %fPos%
echo Zero position is %zeroPosition%
echo Vermagic is:
type vermagic.txt
dd.exe if=vermagic.txt of=antysfd.ko bs=1 seek=%fPos% count=%fSize% conv=notrunc
dd.exe if=/dev/zero of=antysfd.ko bs=1 seek=%zeroPosition% count=1 conv=notrunc
pause
goto :eof

:checksize
REM echo filename is %1
set /A filesize = %~z1 - 1
REM echo filesize is %filesize%
exit /b %filesize%
goto :eof
