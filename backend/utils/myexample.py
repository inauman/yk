from fido2.hid import CtapHidDevice
from fido2.client import Fido2Client
from exampleutils import CliInteraction
from binascii import unhexlify

# Known credential ID for localhost
cred_id = unhexlify("06b343a2fefbc636bdc8cf7fc11fb81a860ae923a70f5111acf194a0535b9db34a11aa046a56b7c9ad7dd08336a5886b")

# Locate a device
dev = next(CtapHidDevice.list_devices(), None)
if not dev:
    print("No FIDO device found")
    exit(1)

origin = "https://localhost"
client = Fido2Client(dev, origin, user_interaction=CliInteraction())

request_options = {
    "rpId": "localhost",
    "challenge": b"0" * 32,
    "userVerification": "preferred",
    "allowCredentials": [{"type": "public-key", "id": cred_id}],
}

try:
    # Get assertion selection (may contain multiple assertions)
    selection = client.get_assertion(request_options)
    
    # Get all assertions
    assertions = selection.get_assertions()
    
    # Process each assertion
    for i, assertion in enumerate(assertions):
        print(f"Assertion {i+1}:")
        
        # Print credential ID
        if assertion.credential and "id" in assertion.credential:
            print(f"  CREDENTIAL ID (hex): {assertion.credential['id'].hex()}")
        
        # Print user info if available
        if assertion.user and "id" in assertion.user:
            print(f"  USER ID: {assertion.user['id'].hex()}")
        else:
            print("  USER ID: Not available")
        
        # Print other assertion details
        print(f"  AUTHENTICATOR DATA: {assertion.auth_data.hex()}")
        print(f"  SIGNATURE: {assertion.signature.hex()}")
        
except Exception as e:
    print(f"Error: {e}")
    # Debug information
    import traceback
    traceback.print_exc()