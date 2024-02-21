<!---TODO: [![Journal of open source software status](https://joss.theoj.org/papers/456eaf591244858915ad8730dcbc19d7/status.svg)](https://joss.theoj.org/papers/456eaf591244858915ad8730dcbc19d7)
-->
[![status](https://joss.theoj.org/papers/fcfce9c9fb4d33c87dac8cf876fd3b27/status.svg)](https://joss.theoj.org/papers/fcfce9c9fb4d33c87dac8cf876fd3b27)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/gouverneurp/eVAS/blob/main/LICENSE.MD)

# eVAS
<picture>
    <img src="./images/icon.png?raw=true" width="50"/>
</picture>

This is the source code of the **e**lectronic **V**isual **A**nalogue **S**cale (**eVAS**).
It is an open source, easy to use and user friendly slider that records the slider values and saves them to CSV files.
The *config.ini* file can be edited to customise the **eVAS** to your needs. Examples of possible configurations can be found in the [examples](examples/) directory.
Possible errors are logged in a *log.txt* file.

<picture>
    <p align="center">
        <img src="images/screenshot_application.png?raw=true" width="500"/>
    </p>
</picture>

# How to use

## Standalone
To use **eVAS** easily, you can download the latest version and run it without any further requirements. Just follow the instructions:
- Just visit the [download page](https://gouverneurp.github.io/evas.html) or the github page with the [latest releases](https://github.com/gouverneurp/eVAS/releases/latest/)
- Download the **eVAS** standalone software ('*eVAS.exe*' for Windows)
- Launch the application
- (If you see a message like the one below from Windows Defender, run the software anyway by following these steps: )

First step                 |  Second step
:-------------------------:|:-------------------------:
<picture><img src="images/windows_protected_1.png?raw=true" width="400"/></picture>  |  <picture><img src="images/windows_protected_2.png?raw=true" width="400"/></picture>

## Examples

**eVAS** is highly configurable. Simply specify the configuration file to suit your needs. Various use cases and configuration files can be found below:

Cold hot scale             |  Custom image scale
:-------------------------:|:-------------------------:
<picture><img src="examples/cold_hot_scale/screenshot.png?raw=true" width="400"/></picture>  |  <picture><img src="examples/custom_image_scale/screenshot.png?raw=true" width="400"/></picture>
**Default**                |  **Simplified faces pain scale**
<picture><img src="examples/default/screenshot.png?raw=true" width="400"/></picture>  |  <picture><img src="examples/simplified_faces_pain_scale/screenshot.png?raw=true" width="400"/></picture>

## Python
If you want to run **eVAS** as a Python script, debug or contribute, please run the following commands:

- Clone the project
    ```bash 
    git clone https://github.com/gouverneurp/eVAS.git
    ```
- Install Python (tested with [Python 3.12](https://www.python.org/downloads/release/python-3120/))
- Create and activate a Python environment

    Windows:
    ```bash
    python -m venv venv
    .\venv\Scripts\activate
    ```
    Linux:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
- Install the requirements
    ```bash 
    pip install -r requirements.txt
    ```

- Run **eVAS** via Python
    ```bash 
    python eVAS.py
    ```

- Optionally configure the *config.ini* to change the behaviour of the **eVAS**

# Build executables

Just run the appropriate scripts to build the executables. The scripts themselves use _pyinstaller_ internally. Cross-platform building is not supported, so if you want to build the Windows application, run it on Windows.

For Windows use the [create_vas_exe.ps1](scripts/create_vas_exe.ps1) script: 
```bash 
.\scripts\create_vas_exe.ps1
```

For Ubuntu use the [create_ubuntu_app.sh](scripts/create_ubuntu_app.sh) script:
```bash 
./scripts/create_ubuntu_app.sh
```

For MacOS use the [create_mac_app.sh](scripts/create_mac_app.sh) script:
```bash 
./scripts/create_mac_app.sh
```

# How to contribute to the software
All help is welcome and needed! Feel free to open pull requests and contact us via email at [philipgouverneur@gmx.de](mailto:philipgouverneur@gmx.de).

# Report issues or problems with the software
You are welcome to open issues here directly on GitHub, or contact us by email at [philipgouverneur@gmx.de](mailto:philipgouverneur@gmx.de).

# Used resources
The application icon (<picture><img src="./images/icon.png?raw=true" width="12"/></picture>) is free to use and can be found at the following [link](https://de.freepik.com/icon/schlecht_10012613#fromView=search&term=pain+rating&page=1&position=16&track=ais).

<a href="https://de.freepik.com/icon/schlecht_10012613#fromView=search&term=pain+rating&page=1&position=16&track=ais">Created by Muhammad_Usman</a>
<!---TODO:
# Please cite our paper if you use our software or code:
```bibtex
@article{ TODO:
}
```
-->