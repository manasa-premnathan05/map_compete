"""Canonical Google Maps place identity for MapCompete.

One real-world business must resolve to exactly one identity, no matter how it
entered the system:

* a full Google Maps URL (``!1s0x..:0x..``, ``!19sChIJ..``, ``?cid=``, ``/g/``)
* a bare place id (``ChIJ...``)
* a CID (``0x...`` or the decimal ``?cid=`` form)
* a manually typed name (optionally with an address)

All of those are normalised onto a single canonical ``place_key`` so projects,
discovered competitors, manually entered competitors and raw Google Maps places
share one ``places`` row instead of drifting into near-duplicates.

Google encodes the same pair of 64 bit ids in two equivalent ways::

    hex pair : 0x3be7e96f92ea224f:0xa9ff73e60b0c7c2a
    place id : ChIJTyLqkm_p5zsRKnwMC-Zz_6k

``ChIJ...`` is url-safe base64 of a tiny protobuf::

    outer : field 1, wire 2 (length delimited) -> inner message (18 bytes)
    inner : field 1, wire 1 (fixed64, little endian) = 0x3be7e96f92ea224f
            field 2, wire 1 (fixed64, little endian) = 0xa9ff73e60b0c7c2a

The second half of the hex pair is the CID, which is what ``?cid=`` links use
in decimal form. Because the hex pair can be reconstructed from a place id and
vice versa, both forms collapse onto the same canonical key.
"""

import base64
import binascii
import re
import urllib.parse
from typing import Any, Dict, Optional, Tuple

UINT64_MASK = (1 << 64) - 1

# Identity strength. Higher confidence always wins when the same place arrives
# twice with different metadata (e.g. the project name typed by hand first and
# the real Google Maps place discovered later).
CONFIDENCE = {
    'place_id': 3,
    'hex_id': 3,
    'cid': 2,
    'kgmid': 2,
    'coordinates': 1,
    'name_address': 1,
    'name': 0,
}

# Sources that identify an actual Google Maps listing (not a guess based on
# text). Only these are safe to de-duplicate on across different names.
STRONG_SOURCES = ('place_id', 'hex_id', 'cid', 'kgmid')

_PLACE_ID_RE = re.compile(r'ChIJ[0-9A-Za-z_\-]{6,}', re.IGNORECASE)
_HEX_PAIR_RE = re.compile(r'0x[0-9a-fA-F]{1,20}:0x[0-9a-fA-F]{1,20}', re.IGNORECASE)
_CID_QUERY_RE = re.compile(r'[?&]cid=(?P<cid>0x[0-9a-fA-F]{4,}|\d{1,25})', re.IGNORECASE)
_KGMID_RE = re.compile(r'/(?:g|m)/[0-9a-zA-Z_]{5,}', re.IGNORECASE)
_COORD_AT_RE = re.compile(r'@(-?\d{1,3}(?:\.\d+)?),(-?\d{1,3}(?:\.\d+)?)')
_COORD_DATA_RE = re.compile(r'!3d(-?\d{1,3}(?:\.\d+)?)!4d(-?\d{1,3}(?:\.\d+)?)')
_PLACE_PATH_RE = re.compile(r'/maps/place/([^/@?]+)')

# Filler words dropped when comparing business names loosely.
_NAME_STOPWORDS = {
    'a', 'an', 'and', 'at', 'by', 'for', 'in', 'of', 'on', 'the', 'to', 'with',
}


# ---------------------------------------------------------------------------
# small helpers
# ---------------------------------------------------------------------------

def _b64url_decode(value: str) -> bytes:
    padded = value + '=' * (-len(value) % 4)
    return base64.urlsafe_b64decode(padded.encode('ascii'))


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode('ascii').rstrip('=')


def _read_varint(data: bytes, index: int) -> Tuple[int, int]:
    result = 0
    shift = 0
    while index < len(data):
        byte = data[index]
        index += 1
        result |= (byte & 0x7F) << shift
        if not byte & 0x80:
            return result, index
        shift += 7
        if shift > 70:
            break
    raise ValueError('truncated varint')


def _encode_varint(value: int) -> bytes:
    out = bytearray()
    value &= UINT64_MASK
    while True:
        byte = value & 0x7F
        value >>= 7
        if value:
            out.append(byte | 0x80)
        else:
            out.append(byte)
            return bytes(out)


def _encode_fixed64(field: int, value: int) -> bytes:
    key = (field << 3) | 1  # wire type 1 == 64 bit
    return bytes([key]) + (value & UINT64_MASK).to_bytes(8, 'little')


def _encode_bytes_field(field: int, payload: bytes) -> bytes:
    key = (field << 3) | 2  # wire type 2 == length delimited
    return bytes([key]) + _encode_varint(len(payload)) + payload


