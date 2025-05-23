def get_com(root):
    """Function to find the COM of the 'QST.LAB TCS2' device.

    First looks for it automatically, if not found ask for the user to define the port.

    Returns:
        str: COM port of the 'QST.LAB TCS2' device.
    """
    from serial.tools.list_ports_windows import comports
    # find all com ports
    ports = comports()
    # filter ports for the one with "CH340" in the description title
    ports = [x for x in ports if "CH340" in x.description]

    # if the port was not found
    if len(ports) != 1:
        print("QST.LAB TCS2 could not be found automatically.")

        # create a GUI to ask for the port
        import tkinter as tk
        from tkinter import simpledialog
        root.withdraw()
        com = simpledialog.askstring(title="COM", prompt="QST.LAB TCS2 could not be found automatically. Please define COM:", parent=root)
        root.deiconify()

        return com

    # if the correct port was found, use its COM
    com = ports[0].device 
    return com

def send_start_trigger(com, baudrate=115200):
    """Sends a trigger to the 'QST.LAB TCS2'.

    Args:
        com (str): COM port of the 'QST.LAB TCS2' device. Can be retrieved using 'get_com()'.
        baudrate (int, optional): Used baudrate for the signal. Defaults to 115200.
    """
    import serial
    ser = serial.Serial(com, baudrate=baudrate)
    ser.write(str.encode('H'))

if __name__ == '__main__':
    com = get_com()
    send_start_trigger(com)