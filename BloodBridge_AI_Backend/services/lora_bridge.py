"""
LoRa offline communication bridge for BloodBridge AI.

WHY LORA: Rural India has ~600M people with unreliable/no internet.
LoRa (Long Range) radio (433/868 MHz) can transmit ~250 bytes up to 15km
without internet infrastructure.

Architecture:
  Rural gateway (Raspberry Pi + LoRa hat)
    → receives compressed emergency packet over LoRa radio
    → stores locally in SQLite if offline
    → flushes to BloodBridge REST API when connectivity resumes

This module handles:
  1. Packet encoding/decoding (msgpack binary serialization)
  2. Simulated serial send (real impl uses pyserial)
  3. SQLite store-and-forward queue
  4. Queue flush when connectivity is restored
"""
import json
import time
import struct
import hashlib
import logging
import sqlite3
import asyncio
from dataclasses import dataclass, asdict
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────
LORA_SQLITE_PATH = Path(__file__).parent.parent / "data" / "lora_offline_queue.db"
LORA_MAX_QUEUE_DEPTH = 200      # Max stored packets before dropping oldest
LORA_PACKET_VERSION = 1
BLOODBRIDGE_API_BASE = "http://localhost:8000"  # Override via env in production

# Blood type encoding: compact 4-bit codes
BLOOD_TYPE_ENCODE = {
    "A+": 0, "A-": 1, "B+": 2, "B-": 3,
    "AB+": 4, "AB-": 5, "O+": 6, "O-": 7
}
BLOOD_TYPE_DECODE = {v: k for k, v in BLOOD_TYPE_ENCODE.items()}

# Urgency encoding
URGENCY_ENCODE = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}
URGENCY_DECODE = {v: k for k, v in URGENCY_ENCODE.items()}


# ── Packet Dataclass ──────────────────────────────────────────────────────────
@dataclass
class LoRaPacket:
    """
    Compact emergency packet transmitted over LoRa radio.
    Designed to fit within LoRa's 51–222 byte payload limit.

    Fields chosen to represent a complete emergency request with ~90 bytes.
    """
    request_id: str           # 8-char truncated UUID
    patient_id: str           # 8-char truncated UUID
    blood_type: str           # e.g. 'O-'
    city: str                 # max 20 chars
    urgency: str              # LOW / MEDIUM / HIGH / CRITICAL
    timestamp: int            # Unix epoch seconds
    hospital_name: str = ""   # max 30 chars, optional
    units_needed: int = 1     # number of units
    checksum: str = ""        # 4-char CRC for integrity

    def __post_init__(self):
        # Enforce field size limits for radio transmission
        self.request_id = self.request_id[:8]
        self.patient_id = self.patient_id[:8]
        self.city = self.city[:20]
        self.hospital_name = self.hospital_name[:30]
        if not self.checksum:
            self.checksum = self._compute_checksum()

    def _compute_checksum(self) -> str:
        """4-char CRC-like checksum for corruption detection."""
        raw = f"{self.request_id}{self.patient_id}{self.blood_type}{self.city}{self.urgency}{self.timestamp}"
        return hashlib.md5(raw.encode()).hexdigest()[:4]

    def is_valid(self) -> bool:
        """Verify packet integrity after transmission."""
        expected = self._compute_checksum()
        return self.checksum == expected


# ── Encoding / Decoding ───────────────────────────────────────────────────────
def encode_lora_packet(emergency: dict) -> bytes:
    """
    Encode an emergency dict into a compact binary LoRa packet.

    Format (binary struct):
      [1B version][1B blood_type_code][1B urgency_code][1B units]
      [4B timestamp][8B request_id][8B patient_id]
      [1B city_len][N bytes city][1B hospital_len][M bytes hospital]
      [4B checksum]

    This produces ~35–80 bytes depending on city/hospital name length.
    Well within LoRa's minimum 51-byte payload.

    Args:
        emergency: dict with keys matching BloodBridge emergency schema

    Returns:
        bytes — binary encoded packet
    """
    blood_type = emergency.get("blood_type", "O+")
    urgency = emergency.get("urgency_level", emergency.get("urgency", "HIGH"))
    request_id = str(emergency.get("request_id", "LORA0001"))[:8].ljust(8)
    patient_id = str(emergency.get("patient_id", "UNKN0001"))[:8].ljust(8)
    city = str(emergency.get("city", ""))[:20]
    hospital = str(emergency.get("hospital_name", ""))[:30]
    units = int(emergency.get("units_needed", 1))
    timestamp = int(emergency.get("timestamp", time.time()))

    bt_code = BLOOD_TYPE_ENCODE.get(blood_type.upper(), 0)
    urg_code = URGENCY_ENCODE.get(urgency.upper(), 2)

    city_bytes = city.encode("utf-8")
    hosp_bytes = hospital.encode("utf-8")

    # Build binary packet
    header = struct.pack(
        "!BBBBi8s8s",
        LORA_PACKET_VERSION,
        bt_code,
        urg_code,
        min(units, 255),
        timestamp,
        request_id.encode("ascii"),
        patient_id.encode("ascii")
    )

    body = (
        struct.pack("!B", len(city_bytes)) + city_bytes +
        struct.pack("!B", len(hosp_bytes)) + hosp_bytes
    )

    # 4-byte CRC checksum over header+body
    full = header + body
    crc = hashlib.md5(full).digest()[:4]

    return full + crc


