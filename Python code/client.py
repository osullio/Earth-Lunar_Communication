import socket
import time
import random

# Add something to check for version in the header
# all length is in bit
HEADER = 192  # This is the total fixed header size
SOURCE_PORT = 16  # bit length of the source port (16)
DEST_PORT = 16  # bit length of the dest port (16)
SEQUENCE_LENGTH = 32  # bit length of the sequence number
ACK_NUM_LENGTH = 32  # bit length of the ACK number
HEADER_LENGTH = 4  # bit length of the header length data segment
UNUSED_LENGTH = 6  # bit length of the unused data segment
FLAGS_LENGTH = 6  # bit length of the flags data segment
REC_WIN_LENGTH = 16  # bit length of the receive window
CHECKSUM_LENGTH = 16  # bit length of the checksum
URG_DATA_POINT = 16  # bit length of the urgent data pointer
OPTION = 32  # bit length for the option

SERVER = "10.6.141.128"  # Server IP address
FORMAT = 'utf-8'  # Encoding format
DISCONNECT_MESSAGE = "!DISCONNECT"  # Disconnect message
TIMEOUT_MSG = "TIMEOUT"
CONN_CLOSE = "CONNECTION CLOSED"

SERVER_PORT = 5050  # Server port
MESSAGE_PORT = 5051  # Client message port
TEMPERATURE_PORT = 5052  # Client temperature request port
MOVE_PORT = 5053  # Client movement request port
STATUS_PORT = 5054  # Client status request port

CURRENT_EARTH_MOON_DISTANCE = 381, 550, 000
LIGHT_SPEED = 299792458  # Speed of light in meters per second

FLAGSACK1 = 16  # 010000
FLAGSACK0 = 0  # 000000


def calculate_delay(jitter=0.05):
    """
    Calculate the one-way delay for signals between Earth and Moon

    Parameters:
    - distance: Optional specific distance in meters. If None, uses average distance
    - jitter: Random variation (as percentage) to simulate atmospheric effects

    Returns:
    - Delay time in seconds
    """

    distance = CURRENT_EARTH_MOON_DISTANCE

    # Calculate base delay (distance / speed of light)
    base_delay = distance / LIGHT_SPEED

    # Add random jitter to simulate atmospheric effects and other variations
    jitter_amount = base_delay * jitter * random.uniform(-1, 1)
    total_delay = base_delay + jitter_amount

    return total_delay


# function to simulate flipped bits
def flip_bits(message_bytes, error_rate=0.01):
    """
    Randomly flips bits in the message with the given error rate.

    Args:
        message (bytes): The original message bytes
        error_rate (float): Probability of each bit being flipped (0.0-1.0)

    Returns:
        bytes: Modified header with some bits flipped
    """
    # Convert bytes to bytearray so we can modify it
    message_bytes_array = bytearray(message_bytes)

    for i in range(len(message_bytes_array)):
        # For each byte, check each of the 8 bits
        for bit_position in range(8):
            # Generate random number and compare with error rate
            if random.random() < error_rate:
                # Flip the bit at this position using XOR
                message_bytes_array[i] ^= (1 << bit_position)

    # print(f"[BITS FLIPPED IN HEADER]")
    time.sleep(3)
    return bytes(message_bytes_array)


# Function to calculate a simple checksum
def calculate_checksum(data):
    """Calculate a simple 16-bit checksum for the provided data"""

    # adding an extra byte if the total length is odd
    # as data length might vary
    # fill with a byte with 0 at end
    if (len(data) % 2) != 0:
        data += b'\x00'

    # initialising checksum as 0
    checksum = 0

    # adding every 16 bits(2 bytes)
    # if a carryout wrap to the end
    for i in range(0, len(data), 2):
        # get the integer value of next 16 bit
        next_16_bit = (data[i] << 8)
        next_16_bit += data[i + 1]
        checksum += next_16_bit
        # adding the 17-bit
        bit_17 = (checksum >> 16)
        checksum = (checksum & 0xFFFF)  # to align with 16 bits
        checksum += bit_17

    # One's complement (invert the bits)
    # need to cut down to 16 bits as
    # python integer has no limitation on bits
    return ((~checksum) & 0xFFFF)


