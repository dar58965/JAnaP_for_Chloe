if not exist %~dp0\packages (
    mkdir %~dp0\packages
)

REM Download Python package from our cache
if not exist %~dp0\packages\python-2.7.15.msi (
    bitsadmin.exe /transfer "Download Python" https://www.python.org/ftp/python/2.7.15/python-2.7.15.msi %~dp0\packages\python-2.7.15.msi
)

REM Install Python 
msiexec /i %~dp0\packages\python-2.7.15.msi /passive /norestart ADDLOCAL=ALL

REM Upgrade pip
C:\Python27\python.exe -m pip install --upgrade pip

REM Install requirements
C:\Python27\Scripts\pip.exe install --upgrade cython
C:\Python27\Scripts\pip.exe install boto3
C:\Python27\Scripts\pip.exe install configparser
C:\Python27\Scripts\pip.exe install numpy
C:\Python27\Scripts\pip.exe install scipy
C:\Python27\Scripts\pip.exe install mahotas
C:\Python27\Scripts\pip.exe install matplotlib
C:\Python27\Scripts\pip.exe install opencv-python
C:\Python27\Scripts\pip.exe install scikit-image
C:\Python27\Scripts\pip.exe install flask
C:\Python27\Scripts\pip.exe install joblib
C:\Python27\Scripts\pip.exe install jupyter

REM 
REM if not exist %~dp0\packages\ij150-win-java8.zip (
REM     bitsadmin.exe /transfer "Download ImageJ" https://s3.amazonaws.com/umd-cells/packages/ij150-win-java8.zip %~dp0\packages\ij150-win-java8.zip
REM )

REM if not exist %~dp0\packages\ImageJ (
REM     powershell.exe -nologo -noprofile -command "& { Add-Type -A 'System.IO.Compression.FileSystem'; [IO.Compression.ZipFile]::ExtractToDirectory('%~dp0\packages\ij150-win-java8.zip', '%~dp0\packages\'); }"
REM )
