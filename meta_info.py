app_version = "0.2.0"
assert str(app_version)

def create_metadata_file():
    """Function to create a version metadata file with Pyinstaller for this project.
    """
    import pyinstaller_versionfile

    pyinstaller_versionfile.create_versionfile(
        output_file="file_version_info.txt",
        version=str(app_version),
        company_name="Philip Johannes Gouverneur",
        file_description="electronic Visual Analogue Scale",
        internal_name="eVAS.exe",
        legal_copyright="© Philip Johannes Gouverneur. All rights reserved.",
        original_filename="eVAS.exe",
        product_name="eVAS"
    )

if __name__ == '__main__':
    create_metadata_file()