def decode_lora_packet(raw: bytes) -> dict:
    """
    Decode a binary LoRa packet back to a BloodBridge emergency dict.

    Args:
        raw: bytes — binary packet from LoRa receiver

    Returns:
        dict with emergency fields, or raises ValueError on corruption

    Raises:
        ValueError: if packet is too short, version mismatch, or CRC fails
    """
    MIN_PACKET_SIZE = 19  # header (19 bytes) + at least 2 length bytes + 4 CRC
    if len(raw) < MIN_PACKET_SIZE + 6:
        raise ValueError(f"Packet too short: {len(raw)} bytes")

    # Separate payload and CRC
    payload = raw[:-4]
    received_crc = raw[-4:]
    computed_crc = hashlib.md5(payload).digest()[:4]

    if received_crc != computed_crc:
        raise ValueError("CRC mismatch — packet corrupted during transmission")

    # Parse header: version(B) + bt_code(B) + urg_code(B) + units(B) + ts(i=int32) + req_id(8s) + pat_id(8s)
    header_size = struct.calcsize("!BBBBi8s8s")
    version, bt_code, urg_code, units, timestamp, req_id_b, pat_id_b = struct.unpack_from(
        "!BBBBi8s8s", payload, 0
    )

    if version != LORA_PACKET_VERSION:
        raise ValueError(f"Unknown packet version: {version}")

    offset = header_size

    # Parse variable-length city
    city_len = payload[offset]
    offset += 1
    city = payload[offset:offset + city_len].decode("utf-8", errors="replace")
    offset += city_len

    # Parse variable-length hospital
    hosp_len = payload[offset]
    offset += 1
    hospital = payload[offset:offset + hosp_len].decode("utf-8", errors="replace")

    return {
        "request_id": req_id_b.decode("ascii").strip(),
        "patient_id": pat_id_b.decode("ascii").strip(),
        "blood_type": BLOOD_TYPE_DECODE.get(bt_code, "O+"),
        "urgency_level": URGENCY_DECODE.get(urg_code, "HIGH"),
        "units_needed": units,
        "timestamp": timestamp,
        "city": city,
        "hospital_name": hospital,
        "source": "lora_offline",
        "packet_version": version,
    }


# ── Simulated Serial Send ─────────────────────────────────────────────────────
def simulate_lora_send(packet: LoRaPacket, serial_port: str = "/dev/ttyS0") -> bool:
    """
    Simulate sending a LoRa packet over serial.

    In production, replace this with:
        import serial
        ser = serial.Serial(serial_port, 9600, timeout=1)
        ser.write(encoded_bytes)
        ser.close()

    Args:
        packet: LoRaPacket to transmit
        serial_port: serial device path (Raspberry Pi default: /dev/ttyS0)

    Returns:
        bool — True if transmission simulated successfully
    """
    try:
        encoded = encode_lora_packet(asdict(packet))
        packet_size = len(encoded)
        logger.info(
            f"[LoRa SIM] Transmitting {packet_size} bytes on {serial_port}: "
            f"emergency={packet.request_id} blood={packet.blood_type} "
            f"urgency={packet.urgency} city={packet.city}"
        )
        # Simulate transmission delay proportional to packet size (LoRa ~250 bps SF12)
        sim_delay = packet_size / 250.0
        logger.debug(f"[LoRa SIM] Simulated air time: {sim_delay:.2f}s")
        return True
    except Exception as e:
        logger.error(f"[LoRa SIM] Transmission failed: {e}")
        return False


