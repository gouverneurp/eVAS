import platform
from packaging import version

def is_allowed_mac_version():
    """Check whether the used MacOS Version is not to old.
    Currently, we just allow for 10.15 or higher.

    Returns:
        bool: Whether the used MacOS Version is okay.
    """
    return version.parse(platform.mac_ver()[0]) >= version.parse("10.15")

def load_iot():
    """Loads the apple framework IOKit

    Returns:
        iot: apple framework IOKit
    """
    try:
        import objc
        from Foundation import NSBundle
        IOKit = NSBundle.bundleWithIdentifier_('com.apple.framework.IOKit')

        ioset = {}
        functions = [
            ("IOHIDRequestAccess", b"BI"),
            ("IOHIDCheckAccess", b"II"),
        ]

        objc.loadBundleFunctions(IOKit, ioset, functions)

        return ioset

    except Exception as e:
        print(e)

def is_keyboard_verified(ioset=None, kIOHIDAccessTypeGranted=0, kIOHIDRequestTypeListenEvent=1):
    """Checks whether keyboard monitoring is verified or not.

    Args:
        ioset (iot, optional): The apple framework IOKit. Can be retrieved with 'load_iot()'. Defaults to None.
        kIOHIDAccessTypeGranted (int, optional): Flag for granted status. Defaults to 0.
        kIOHIDRequestTypeListenEvent (int, optional): Flag for the listen event. Defaults to 1.

    Returns:
        bool: Whether keyboard monitoring can be applied or further rights are needed.
    """
    try:
        if ioset is None:
            ioset = load_iot()

        status = ioset['IOHIDCheckAccess'](kIOHIDRequestTypeListenEvent)

        return status == kIOHIDAccessTypeGranted

    except Exception as e:
        print(e)

def request_access():
    """Function to open the Apple System Preferences at the Privacy section to grant Keyboard Monitoring rights.
    """
    from AppKit import NSWorkspace, NSURL

    url = "x-apple.systempreferences:com.apple.preference.security?Privacy_ListenEvent"
    url = NSURL.alloc().initWithString_(url)
    NSWorkspace.sharedWorkspace().openURL_(url)