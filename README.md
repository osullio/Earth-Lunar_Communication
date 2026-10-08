# Earth–Moon Rover Communication (Computer Networks Project – Group 7)

A client/server system that simulates communication between a ground station on Earth and a lunar rover. The client (Earth) sends commands and requests. The server (the rover) replies with messages, temperature data, movement confirmations and status reports. The link is deliberately made unreliable: packets are delayed by the Earth–Moon light-travel time and can have bits flipped in transit. A custom header with a checksum and an ACK flag is used to detect errors and recover from them.

The project was prototyped in two languages:

| Implementation | Location | State |
|---|---|---|
| **C/C++ (Winsock)** | `C code/` | Early prototype: a minimal TCP echo client/server, used to prove out socket setup |
| **Python** | `Python code/` | **Main solution**: custom header, checksum, error simulation, retransmission, multiple services, multithreaded server |

The rest of this document covers the Python implementation unless stated otherwise.

---

## Repository layout

```
C code/
  server_tcp.c      Winsock TCP server: accepts one client, echoes one message back
  client_tcp.c      Winsock TCP client: sends one line of input, prints the reply
Python code/
  server.py         Rover-side server (multithreaded, one thread per client)
  client.py         Earth-side interactive client
  responses.py      Canned rover responses (greetings, temperature logs, movement, status)
```

---

## Running it

### Python (main solution)

Requires Python 3 (developed on 3.12). Only the standard library is used.

1. Set the server's IP address. `SERVER` is hard-coded in **both** `server.py` and `client.py` (currently `10.6.141.128`). Change it to the machine that runs the server, or to `127.0.0.1` for a local test.
2. Start the server:
   ```
   cd "Python code"
   python server.py
   ```
3. Start the client in another terminal or on another machine:
   ```
   cd "Python code"
   python client.py
   ```
4. Choose a service from the menu, then type messages. Type `!DISCONNECT` to end the session.

### C/C++ prototype

Windows only (it uses Winsock2). The server listens on port 5050. The client connects to a hard-coded IP (`192.168.0.171`), so edit that address first.

```
gcc "C code/server_tcp.c" -o server -lws2_32
gcc "C code/client_tcp.c" -o client -lws2_32
```
With MSVC (`cl`), the `#pragma comment(lib, "ws2_32.lib")` line links the library automatically.

---

## How it works

### Services are selected by source port

The client binds its socket to a specific **source port** before it connects. The server checks the client's port to decide which service it is talking to:

| Menu option | Client port | Service | Server response |
|---|---|---|---|
| 1 | 5051 | Messaging | Random greeting |
| 2 | 5052 | Temperature | A temperature log in CSV format |
| 3 | 5053 | Movement | `w` forward, `s` backward, `a` left, `d` right, space stops; anything else stops the rover as an invalid control |
| 4 | 5054 | Status | A rover status report |

The server listens on port **5050**. A connection from any other port is rejected and closed.

### Custom packet header (24 bytes)

Each message is sent as a hand-built header followed by a UTF-8 payload. The layout is modelled on the TCP header and is built byte by byte in `create_header()`:

| Bytes | Field | Use in this project |
|---|---|---|
| 0–1 | Source port | Sender's port |
| 2–3 | Destination port | Receiver's port |
| 4–7 | Sequence number | Always `1000` (not used) |
| 8–11 | ACK number | Always `0` (not used) |
| 12 | Header length (4 bits) + unused | Set to 5 |
| 13 | Unused (2 bits) + flags (6 bits) | **ACK flag** (`0x10`): 1 = OK/new data, 0 = "please resend" |
| 14–15 | Receive window | Always 65535 (not used) |
| 16–17 | Checksum | 16-bit one's-complement checksum over header + payload |
| 18–19 | Urgent pointer | Always 0 (not used) |
| 20–23 | Option | **Payload length in bytes**, so the receiver knows how much to read |

The receiver reads exactly 24 bytes, gets the payload length from the option field, and then reads exactly that many bytes (`recv_expected()`). This handles TCP's stream nature without relying on delimiters.

### Error detection

`calculate_checksum()` uses the Internet checksum: data is summed in 16-bit words, carries are wrapped around, and the result is inverted. The receiver runs the same checksum over the received header and payload. A result of `0` means the packet arrived intact.

### Simulated channel impairments

- **Bit errors:** each send has a 10% chance of going through `flip_bits()`, which flips each bit of the packet with 1% probability.
- **Propagation delay:** the server sleeps for `distance / speed_of_light` with ±5% jitter before sending. This is about 1.36 s at the maximum Earth–Moon distance. The client uses fixed sleeps instead.

### Reliability (stop-and-wait with ACK/NAK)

The protocol is stop-and-wait. One message is outstanding at a time, and the ACK flag is used as an ACK/NAK:

