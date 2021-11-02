import pyvisa
rm = pyvisa.ResourceManager('@py')
print('PyVISA Resources Found:')
print("   " + "\n   ".join(rm.list_resources()))
resource = 'USB0::0x1AB1::0x0E11::DP8B153600499::INSTR'
print('opening resource: ' + resource)
inst = rm.open_resource(resource)
print(inst.query("*IDN?"))
