"""Offline SMS-SUBMIT lab; a deliberately small subset, not a full SMS stack."""

import argparse
import json
from pathlib import Path

from pycrate_mobile.TS23038 import decode_7b, encode_7b
from pycrate_mobile.TS23040_SMS import SMS_SUBMIT


VECTORS = Path(__file__).parent / "examples" / "sms_vectors.json"


def _ucs2_bytes(text):
    # UCS-2 has no supplementary-plane characters or surrogate pairs.
    if any(ord(c) > 0xFFFF or 0xD800 <= ord(c) <= 0xDFFF for c in text):
        raise ValueError("This UCS-2 lab accepts BMP characters, excluding surrogates")
    return text.encode("utf-16-be")


def _decode_gsm7_with_length(payload, septets):
    """Use TP-UDL so a real final @ or CR cannot be mistaken for padding.

    Pycrate 0.8.1 decode_7b() does not accept a septet count. Append a temporary
    'A' septet after exactly the declared data bits, then remove that character.
    Validate by re-encoding the meaningful bits, ignoring unused padding bits.
    """
    bits = 7 * septets
    mask = (1 << bits) - 1
    meaningful = int.from_bytes(payload, "little") & mask
    tagged = meaningful | (0x41 << bits)
    tagged_bytes = tagged.to_bytes((bits + 7 + 7) // 8, "little")
    text = decode_7b(tagged_bytes)[:-1]
    rebuilt, count = encode_7b(text)
    if count != septets or int.from_bytes(rebuilt, "little") & mask != meaningful:
        raise ValueError("Invalid or unsupported GSM 7-bit escape sequence")
    return text


def encode_submit(text, recipient="+12025550123", alphabet="gsm7", reference=0):
    """Build SMSC-length 00 + a basic SMS-SUBMIT TPDU without UDH or TP-VP."""
    if not recipient.startswith("+") or not 1 <= len(recipient[1:]) <= 20:
        raise ValueError("Expected + followed by 1..20 ASCII digits")
    if any(c not in "0123456789" for c in recipient[1:]):
        raise ValueError("Expected an international numeric address")
    if not isinstance(reference, int) or not 0 <= reference <= 255:
        raise ValueError("TP-MR must be in 0..255")
    if alphabet == "gsm7":
        payload, udl = encode_7b(text)
        dcs = 0
    elif alphabet == "ucs2":
        payload = _ucs2_bytes(text)
        udl, dcs = len(payload), 8
    else:
        raise ValueError("Supported alphabets: gsm7, ucs2")
    if len(payload) > 140:
        raise ValueError("Single-part TP-UD exceeds 140 octets; UDH is outside this lab")

    message = SMS_SUBMIT()
    message["TP_MR"].set_val(reference)
    message["TP_DA"]["Num"].encode(recipient[1:])
    message["TP_DCS"].from_bytes(bytes([dcs]))
    message["TP_UD"]["UD"].set_val(payload)
    # Use the encoder's septet count, not a count inferred from packed octets.
    message["TP_UD"]["UDL"].set_val(udl)
    return (b"\x00" + message.to_bytes()).hex().upper()


def decode_submit(pdu_hex):
    """Validate this lab's subset before handing the TPDU to Pycrate."""
    try:
        raw = bytes.fromhex(pdu_hex)
    except ValueError as exc:
        raise ValueError("PDU must contain complete hexadecimal octets") from exc
    if len(raw) < 9 or raw[0] != 0:
        raise ValueError("Expected a PDU with SMSC-length 00 and a complete TPDU")
    tpdu = raw[1:]
    if tpdu[0] != 0x01:
        raise ValueError("Only first octet 01 (SMS-SUBMIT, no UDH/VP) is supported")
    digits = tpdu[2]
    if not 1 <= digits <= 20 or tpdu[3] != 0x91:
        raise ValueError("Only numeric international TP-DA with TOA 91 is supported")
    address_end = 4 + (digits + 1) // 2
    if len(tpdu) < address_end + 3:
        raise ValueError("Truncated address, PID, DCS or UDL")
    nibbles = [n for b in tpdu[4:address_end] for n in (b & 15, b >> 4)]
    if any(n > 9 for n in nibbles[:digits]):
        raise ValueError("Non-decimal destination digit")
    if digits % 2 and nibbles[-1] != 15:
        raise ValueError("An odd-length address requires high-nibble F padding")
    pid, dcs, udl = tpdu[address_end:address_end + 3]
    if pid != 0 or dcs not in (0, 8):
        raise ValueError("Only PID 00 and DCS 00/08 are supported")
    payload = tpdu[address_end + 3:]
    expected_octets = (7 * udl + 7) // 8 if dcs == 0 else udl
    if len(payload) != expected_octets or len(payload) > 140:
        raise ValueError("TP-UD length disagrees with TP-UDL or exceeds 140 octets")
    if dcs == 8 and udl % 2:
        raise ValueError("UCS-2 payload must have an even octet count")

    message = SMS_SUBMIT()
    message.from_bytes(tpdu)
    if dcs == 0:
        text = _decode_gsm7_with_length(message["TP_UD"]["UD"].get_val(), udl)
    else:
        text = message["TP_UD"]["UD"].decode()
        _ucs2_bytes(text)
    recipient = "+" + message["TP_DA"]["Num"].decode()
    alphabet = "gsm7" if dcs == 0 else "ucs2"
    serialized = (b"\x00" + message.to_bytes()).hex().upper()
    rebuilt = encode_submit(text, recipient, alphabet, message["TP_MR"]())
    return {
        "pdu_hex": raw.hex().upper(),
        "tpdu_hex": tpdu.hex().upper(),
        "recipient": recipient,
        "reference": message["TP_MR"](),
        "alphabet": alphabet,
        "dcs": f"{dcs:02X}",
        "text": text,
        "udl": udl,
        "udl_unit": "septets" if dcs == 0 else "octets",
        "ud_octets": len(payload),
        "serialized_hex": serialized,
        "rebuilt_hex": rebuilt,
        "object_roundtrip": serialized == raw.hex().upper(),
        "semantic_rebuild": rebuilt == raw.hex().upper(),
        "tree": message.show(),
    }


def load_vectors():
    return json.loads(VECTORS.read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample", choices=["all", "gsm7", "extension", "ucs2"], default="all")
    parser.add_argument("--tree", action="store_true", help="Print the Pycrate field tree")
    args = parser.parse_args()
    for sample in load_vectors():
        if args.sample not in ("all", sample["name"]):
            continue
        result = decode_submit(sample["pdu_hex"])
        for field in ("recipient", "text", "alphabet", "udl", "ud_octets"):
            if result[field] != sample[field]:
                raise RuntimeError(f"{sample['name']}: wrong {field}")
        if not result["object_roundtrip"] or not result["semantic_rebuild"]:
            raise RuntimeError(f"{sample['name']}: round-trip mismatch")
        print(f"[{sample['name']}] {result['text']!r} -> {result['recipient']}")
        print(f"  DCS={result['dcs']}; TP-UDL={result['udl']} {result['udl_unit']}; TP-UD={result['ud_octets']} octets")
        print(f"  PDU: {result['pdu_hex']}")
        print("  Object round-trip: PASS; semantic rebuild: PASS")
        if args.tree:
            print(result["tree"])


if __name__ == "__main__":
    main()