def _iter_protobuf(data: bytes):
    """Yield ``(field_number, wire_type, value)`` for each protobuf field.

    ``value`` is an ``int`` for varint/fixed fields and ``bytes`` for
    length-delimited fields. Malformed trailing bytes simply end iteration.
    """
    index = 0
    while index < len(data):
        try:
            key, index = _read_varint(data, index)
        except ValueError:
            return
        field, wire = key >> 3, key & 0x07
        if wire == 0:
            value, index = _read_varint(data, index)
            yield field, wire, value
        elif wire == 1:
            chunk = data[index:index + 8]
            index += 8
            if len(chunk) < 8:
                return
            yield field, wire, int.from_bytes(chunk, 'little')
        elif wire == 2:
            length, index = _read_varint(data, index)
            chunk = data[index:index + length]
            index += length
            if len(chunk) < length:
                return
            yield field, wire, chunk
        elif wire == 5:
            chunk = data[index:index + 4]
            index += 4
            if len(chunk) < 4:
                return
            yield field, wire, int.from_bytes(chunk, 'little')
        else:
            return


# ---------------------------------------------------------------------------
# Google identity codecs
# ---------------------------------------------------------------------------

def normalize_hex_pair(value: Optional[str]) -> Optional[str]:
    """Return ``0x<h>:0x<l>`` (lower-case, 64 bit padded) for any hex pair."""
    if not value:
        return None
    match = _HEX_PAIR_RE.search(str(value))
    if not match:
        return None
    high, low = match.group(0).split(':')
    return '0x%016x:0x%016x' % (int(high, 16) & UINT64_MASK, int(low, 16) & UINT64_MASK)


def parse_place_id(place_id: Optional[str]) -> Optional[Tuple[int, int]]:
    """Decode a ``ChIJ...`` place id into its two 64 bit ids ``(high, low)``."""
    if not place_id:
        return None
    value = str(place_id).strip()
    if value.lower().startswith('place_id:'):
        value = value.split(':', 1)[1]
    if not value or value.lower().startswith('0x'):
        return None
    try:
        raw = _b64url_decode(value)
    except (binascii.Error, ValueError):
        return None

    inner = None
    for field, wire, chunk in _iter_protobuf(raw):
        if wire == 2 and field == 1 and inner is None:
            inner = chunk
    if not isinstance(inner, (bytes, bytearray)):
        inner = raw

    high = low = None
    for field, wire, chunk in _iter_protobuf(inner):
        if field not in (1, 2) or not isinstance(chunk, int):
            continue
        if field == 1 and high is None:
            high = chunk
        elif field == 2 and low is None:
            low = chunk
    if high is None or low is None:
        return None
    return high & UINT64_MASK, low & UINT64_MASK


def place_id_from_pair(high: int, low: int) -> str:
    """Encode a hex pair into the canonical ``ChIJ...`` place id."""
    inner = _encode_fixed64(1, high) + _encode_fixed64(2, low)
    return _b64url_encode(_encode_bytes_field(1, inner))


def place_id_from_hex(hex_pair: Optional[str]) -> Optional[str]:
    """Rebuild the ``ChIJ...`` place id from a ``0x..:0x..`` string."""
    normalized = normalize_hex_pair(hex_pair)
    if not normalized:
        return None
    high, low = normalized.split(':')
    return place_id_from_pair(int(high, 16), int(low, 16))


def cid_from_hex(hex_pair: Optional[str]) -> Optional[str]:
    """The CID (decimal form used by ``?cid=``) is the low half of the pair."""
    normalized = normalize_hex_pair(hex_pair)
    if not normalized:
        return None
    _, low = normalized.split(':')
    return str(int(low, 16))


def normalize_cid(value: Optional[str]) -> Optional[str]:
    """Return the decimal CID for ``0x..`` / decimal / ``?cid=`` inputs."""
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    match = _CID_QUERY_RE.search(text)
    if match:
        text = match.group('cid')
    if text.lower().startswith('0x'):
        try:
            return str(int(text, 16) & UINT64_MASK)
        except ValueError:
            return None
    return str(int(text)) if text.isdigit() else None


def is_google_maps_url(value: Optional[str]) -> bool:
    """True for Google Maps profile links (not for arbitrary URLs)."""
    if not value:
        return False
    text = str(value).strip().lower()
    return ('google.' in text or 'goo.gl' in text) and ('/maps' in text or 'cid=' in text)


# ---------------------------------------------------------------------------
# text normalisation
# ---------------------------------------------------------------------------

