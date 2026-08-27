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


def _read_response(ser, settle=0.05, max_wait=0.4):
    """Collects whatever the TCS sends back within a short time window.

    Between stimulations the TCS II streams temperatures at 1 Hz, so a query
    answer may be surrounded by lines like '+300+300+300+300+300+300'. We
    therefore just gather everything that arrives within 'max_wait' seconds
    instead of trying to match an exact line.

    Args:
        ser (serial.Serial): Open serial connection to the TCS II.
        settle (float, optional): Grace period for the first bytes to arrive.
        max_wait (float, optional): Overall time budget for reading.

    Returns:
        str: Raw decoded text received (possibly several lines), stripped.
    """
    import time

    time.sleep(settle)
    deadline = time.time() + max_wait
    chunks = []
    while time.time() < deadline:
        waiting = ser.in_waiting
        if not waiting:
            break
        chunks.append(ser.read(waiting).decode(errors="replace"))
        time.sleep(0.05)
    return "".join(chunks).strip()


def _query(ser, command, **kwargs):
    """Sends a command to the TCS and returns its textual response.

    Args:
        ser (serial.Serial): Open serial connection to the TCS II.
        command (str): Command character(s), e.g. '?' or 'P'.

    Returns:
        str: The device response, see '_read_response()'.
    """
    ser.reset_input_buffer()
    ser.write(str.encode(command))
    return _read_response(ser, **kwargs)


def run_sanity_checks(com, baudrate=115200):
    """Opens the TCS II once, queries identity, error/battery state and the
    loaded stimulation parameters, writes everything to the log, then closes.

    This is meant to be called once when the application starts - never on the
    hot path that launches a stimulation ('send_start_trigger()'). All checks
    are read-only and non-fatal; anomalies are logged as warnings so that, if a
    stimulation later does not happen, the log shows the device state.

    Args:
        com (str): COM port of the 'QST.LAB TCS2' device. Can be retrieved using 'get_com()'/'resolve_com()'.
        baudrate (int, optional): Used baudrate. Defaults to 115200.

    Returns:
        bool: Whether the device identified itself as a 'TCS'.
    """
    import logging
    import serial

    logging.info(f"TCS: running start-up sanity checks on '{com}' at {baudrate} baud.")
    identified = False
    try:
        # 'timeout' keeps the reads from blocking if the device stays quiet.
        with serial.Serial(com, baudrate=baudrate, timeout=0.2) as ser:
            try:
                identity = _query(ser, "?")
                logging.info(f"TCS sanity check - identity ('?'): {identity!r}")
                identified = "TCS" in identity
                if not identified:
                    logging.warning(
                        "TCS sanity check - '?' did not return 'TCS'. Wrong COM "
                        f"port, wrong baudrate or device not ready? Got: {identity!r}"
                    )
            except Exception as e:
                logging.warning(f"TCS sanity check - identity check failed: '{e}'")

            try:
                errors = _query(ser, "Q")
                logging.info(f"TCS sanity check - error state ('Q'): {errors!r}")
                # 'Q' returns one digit per zone + neutral: '0' = OK, '>1' = ERROR.
                digits = [c for c in errors if c.isdigit()]
                if digits and any(c != "0" for c in digits):
                    logging.warning(
                        f"TCS sanity check - device reports a non-OK error state: {errors!r}"
                    )
            except Exception as e:
                logging.warning(f"TCS sanity check - error-state check failed: '{e}'")

            try:
                battery = _query(ser, "B")
                logging.info(f"TCS sanity check - battery ('B'): {battery!r}")
            except Exception as e:
                logging.warning(f"TCS sanity check - battery check failed: '{e}'")

            try:
                params = _query(ser, "P", max_wait=1.0)
                logging.info(
                    f"TCS sanity check - stimulation parameters ('P'): {params!r}"
                )
                if not params:
                    logging.warning(
                        "TCS sanity check - 'P' returned nothing. Is a stimulation "
                        "configured? 'L' does not launch anything without one."
                    )
            except Exception as e:
                logging.warning(f"TCS sanity check - parameter check failed: '{e}'")
    except Exception as e:
        logging.warning(
            f"TCS: start-up sanity checks could not be run (port '{com}'): '{e}'"
        )

    return identified


def send_start_trigger(com, baudrate=115200):
    """Sends the start trigger to the 'QST.LAB TCS2' to launch the configured stimulation.

    This runs on the hot path (the moment the run starts), so it does the
    minimum: open the port, send 'L', close. Device health is verified once at
    start-up by 'run_sanity_checks()'.

    Args:
        com (str): COM port of the 'QST.LAB TCS2' device. Can be retrieved using 'get_com()'/'resolve_com()'.
        baudrate (int, optional): Used baudrate for the signal. Defaults to 115200.
    """
    import serial

    # 'L' = "start stimuLation" in the TCS II serial protocol.
    with serial.Serial(com, baudrate=baudrate) as ser:
        ser.write(str.encode("L"))


if __name__ == "__main__":
    import logging
    import tkinter as tk

    # when run standalone, surface the sanity-check output on the console
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    root = tk.Tk()
    com = resolve_com(root)
    root.destroy()

    if com is not None:
        run_sanity_checks(com)
        send_start_trigger(com)
