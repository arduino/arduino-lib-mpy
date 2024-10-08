import logging
from micropython import const
import se05x

TC_R = "\033[91m"
TC_G = "\033[92m"
TC_B = "\033[94m"
TC_RST = "\033[0m"
KEY_ID = const(0x10)
CERT_ID = const(0x11)

PRIVATE_KEY = const(
    b"\xd0\xa2\x15\x85\x55\xf2\x13\xa5\x3a\xae\xd8\xe1\x22\xd6\x0f\xd3"
    b"\x94\x15\x3c\xa5\x56\x65\xf2\x38\xc8\xf1\xed\x3f\xe9\x29\xde\xb0"
)

PUBLIC_KEY = const(
    b"\x04\xb0\x86\x11\x63\xf3\x8e\xb6\x64\xc5\x46\xd8\xc6\x7f\x17\xbf"
    b"\xbc\x68\x24\xf0\x07\x68\x37\xa9\x26\xc2\xbd\x2d\x48\xf8\xd6\x85"
    b"\x6e\xa9\x61\xf3\x88\x1a\x98\x5f\xd8\x50\x53\x32\x46\x7f\xe4\x24"
    b"\x4a\x94\x1f\x87\xc8\x53\xa4\x91\x2a\x09\x3f\x72\xdf\x44\xb6\x87"
    b"\x03"
)

CERT = const(
    b"\x2a\x40\x42\x1e\xe9\x36\x80\xbb\xb5\xb0\xc3\x76\xed\x7f\xca\xf8"
    b"\xf3\x12\xeb\x67\xee\xc1\x2f\x7e\xb3\x1b\x48\x36\x6d\x16\xba\xa3"
    b"\x38\x29\x5b\x22\x52\xf9\x97\x2f\xc9\xbb\x67\x2b\xc3\xe0\x0a\x57"
    b"\xbe\x64\x12\x0a\x62\xc4\xe7\xa6\xfe\xfc\xae\xee\x39\x84\xb9\x50"
    b"\x9f\x6d\x36\x87\xc0\xf6\x21\xb4\xb7\xa9\xe9\x82\x11\x0b\x9a\x62"
    b"\x04\x9f\x4f\x93\xcb\x33\xf3\x84\x95\x1e\x5f\xe8\x38\x93\xc4\xcb"
    b"\xe4\xf5\xd3\x61\x4d\x99\x14\xb2\xfb\xbe\xa5\xfe\xe8\x40\x09\xdd"
    b"\xc0\x89\xac\x27\x27\x2e\x52\x3b\x2f\x49\x09\xa5\xd3\x24\x3d\xb1"
    b"\x31\xee\x2f\xa6\x74\xb6\xb9\x1a\x4e\xd3\x48\x73\xff\x2e\x07\xc1"
    b"\x67\xf0\x75\x62\xd5\x7e\x80\x01\xe5\x24\xb4\x75\x37\x75\xf6\xfe"
    b"\x4e\x6c\xb2\xfc\xd1\xb4\x2c\x80\x72\x63\x50\x8d\x21\x86\xd7\x8b"
    b"\xf2\x75\xc2\xea\x49\x23\x95\x73\x7b\x91\x28\x69\x46\xd2\x00\x11"
    b"\x6c\x51\x65\xb4\xf9\x2b\x42\xe6\xeb\x8c\xa1\xd3\xb1\xec\xf1\x47"
    b"\x07\xe2\x24\x3d\x8c\xa5\xc3\x4f\xf5\xfd\x67\xb1\x45\x36\x6d\x30"
    b"\x0e\x89\x7d\x96\xe8\x3b\xeb\xae\x38\x1b\x07\xbd\xb4\xa8\xc1\x62"
    b"\xee\xa2\x78\x9f\xc5\x8f\xc0\x8b\x21\xdc\x55\x8e\xf2\x14\x3e\x40"
    b"\x33\xfc\x11\xf8\xc5\x2d\xc8\x0e\x73\x88\x23\xc3\xd2\xf2\xde\xb5"
    b"\x69\x0c\xa4\xb5\xb4\x64\xd5\x0f\xbd\x2a\x18\x35\x08\x73\xaa\xc5"
    b"\x32\x5a\x8f\xbe\x31\x9f\xda\x8d\x09\x5e\xbe\xf0\x9f\x45\xbe\x5d"
    b"\x5b\x26\x57\xa8\x7a\xcd\x63\xa9\x1a\x27\x49\x0a\x4e\x45\x32\x14"
    b"\x00\xbb\x88\xea\x5a\x46\x88\x59\x79\x5b\x01\xc4\xd4\x0a\x08\x55"
    b"\x20\x58\xba\xb4\x74\xfd\x40\x6b\xf6\x56\x55\xbd\xca\x56\x25\xdf"
    b"\xb8\xbb\x9a\xb7\x76\xb1\xcb\x1c\x81\xfd\x0f\xde\x87\x6a\xcf\x1d"
    b"\x77\xa4\xa0\x6a\xbe\xf7\xd0\x60\x7d\xba\xb5\x1c\xf0\x62\x4d\xab"
    b"\x62\xf9\x36\xf4\x95\x76\x90\x79\xc0\x47\xfc\x3e\x32\xc7\x60\x3a"
    b"\x31\xf4\xff\x86\xfc\x67\xb3\xa8\x32\x39\xce\x7c"
)


if __name__ == "__main__":
    logging.basicConfig(
        datefmt="%H:%M:%S",
        format="%(asctime)s.%(msecs)03d %(message)s",
        level=logging.INFO
    )

    # Create and initialize SE05x device.
    se = se05x.SE05X()

    # Print applet version.
    major, minor, patch = se.version()
    logging.info(f"{TC_G}Applet Version: {major}.{minor}.{patch}{TC_RST}")

    # Delete key object if it exists.
    if se.exists(KEY_ID):
        se.delete(KEY_ID)

    # Write public/private key pair and verify.
    se.write(KEY_ID, se05x.EC_KEY, key=(PRIVATE_KEY, PUBLIC_KEY), curve=se05x.EC_CURVE_NIST_P256)

    # Read back the public key part and verify it.
    ec_pub_key = se.read(KEY_ID)
    if PUBLIC_KEY != ec_pub_key:
        logging.info(f"{TC_R}Key verification failed!{TC_RST}")
    logging.info(f"{TC_G}Key verified successfully!{TC_RST}")
    logging.info(f"{TC_B}Public Key: " + "".join("%02X" % b for b in ec_pub_key) + TC_RST)

    # Delete certificate object if it exists.
    if se.exists(CERT_ID):
        se.delete(CERT_ID)

    # Write binary certificate object.
    se.write(CERT_ID, se05x.BINARY, binary=CERT)
    logging.info(f"{TC_G}Binary certificate written successfully!{TC_RST}")

    # Read back the certificate and verify it.
    if CERT != se.read(CERT_ID, 412):
        logging.info(f"{TC_R}Certificate verification failed!{TC_RST}")
    logging.info(f"{TC_G}Certificate verified successfully!{TC_RST}")
