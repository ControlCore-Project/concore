"""Tests for the SHM race condition (issue #195).

Layout used by the C++ fix in concore.hpp / concoredocker.hpp:
    bytes [0..7]   : uint64_t little-endian sequence number
                     (odd = write in progress, even = ready, 0 = none)
    bytes [8..end] : null-terminated payload
Concurrent writers serialise via a POSIX semaphore (one per segment);
readers double-read the seq# to confirm a stable snapshot.
"""

from __future__ import annotations

import multiprocessing as mp
import os
import struct
import time
from multiprocessing import shared_memory
from pathlib import Path

import pytest

SHM_TOTAL_SIZE = 4096
SHM_HEADER_SIZE = 8
SHM_PAYLOAD_SIZE = SHM_TOTAL_SIZE - SHM_HEADER_SIZE - 1
SHM_NAME_PREFIX = "concore_shm_test_"

_HEADER_FMT = "<Q"


def _encode_payload(payload: str) -> bytes:
    payload_bytes = payload.encode("utf-8")[:SHM_PAYLOAD_SIZE]
    return payload_bytes + b"\x00"


def _decode(data: bytes) -> tuple[int, str]:
    seq = struct.unpack(_HEADER_FMT, data[:SHM_HEADER_SIZE])[0]
    payload = (
        data[SHM_HEADER_SIZE:].split(b"\x00", 1)[0].decode("utf-8", errors="replace")
    )
    return seq, payload


def _writer_safe(shm_name: str, lock_path: str, iterations: int) -> int:
    shm = shared_memory.SharedMemory(name=shm_name)
    fd = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o600)
    import fcntl

    fcntl.flock(fd, fcntl.LOCK_EX)
    try:
        for i in range(iterations):
            payload = f"safe_{i}_" + ("Y" * 200)
            body = _encode_payload(payload)
            shm.buf[SHM_HEADER_SIZE : SHM_HEADER_SIZE + len(body)] = body
            shm.buf[:SHM_HEADER_SIZE] = struct.pack(_HEADER_FMT, (i + 1) * 2)
    finally:
        try:
            os.close(fd)
        except OSError:
            pass
    shm.close()
    return 0


def _writer_unsafe(shm_name: str, lock_path: str, iterations: int) -> int:
    # Reference "broken" writer: no lock, no seqlock protocol. Writes
    # payload first then bumps seq, leaving the seq UNCHANGED across a
    # tearing window.
    shm = shared_memory.SharedMemory(name=shm_name)
    for i in range(iterations):
        payload = f"unsafe_{i}_" + ("X" * 200)
        body = _encode_payload(payload)
        # Without a seqlock, a reader may catch the writer mid-update.
        # We deliberately do payload-write THEN seq-bump; in C++ with
        # raw strncpy the bytes get interleaved.
        shm.buf[SHM_HEADER_SIZE : SHM_HEADER_SIZE + len(body)] = body
        shm.buf[:SHM_HEADER_SIZE] = struct.pack(_HEADER_FMT, (i + 1) * 2)
    shm.close()
    return 0


def _reader_verify(
    shm_name: str, lock_path: str, iterations: int
) -> tuple[int, int, int]:
    shm = shared_memory.SharedMemory(name=shm_name)
    accepted = 0
    torn = 0
    missing = 0
    last_seq = 0
    # Writers in this test always pad payloads with a known 200-byte
    # suffix. A torn read produces a payload that does not end in the
    # suffix (because the writer's memcpy was caught mid-byte).
    valid_suffixes = ("X" * 200, "Y" * 200, "Z" * 50)
    for _ in range(iterations):
        deadline = time.monotonic() + 2.0
        while time.monotonic() < deadline:
            snap1 = bytes(shm.buf[: SHM_HEADER_SIZE + SHM_PAYLOAD_SIZE + 1])
            snap2 = bytes(shm.buf[: SHM_HEADER_SIZE + SHM_PAYLOAD_SIZE + 1])
            if snap1 != snap2:
                continue
            seq, payload = _decode(snap1)
            if seq == last_seq:
                continue
            if seq % 2 != 0:
                continue
            if not payload.endswith(valid_suffixes):
                torn += 1
                continue
            accepted += 1
            last_seq = seq
            break
        else:
            missing += 1
    shm.close()
    return accepted, torn, missing