# ── SQLite Store-and-Forward Queue ────────────────────────────────────────────
def _init_db() -> sqlite3.Connection:
    """Initialize the SQLite offline queue database."""
    LORA_SQLITE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(LORA_SQLITE_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS lora_queue (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id  TEXT NOT NULL,
            blood_type  TEXT NOT NULL,
            urgency     TEXT NOT NULL,
            city        TEXT NOT NULL,
            packet_json TEXT NOT NULL,
            received_at INTEGER NOT NULL,
            flushed     INTEGER DEFAULT 0,
            flushed_at  INTEGER
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_flushed ON lora_queue (flushed)")
    conn.commit()
    return conn


def store_offline_packet(packet: LoRaPacket) -> bool:
    """
    Store a received LoRa packet to the SQLite offline queue.
    Used when the BloodBridge API is temporarily unreachable.

    Automatically evicts the oldest packets if queue exceeds LORA_MAX_QUEUE_DEPTH.

    Returns:
        bool — True if stored successfully
    """
    try:
        conn = _init_db()
        with conn:
            # Evict oldest unflushed if at capacity
            count = conn.execute("SELECT COUNT(*) FROM lora_queue WHERE flushed=0").fetchone()[0]
            if count >= LORA_MAX_QUEUE_DEPTH:
                # Delete oldest 10%
                evict_n = max(1, LORA_MAX_QUEUE_DEPTH // 10)
                conn.execute(
                    "DELETE FROM lora_queue WHERE id IN "
                    "(SELECT id FROM lora_queue WHERE flushed=0 ORDER BY id ASC LIMIT ?)",
                    (evict_n,)
                )
                logger.warning(f"LoRa queue at capacity. Evicted {evict_n} oldest packets.")

            conn.execute(
                """INSERT INTO lora_queue
                   (request_id, blood_type, urgency, city, packet_json, received_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    packet.request_id,
                    packet.blood_type,
                    packet.urgency,
                    packet.city,
                    json.dumps(asdict(packet)),
                    int(time.time())
                )
            )
        conn.close()
        logger.info(f"LoRa packet {packet.request_id} stored to offline queue.")
        return True
    except Exception as e:
        logger.error(f"Failed to store LoRa packet to SQLite: {e}", exc_info=True)
        return False


def get_queue_depth() -> int:
    """Return number of unprocessed packets in the offline queue."""
    try:
        conn = _init_db()
        count = conn.execute("SELECT COUNT(*) FROM lora_queue WHERE flushed=0").fetchone()[0]
        conn.close()
        return count
    except Exception:
        return -1


async def flush_offline_queue() -> dict:
    """
    Replay all stored offline packets to the BloodBridge REST API.
    Called when connectivity is restored (by the /api/lora/flush endpoint
    or the background connectivity monitor).

    Returns:
        {flushed: int, failed: int, errors: list[str]}
    """
    import httpx
    conn = _init_db()
    rows = conn.execute(
        "SELECT id, packet_json FROM lora_queue WHERE flushed=0 ORDER BY id ASC"
    ).fetchall()

    flushed = 0
    failed = 0
    errors = []

    for row_id, packet_json in rows:
        try:
            packet_dict = json.loads(packet_json)

            # Post to the LoRa receive endpoint
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.post(
                    f"{BLOODBRIDGE_API_BASE}/api/lora/receive",
                    json={
                        "request_id": packet_dict["request_id"],
                        "patient_id": packet_dict["patient_id"],
                        "blood_type": packet_dict["blood_type"],
                        "urgency_level": packet_dict["urgency"],
                        "city": packet_dict["city"],
                        "hospital_name": packet_dict.get("hospital_name", ""),
                        "units_needed": packet_dict.get("units_needed", 1),
                        "source": "lora_offline_replay",
                        "original_timestamp": packet_dict["timestamp"],
                    }
                )
                resp.raise_for_status()

            # Mark as flushed
            conn.execute(
                "UPDATE lora_queue SET flushed=1, flushed_at=? WHERE id=?",
                (int(time.time()), row_id)
            )
            conn.commit()
            flushed += 1
            logger.info(f"Flushed LoRa packet {packet_dict['request_id']} to BloodBridge API.")

        except Exception as e:
            failed += 1
            err = f"Packet row {row_id}: {e}"
            errors.append(err)
            logger.warning(f"Failed to flush LoRa packet: {err}")

    conn.close()
    logger.info(f"LoRa queue flush complete: {flushed} flushed, {failed} failed.")
    return {"flushed": flushed, "failed": failed, "errors": errors}