def normalize_name(name: Optional[str], aggressive: bool = False) -> str:
    """Lower-case, punctuation-free identity for a business name.

    ``aggressive=True`` additionally drops filler words ("and", "the", "&" ...)
    so that "Aura Salon & Wellness" and "Aura Salon and Wellness" compare
    equal. That form is only used for text-based fallback matching - never as
    the canonical key, which stays readable and stable.
    """
    base = re.sub(r'[^a-z0-9]+', ' ', (name or '').strip().lower()).strip()
    if not aggressive:
        return base
    tokens = [token for token in base.split() if token not in _NAME_STOPWORDS]
    return ' '.join(tokens) or base


def normalize_address(address: Optional[str]) -> str:
    """Normalised address used only for last-resort identity."""
    cleaned = re.sub(r'\b\d{6}\b', '', address or '')  # drop stray pin codes
    return re.sub(r'[^a-z0-9]+', ' ', cleaned.strip().lower()).strip()


def _decode_text(value: Optional[str]) -> str:
    if not value:
        return ''
    text = str(value).strip()
    if '%' in text:
        try:
            text = urllib.parse.unquote(text)
        except Exception:  # pragma: no cover - defensive
            pass
    return text


def _name_from_maps_url(url: str) -> Optional[str]:
    match = _PLACE_PATH_RE.search(url)
    if not match:
        return None
    name = _decode_text(match.group(1)).replace('+', ' ').strip()
    return name or None


def _to_float(value: Any) -> Optional[float]:
    if value is None or value == '':
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _pair_to_hex(high: int, low: int) -> str:
    return '0x%016x:0x%016x' % (high & UINT64_MASK, low & UINT64_MASK)


# ---------------------------------------------------------------------------
# the canonical key
# ---------------------------------------------------------------------------

