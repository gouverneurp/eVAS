#change directory to script's directory and output 
Push-Location(split-path $MyInvocation.MyCommand.Path -Parent) 

Set-Location ..

# Create env
python -m venv venv
# Activate it
.\venv\Scripts\activate
# Update pip
python -m pip install --upgrade pip
# Install requirements
python -m pip install -r requirements.txt

# Create info file with meta data
python .\meta_info.py

# Create exe
pyinstaller eVAS.py `
            --clean `
            --onefile `
            --noconsole `
            --icon='images/icon.ico' `
            --add-data 'images/icon.png;images/' `
            --version-file file_version_info.txt `
            -n 'eVAS' `
            -y

# Clean up
Remove-Item eVAS.spec
Remove-Item file_version_info.txt
Remove-Item -r -fo build
