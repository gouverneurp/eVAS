def list_serial_ports():
    """Lists the serial ports that are currently valid, i.e. that can actually be opened.

    This filters out stale/ghost entries (e.g. ports Windows still lists after a device
    was unplugged) and ports that are currently in use by another application.

    Returns:
        list: List of 'serial.tools.list_ports_common.ListPortInfo' for ports that can be opened right now.
    """
    import serial
    from serial.tools.list_ports_windows import comports

    valid_ports = []
    for port in comports():
        try:
            # opening (and immediately closing) the port is the only reliable way to know
            # whether it is actually usable right now (device present, not held by another app)
            with serial.Serial(port.device):
                pass
            valid_ports.append(port)
        except (serial.SerialException, OSError):
            continue
    return valid_ports


def ask_for_com(
    root, ports, message="Please select the COM port of the 'QST.LAB TCS2' device:"
):
    """Opens a small dialog letting the user pick a COM port from a list of (valid) ports.

    Args:
        root (tk.Tk): Parent tk window.
        ports (list): Ports to choose from, e.g. as returned by 'list_serial_ports()'.
        message (str, optional): Instruction shown above the dropdown/list.

    Returns:
        str or None: The chosen COM port (e.g. 'COM3'), or None if the user cancelled or no ports were given.
    """
    import tkinter as tk
    from tkinter import ttk
    from tkinter.messagebox import showinfo

    if not ports:
        root.withdraw()
        showinfo(
            title="eVAS: No COM ports found",
            message="No usable COM ports were found. Please connect the 'QST.LAB TCS2' device and try again.",
            parent=root,
        )
        root.deiconify()
        return None

    root.withdraw()

    dialog = tk.Toplevel(root)
    dialog.title("eVAS: Select COM port")
    dialog.attributes("-topmost", True)
    dialog.resizable(False, False)

    tk.Label(dialog, text=message, wraplength=350, justify="left").pack(
        padx=10, pady=(10, 5)
    )

    labels = [f"{p.device} ({p.description})" for p in ports]
    devices = [p.device for p in ports]

    selected = tk.StringVar(value=labels[0])
    combo = ttk.Combobox(
        dialog, textvariable=selected, values=labels, state="readonly", width=40
    )
    combo.current(0)
    combo.pack(padx=10, pady=5)

    result = {"com": None}

    def on_ok():
        result["com"] = devices[labels.index(selected.get())]
        dialog.destroy()

    def on_cancel():
        dialog.destroy()

    button_frame = tk.Frame(dialog)
    button_frame.pack(pady=(5, 10))
    tk.Button(button_frame, text="OK", width=10, command=on_ok).pack(
        side="left", padx=5
    )
    tk.Button(button_frame, text="Cancel", width=10, command=on_cancel).pack(
        side="left", padx=5
    )

    dialog.protocol("WM_DELETE_WINDOW", on_cancel)
    dialog.grab_set()
    dialog.wait_window()

    root.deiconify()
    return result["com"]


def get_com(root):
    """Function to find the COM of the 'QST.LAB TCS2' device.

    First looks for it automatically by matching "CH340" in the port description, without touching any
    port. Only if that fails is the selector dialog shown, listing the currently valid (openable) ports.

    Args:
        root (tk.Tk): Parent tk window, used to display a port-selection dialog if needed.

    Returns:
        str or None: COM port of the 'QST.LAB TCS2' device, or None if none could be determined.
    """
    import logging
    from serial.tools.list_ports_windows import comports

    # find all com ports
    ports = comports()
    # filter ports for the one with "CH340" in the description title
    ch340_ports = [x for x in ports if "CH340" in x.description]

    # if the port was found automatically, use its COM
    if len(ch340_ports) == 1:
        return ch340_ports[0].device

    print("QST.LAB TCS2 could not be found automatically.")
    ports_description = (
        ", ".join(f"{p.device} ({p.description})" for p in ports) if ports else "none"
    )
    print(f"Available ports: {ports_description}")
    logging.info(
        f"QST.LAB TCS2 could not be found automatically. Available ports: {ports_description}"
    )

    # only now probe which of the available ports can actually be opened, to populate the selector
    valid_ports = list_serial_ports()
    if valid_ports:
        prompt = "QST.LAB TCS2 could not be found automatically. Please select the correct COM port:"
    else:
        prompt = (
            "QST.LAB TCS2 could not be found automatically and no usable COM ports were detected. "
            + "Please connect the device and select the correct COM port, or cancel to continue without it."
        )
    return ask_for_com(root, valid_ports, message=prompt)


def resolve_com(root):
    """Determines a validated, currently openable COM port for the 'QST.LAB TCS2' device.

    Tries to find the device automatically. If that fails, or the found/selected port turns out to be
    unusable when actually tested, the user is informed with details and repeatedly asked to pick a
    different port from the list of currently valid ones, until a working one is chosen or cancelled.

    Args:
        root (tk.Tk): Parent tk window, used to display dialogs if needed.

    Returns:
        str or None: A validated, currently openable COM port (e.g. 'COM3'), or None if the user
            cancelled or no working port could be determined.
    """
    import serial
    from tkinter.messagebox import showinfo

    com = get_com(root)

    while com is not None:
        try:
            with serial.Serial(com):
                pass
            return com
        except (serial.SerialException, OSError) as e:
            root.withdraw()
            showinfo(
                title="eVAS: Invalid COM port",
                message=f"The COM port '{com}' could not be opened ({e}). "
                + "Please select a different, valid port.",
                parent=root,
            )
            root.deiconify()
            com = ask_for_com(root, list_serial_ports())

    return None


def send_start_trigger(com, baudrate=115200):
    """Sends a trigger to the 'QST.LAB TCS2'.

    Args:
        com (str): COM port of the 'QST.LAB TCS2' device. Can be retrieved using 'get_com()'/'resolve_com()'.
        baudrate (int, optional): Used baudrate for the signal. Defaults to 115200.
    """
    import serial

    ser = serial.Serial(com, baudrate=baudrate)
    ser.write(str.encode("H"))


if __name__ == "__main__":
    import tkinter as tk

    root = tk.Tk()
    com = resolve_com(root)
    root.destroy()

    if com is not None:
        send_start_trigger(com)