def extract_place_identity(gmap_url: Optional[str] = None,
                           name: Optional[str] = None,
                           address: Optional[str] = None,
                           place_key: Optional[str] = None,
                           google_place_id: Optional[str] = None,
                           hex_id: Optional[str] = None,
                           cid: Optional[str] = None,
                           kgmid: Optional[str] = None,
                           latitude: Any = None,
                           longitude: Any = None) -> Dict[str, Any]:
    """Resolve every available hint into one canonical place identity.

    The returned dict always contains ``place_key`` (empty when nothing at all
    is known), ``identity_source`` and ``confidence``. Callers may pass extra
    hints collected from the UI or from a discovery result; they are merged
    with whatever the URL already encodes.
    """
    url_text = _decode_text(gmap_url)
    has_url_identity = bool(
        _HEX_PAIR_RE.search(url_text) or _PLACE_ID_RE.search(url_text)
        or _CID_QUERY_RE.search(url_text) or _KGMID_RE.search(url_text)
    )
    url_is_maps = is_google_maps_url(url_text) or has_url_identity

    # ---- raw signals ----------------------------------------------------
    raw_hex = hex_id or None
    if not raw_hex and url_text:
        match = _HEX_PAIR_RE.search(url_text)
        if match:
            raw_hex = match.group(0)

    raw_place_id = (google_place_id or '').strip() or None
    if not raw_place_id and url_text:
        match = _PLACE_ID_RE.search(url_text)
        if match:
            raw_place_id = match.group(0)
    if not raw_place_id and url_text and not has_url_identity:
        stripped = url_text.strip()  # a bare place id pasted into the URL box
        if _PLACE_ID_RE.fullmatch(stripped):
            raw_place_id = stripped

    raw_cid = cid if cid not in (None, '') else None
    if raw_cid is None and url_text:
        match = _CID_QUERY_RE.search(url_text)
        if match:
            raw_cid = match.group('cid')

    raw_kgmid = (kgmid or '').strip() or None
    if not raw_kgmid and url_text:
        match = _KGMID_RE.search(url_text)
        if match:
            raw_kgmid = _decode_text(match.group(0))

    lat = _to_float(latitude)
    lng = _to_float(longitude)
    if (lat is None or lng is None) and url_text:
        match = _COORD_DATA_RE.search(url_text) or _COORD_AT_RE.search(url_text)
        if match:
            lat = _to_float(match.group(1))
            lng = _to_float(match.group(2))

    # ---- text identity --------------------------------------------------
    clean_name = (name or '').strip() or (_name_from_maps_url(url_text) if url_is_maps else '') or ''
    clean_address = (address or '').strip()
    normalized_name = normalize_name(clean_name)
    normalized_address = normalize_address(clean_address)
    core_name = normalize_name(clean_name, aggressive=True)
    core_address = normalize_name(clean_address, aggressive=True)

    # ---- strongest available key ---------------------------------------
    hex_pair = normalize_hex_pair(raw_hex)
    identity_source = 'unknown'
    resolved_place_id = None
    resolved_cid = None
    lookup_keys = []
    key = ''

    if hex_pair:
        identity_source = 'hex_id'
        resolved_place_id = place_id_from_hex(hex_pair)
        resolved_cid = str(int(hex_pair.split(':')[1], 16))
        key = 'place:' + hex_pair
    else:
        parsed = parse_place_id(raw_place_id)
        if parsed:
            candidate_hex = _pair_to_hex(*parsed)
            # Only trust the decoded pair when it round-trips exactly, so odd
            # place id shapes stay opaque instead of colliding on a bogus key.
            if place_id_from_hex(candidate_hex) == str(raw_place_id).rstrip('='):
                hex_pair = candidate_hex
                identity_source = 'place_id'
                resolved_place_id = str(raw_place_id)
                resolved_cid = str(parsed[1])
                key = 'place:' + hex_pair
            else:
                raw_place_id = str(raw_place_id)

        if not key:
            resolved_cid = normalize_cid(raw_cid)
            if resolved_cid:
                identity_source = 'cid'
                key = 'cid:' + resolved_cid
            elif raw_place_id:
                identity_source = 'place_id'
                resolved_place_id = raw_place_id
                key = 'place_id:' + raw_place_id
            elif raw_kgmid:
                identity_source = 'kgmid'
                key = 'kgmid:' + raw_kgmid
            elif lat is not None and lng is not None and normalized_name:
                identity_source = 'coordinates'
                key = 'geo:%s@%.6f,%.6f' % (normalized_name, lat, lng)
            elif normalized_name and normalized_address:
                identity_source = 'name_address'
                key = 'addr:%s|%s' % (normalized_name, normalized_address)
            elif normalized_name:
                identity_source = 'name'
                key = 'name:' + normalized_name

    if place_key:
        explicit = str(place_key).strip()
        if explicit:
            if not key:
                key = explicit
                identity_source = 'explicit'
            lookup_keys.append(explicit)

    for candidate in (key,
                      'place:' + hex_pair if hex_pair else None,
                      'place_id:' + resolved_place_id if resolved_place_id else None,
                      'cid:' + resolved_cid if resolved_cid else None,
                      'kgmid:' + raw_kgmid if raw_kgmid else None):
        if candidate and candidate not in lookup_keys:
            lookup_keys.append(candidate)

    # Text-only keys are never authoritative on their own: they are only used
    # to find an existing row that was created from a name/address before a
    # real Google Maps identity became known.
    text_keys = []
    if normalized_name and normalized_address:
        text_keys.append('addr:%s|%s' % (normalized_name, normalized_address))
    if normalized_name:
        text_keys.append('name:' + normalized_name)
    if core_name and core_name != normalized_name:
        text_keys.append('name:' + core_name)
    if core_name and core_address and (core_name, core_address) != (normalized_name, normalized_address):
        text_keys.append('addr:%s|%s' % (core_name, core_address))
    if core_name and lat is not None and lng is not None:
        text_keys.append('geo:%s@%.6f,%.6f' % (core_name, lat, lng))

    return {
        'place_key': key,
        'identity_source': identity_source,
        'confidence': CONFIDENCE.get(identity_source, 1 if key else 0),
        'is_strong': identity_source in STRONG_SOURCES,
        'google_place_id': resolved_place_id,
        'hex_id': hex_pair,
        'cid': resolved_cid,
        'kgmid': raw_kgmid,
        'latitude': lat,
        'longitude': lng,
        'name': clean_name or None,
        'normalized_name': normalized_name or None,
        'core_name': core_name or None,
        'address': clean_address or None,
        'normalized_address': normalized_address or None,
        'google_maps_url': (gmap_url or '').strip() or None,
        'url_is_maps': url_is_maps,
        'lookup_keys': lookup_keys,
        'text_keys': text_keys,
    }


def is_strong_identity(identity: Optional[Dict[str, Any]]) -> bool:
    """True when the identity points at a real Google Maps listing."""
    if not identity:
        return False
    if identity.get('is_strong'):
        return True
    return identity.get('identity_source') in STRONG_SOURCES


def maps_url_for_place(place: Optional[Dict[str, Any]]) -> Optional[str]:
    """Canonical Google Maps link for a stored place row."""
    if not place:
        return None
    place_id = place.get('google_place_id')
    if place_id:
        return 'https://www.google.com/maps/place/?q=place_id:%s' % place_id
    cid = place.get('cid')
    if cid:
        return 'https://maps.google.com/?cid=%s' % cid
    hex_id = place.get('hex_id')
    if hex_id:
        return 'https://www.google.com/maps/search/?api=1&query=%s' % urllib.parse.quote(hex_id)
    name = place.get('name')
    if name:
        query = name if not place.get('address') else '%s %s' % (name, place['address'])
        return 'https://www.google.com/maps/search/?api=1&query=%s' % urllib.parse.quote(query)
    return None