@pytest.fixture
def shm_region(tmp_path):
    import uuid

    name = SHM_NAME_PREFIX + uuid.uuid4().hex[:8]
    shm = shared_memory.SharedMemory(name=name, create=True, size=SHM_TOTAL_SIZE)
    lock_path = str(tmp_path / (name + ".lock"))
    Path(lock_path).touch()
    try:
        yield name, lock_path
    finally:
        try:
            shm.close()
            shm.unlink()
        except FileNotFoundError:
            pass
        try:
            os.unlink(lock_path)
        except FileNotFoundError:
            pass


def test_layout_constants_match_header():
    assert SHM_TOTAL_SIZE == 4096
    assert SHM_HEADER_SIZE == 8


@pytest.mark.skipif(os.name != "posix", reason="fork-based concurrency test")
def test_safe_writer_reader_roundtrip(shm_region):
    name, lock_path = shm_region
    iterations = 200
    ctx = mp.get_context("fork")
    with ctx.Pool(2) as pool:
        writer_async = pool.apply_async(_writer_safe, (name, lock_path, iterations))
        reader_async = pool.apply_async(
            _reader_verify, (name, lock_path, iterations * 4)
        )
        writer_async.get(timeout=30)
        accepted, torn, missing = reader_async.get(timeout=30)

    assert torn == 0, f"reader observed {torn} torn reads; SHM is still racy"
    assert accepted >= iterations, (
        f"reader accepted only {accepted}/{iterations} payloads"
    )


@pytest.mark.skipif(os.name != "posix", reason="fork-based concurrency test")
def test_unsafe_writer_produces_torn_reads(shm_region):
    name, lock_path = shm_region
    iterations = 500
    ctx = mp.get_context("fork")
    with ctx.Pool(2) as pool:
        writer_async = pool.apply_async(_writer_unsafe, (name, lock_path, iterations))
        reader_async = pool.apply_async(
            _reader_verify, (name, lock_path, iterations * 4)
        )
        writer_async.get(timeout=30)
        accepted, torn, missing = reader_async.get(timeout=30)

    if torn == 0:
        pytest.skip("unsafe writer did not produce torn reads on this host")
    assert torn > 0


def test_layout_invariants_without_concurrency(shm_region):
    name, _lock = shm_region
    shm = shared_memory.SharedMemory(name=name)

    last_seq = 0
    for i in range(100):
        payload = f"sync_{i}_" + ("Z" * 50)
        body = _encode_payload(payload)
        shm.buf[SHM_HEADER_SIZE : SHM_HEADER_SIZE + len(body)] = body
        shm.buf[:SHM_HEADER_SIZE] = struct.pack(_HEADER_FMT, (i + 1) * 2)

        snap = bytes(shm.buf[: SHM_HEADER_SIZE + len(body) + 1])
        seq, decoded = _decode(snap)

        assert seq == (i + 1) * 2
        assert seq > last_seq
        assert decoded == payload
        last_seq = seq

    shm.close()


def test_decode_rejects_odd_seq(shm_region):
    name, _lock = shm_region
    shm = shared_memory.SharedMemory(name=name)
    shm.buf[:SHM_HEADER_SIZE] = struct.pack(_HEADER_FMT, 7)
    shm.buf[SHM_HEADER_SIZE : SHM_HEADER_SIZE + 5] = b"hello"
    snap = bytes(shm.buf[: SHM_HEADER_SIZE + 6])
    seq, _payload = _decode(snap)
    assert seq == 7
    assert seq % 2 != 0, "seq# must be odd during a write"
    shm.close()