# function to read and print the header file
# need to decide what to return
def read_header(conn):
    time.sleep(7)
    header = recv_expected(conn, HEADER // 8)

    return header


# function for encoding data
def encode_data(data_string):
    data_encode = data_string.encode(FORMAT)
    return data_encode


# function for decoding data
def decode_data(data_bytes):
    data_decode = data_bytes.decode(FORMAT)
    return data_decode


# function for recieve message in expected length
def recv_expected(conn, msg_length):
    # a space data collection
    data = b''
    conn.settimeout(30)  # set timeout to 5 seconds

    # timeout after secs
    while ((len(data) < msg_length)):
        # recieve end when length reach the expected value
        try:
            new_data = conn.recv(msg_length - len(data))

        except socket.timeout:
            print("[ERROR] Time out")
            return TIMEOUT_MSG

        except Exception:
            print("[ERROR] Exception occurred")
            conn.close()
            return TIMEOUT_MSG

        if (not new_data):
            print("[ERROR] Closed connection")
            conn.close()
            return CONN_CLOSE

        data += new_data
    return data


# Function to manually create a TCP header without using struct
# option used for storing the length of data transmitted after header
def create_header(source_port, dest_port, seq_num=0, ack_num=0, checksum=0, window_size=65535, urgent_ptr=0,
                  header_length=5, unused=0, flags=0, option=0):
    """
    Manually create a TCP header by concatenating byte representations of each field

    Parameters:
    - source_port: 16-bit source port
    - dest_port: 16-bit destination port
    - seq_num: 32-bit sequence number
    - ack_num: 32-bit acknowledgment number
    - checksum: 16-bit checksum
    - window_size: 16-bit receive window size
    - urgent_ptr: 16-bit urgent pointer
    - header_length: 4-bit header length (in 32-bit words)
    - unused: 4-bit reserved field
    - flags: 8-bit flags field

    Returns:
    - bytes object containing the binary TCP header
    """
    header = bytearray(HEADER // 8)  # Create a byte array of the right size (20 bytes)

    # Source port (bytes 0-1)
    header[0] = (source_port >> 8) & 0xFF  # High byte
    header[1] = source_port & 0xFF  # Low byte

    # Destination port (bytes 2-3)
    header[2] = (dest_port >> 8) & 0xFF  # High byte
    header[3] = dest_port & 0xFF  # Low byte

    # Sequence number (bytes 4-7)
    header[4] = (seq_num >> 24) & 0xFF  # Highest byte
    header[5] = (seq_num >> 16) & 0xFF
    header[6] = (seq_num >> 8) & 0xFF
    header[7] = seq_num & 0xFF  # Lowest byte

    # Acknowledgment number (bytes 8-11)
    header[8] = (ack_num >> 24) & 0xFF  # Highest byte
    header[9] = (ack_num >> 16) & 0xFF
    header[10] = (ack_num >> 8) & 0xFF
    header[11] = ack_num & 0xFF  # Lowest byte

    # first 4 bits header_length last 4 bit unused(highest 4 bits of unused)
    header[12] = ((header_length & 0x0F) << 4) | (unused & 0xF0)

    # first 2 bits unused(lowest 2 bit of unused) last 6 bit flags
    header[13] = ((unused & 0x03) << 6) | (flags & 0x3F)

    # Window size (bytes 14-15)
    header[14] = (window_size >> 8) & 0xFF  # High byte
    header[15] = window_size & 0xFF  # Low byte

    # Checksum (bytes 16-17)
    header[16] = (checksum >> 8) & 0xFF  # High byte
    header[17] = checksum & 0xFF  # Low byte

    # Urgent pointer (bytes 18-19)
    header[18] = (urgent_ptr >> 8) & 0xFF  # High byte
    header[19] = urgent_ptr & 0xFF  # Low byte

    # Option (bytes 20-23)
    header[20] = (option >> 24) & 0xFF
    header[21] = (option >> 16) & 0xFF
    header[22] = (option >> 8) & 0xFF
    header[23] = option & 0xFF

    return bytes(header)


def create_packet(client_port, ack, data_byte):
    # Create initial values for the header
    source_port = client_port
    dest_port = SERVER_PORT  # the server port
    seq_num = 1000  # Initial sequence number
    ack_num = 0  # Initial ACK number
    window_size = 65535  # Default window size

    flags = FLAGSACK0  # initial ACK 0
    if (ack == 1):  # if packet recieve and ack need to set is 1
        flags = FLAGSACK1

    option = len(data_byte)  # return length of the data in integer

    # Create a placeholder header for checksum calculation
    temp_header = create_header(
        source_port, dest_port, seq_num, ack_num,
        checksum=0, window_size=window_size, flags=flags, option=option
    )

    # Calculate checksum using the placeholder header
    checksum = calculate_checksum(temp_header + data_byte)

    # Create the final header with the calculated checksum
    header = create_header(
        source_port, dest_port, seq_num, ack_num,
        checksum=checksum, window_size=window_size, flags=flags,
        option=option
    )

    # new packet
    new_packet = header + data_byte

    return new_packet


# Function to prompt the user for a source port
def get_source_port():
    print("[MESSAGE] Welcome to group 7's Networks Project")
    print("[MESSAGE] Press 1 to send a message to the server")
    print("[MESSAGE] Press 2 to receive temperature data from the moon")
    print("[MESSAGE] Press 3 to move the buggy")
    print("[MESSAGE] Press 4 to receive a status update")
    user_input = input("[INPUT]: ")
    print("\n")

    if user_input == "1":
        return MESSAGE_PORT
    elif user_input == "2":
        return TEMPERATURE_PORT
    elif user_input == "3":
        return MOVE_PORT
    elif user_input == "4":
        return STATUS_PORT
    else:
        return -1


# Function to establish connection and send the initial header
def start_client():
    client_port = get_source_port()
    if client_port == -1:
        print("[ERROR] Invalid selection. Exiting...")
        return None, None

    # Create a socket
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.bind(("", client_port))  # Bind to the selected port

    print(f"[CONNECTING] Connecting to {SERVER}:{SERVER_PORT}...")
    try:
        client.connect((SERVER, SERVER_PORT))
        print(f"[CONNECTED] Connected to server at {SERVER}:{SERVER_PORT}")
        return client, client_port
    except Exception as e:
        print(f"[ERROR] Failed to connect: {e}")
        return None, None


# send data
def send_data(client, message_bytes):
    try:
        # Determine what kind of transmission to simulate
        transmission_type = random.random()

        if transmission_type < 0.1:  # 10% chance of flip bits
            msg_final = flip_bits(message_bytes)
            print(f"[BITS FLIPPED]")
        else:  # Normal transmission
            msg_final = message_bytes
            print(f"[HEADER SENT CORRECTLY]")

        time.sleep(2)

        client.send(msg_final)
        return True
    except Exception as e:
        print("close connection")
        client.close()
        return False


# handle the recieve message first time
def handle_server(client, client_port):
    # create the packet for ack0
    ack0_response = "Error Recieved"
    ack0_response_bytes = encode_data(ack0_response)
    ack0_response_packet = create_packet(client_port, 0, ack0_response_bytes)

    # store the last packet
    # if none means first time
    last_packet = None

    # variable for send next message
    send_next_msg = True

    while True:

        # send next message
        if (send_next_msg):
            # required the input for first time
            message = input("Enter message (or '!DISCONNECT' to exit): ")
            message_bytes = encode_data(message)
            message_packet = create_packet(client_port, 1, message_bytes)
            last_packet = message_packet
            # if the connection is lost
            if (not send_data(client, message_packet)):
                return
            # set the send_next_msg to false until get the required data
            send_next_msg = False

        # read the header
        data_read_bytes = None  # initial for recording the data
        header_read_bytes = read_header(client)

        if (isinstance(header_read_bytes, bytes)):
            option = header_read_bytes[20:24]  # get the option from header
            data_length = int.from_bytes(option, byteorder='big')  # read the integer in option
            data_read_bytes = recv_expected(client, data_length)  # temp to get 1024 bytes


        elif (header_read_bytes == TIMEOUT_MSG):
            if last_packet:  # if there is a last sent packet
                # if the connection is lost
                if (not send_data(client, last_packet)):
                    break
                print("[UPDATE] Resending the packet")
            # continue  # if timeout go to the starts of loop again
        elif (header_read_bytes == "connectionclose"):
            print("[URGENT] Close the connection")
            break  # exit the handle client as connection is closed
        else:
            break  # safe statement

        # since this will negate on the sum again
        # it should be expected as 0x0000 instead of 0xFFFF
        check_errors = calculate_checksum(header_read_bytes + data_read_bytes)

        # get the ack which is the 4th bit in byte 13
        ack_get_int = (header_read_bytes[13] & 0x10)

        # if no error and ack is 1
        if ((check_errors == 0) and (ack_get_int == FLAGSACK1)):
            # if no errors read the data
            print("[UPDATE] Recieved data has no error.")
            data_read = decode_data(data_read_bytes)
            if (data_read == DISCONNECT_MESSAGE):
                # if the disconnection message recieved
                # means server already recieved that and should close automatically
                print("[MESSAGE RECEIVED] Disconnect recieved.")
                client.close()
                print("[CLOSED CONNECTION]")
                break
            else:
                # the message recieved correctly
                print("[MESSAGE]:")
                print(f"{data_read}")

                # set for waiting for another input
                send_next_msg = True
                continue

        elif ((check_errors == 0) and (ack_get_int == FLAGSACK0)):
            # if the packet is correct but ack is 0
            # means lask packet need to be resent
            if (not send_data(client, last_packet)):
                break
            print("[UPDATE] Resending the packet")
            time.sleep(3)

        else:
            # if the error is detected
            # send a packet with ack 0
            print("[ERROR] Recieved data has errors.")

            # send the packet
            if (not send_data(client, ack0_response_packet)):
                break
            print("Send an packet with ack0 sent")

            continue


# Main client loop
def main():
    client, clinet_port = start_client()
    if not client:
        print("[FAILED] Could not establish connection")
        return
    try:
        handle_server(client, clinet_port)
    except KeyboardInterrupt:
        print("\n[INTERRUPTED] Client shutting down...")
        time.sleep(700)
    except Exception as e:
        print(f"[ERROR] An error occurred: {e}")
    finally:
        client.close()
        print("[DISCONNECTED] Connection closed")


if __name__ == "__main__":
    main()