1. The client sends a request with ACK=1 and keeps a copy as `last_packet`.
2. The receiver checks the checksum:
   - **Valid, ACK=1:** the data is processed and a response is sent.
   - **Valid, ACK=0:** the peer is asking for a retransmission, so `last_packet` is resent.
   - **Invalid:** an "Error Received" packet with ACK=0 is sent back, asking the peer to resend.
3. On a timeout, the client resends its last packet.
4. The server drops a client after more than 10 consecutive corrupted packets.

### Concurrency and disconnect

- The server creates a new thread for each accepted connection (`threading.Thread`), so several clients can be served at once.
- When the client sends `!DISCONNECT`, the server echoes it back with ACK=1, waits 3 s so the reply can arrive, and closes the connection. When the client receives the echo, it closes its end.

---

## Pros

- **Hand-built binary header.** Every field is packed manually with bit shifts. This shows how a real header is laid out on the wire, without hiding it behind `struct`.
- **Length-prefixed framing.** Putting the payload length in the header and reading exact byte counts handles partial `recv()` calls correctly. Many simple socket projects get this wrong.
- **Real checksum algorithm.** It is the same one's-complement algorithm used by IP, TCP and UDP, and it verifies to zero.
- **Error and latency injection.** Bit flips and light-speed delay make the recovery logic actually run, instead of relying on a perfect localhost link.
- **Working ACK/NAK recovery** for the common case: a corrupted packet in either direction triggers a resend.
- **Multithreaded server.** Several ground stations can connect at the same time.
- **Clear separation of content.** Rover responses are kept in `responses.py`, apart from the protocol logic.
- **Two-language prototyping.** The C version confirmed the basic socket flow (bind, listen, accept, send/recv) at a lower level before the fuller Python build.

## Cons and known limitations

The project works for the demo scenario but has rough edges.

**Protocol design**
- **It runs on top of real TCP.** The OS already guarantees ordered, error-free delivery, so the bit errors are introduced at the application layer and the custom header is effectively an application protocol, not a replacement transport. A UDP-based version would have been a more honest test of the reliability scheme.
- **Sequence and ACK numbers are unused** (fixed at 1000 and 0). Without them, a duplicate packet cannot be told apart from a new one. Resent requests may be processed twice, and a stale reply may be accepted.
- **The length field is not protected before it is used.** If a bit flip corrupts the option field, the receiver reads the wrong number of bytes before checking the checksum. It can then block until the timeout or read part of the next message, which desynchronises the stream.
- **The header length field says 5 words (20 bytes)** but the header is actually 24 bytes.
- **Stop-and-wait only:** no pipelining or sliding window, so throughput is poor at high latency. That matters a lot on an Earth–Moon link.
- **Services are identified by fixed client source ports.** Only one client per service can run on each machine. Restarting quickly can fail with "address already in use" because of TCP `TIME_WAIT`. The client also cannot change service without reconnecting.

**Bugs found in the current code**
- `client.py`: `CURRENT_EARTH_MOON_DISTANCE = 381, 550, 000` creates a tuple, not a number. `calculate_delay()` would crash if it were called. It isn't called at present: the client uses fixed `time.sleep()` calls instead.
- `client.py`: after a timeout and resend, execution falls through to the checksum on `"TIMEOUT" + None`, which raises a `TypeError`.
- `client.py`: it checks for `"connectionclose"`, but `recv_expected()` returns `"CONNECTION CLOSED"`. This currently only works because the `else: break` branch catches it.
- `server.py`: on a timeout, the server closes the socket and then `continue`s, so it keeps looping on a closed socket instead of exiting the thread.
- `server.py`: `conn.close` is missing its parentheses in the error-limit branch, so the socket is never actually closed there.
- `server.py`: if a valid ACK=0 packet arrives before anything has been sent, `last_packet` is `None` and the send fails.
- `client.py`: Ctrl+C triggers `time.sleep(700)` before shutting down.

**Practicality**
- Server IP addresses are hard-coded in the source rather than passed as arguments or read from config.
- The many fixed `sleep()` calls (2 s, 3 s, 7 s, 10 s) make the system slow, and they add delay on top of the simulated light-speed delay.
- There are no automated tests. Behaviour was checked by running the programs by hand.
- The C prototype is Windows-only, does not check return values, and handles a single message from a single client.

## Possible improvements

- Move to UDP and use the sequence/ACK fields properly (alternating-bit or Go-Back-N).
- Add a separate header checksum, or validate the length before reading the payload.
- Choose the service with a field in the header instead of the source port.
- Read the IP and port from command-line arguments.
- Fix the bugs listed above and add unit tests for `create_header`, `calculate_checksum` and `flip_bits`.
