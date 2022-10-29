# CPA1110
 Python interface for a Cryomech CPA1110

The Cryomech CPA1110 compressor supports remote monitoring through serial
(RS232/485), as well as ethernet connections, through the Modbus RTU protocol
(for serial) or ModbusTCP (for ethernet).
#### Modbus protocol
The protocol is somewhat peculiar in that it's most often only used to access
(read from or write to) 'registers' on a remote device instead of
sending/receiving more general commands. Moreover,
> Modbus protocol is defined as a master/slave protocol, meaning a device
operating as a master will poll one or more devices operating as a slave. This
means a slave device cannot volunteer information; it must wait to be asked for
it. The master will write data to a slave device's registers, and read data from
a slave device's registers. A register address or register reference is always
in the context of the slave's registers.
[[source]](https://www.csimn.com/CSI_pages/Modbus101.html)
To speed things up, I provide one command for reading out all the registers at
once; most of the other functions merely decode the registers into
human-readable data.
There are various kinds of registers defined by the Modbus standard, but the
CPA1110 only uses two kinds, namely Input and Holding Registers. The registers
used are the following [CPAxxxx Digital Panel User Manual]:
    30,001 - Operating State	
    30,002 - Compressor Running 
    30,003 - Warning State 
    30,004 - Errors
    30,005 - Alarm State 
    30,007 - Coolant In Temp 
    30,009 - Coolant Out Temp 
    30,011 - Oil Temp 
    30,013 - Helium Temp 
    30,015 - Low Pressure 
    30,017 - Low Pressure Average 
    30,019 - High Pressure 
    30,021 - High Pressure Average 
    30,023 - Delta Pressure Average 
    30,025 - Motor Current 
    30,027 - Hours Of Operation 
    30,029 - Pressure Scale 
    30,030 - Temp Scale 
    30,031 - Panel Serial Number 
    30,032 - Model Major + Minor numbers  
    30,033 - Software Rev  
    40,001 - Enable / Disable the compressor
"Modbus protocol defines a holding register as 16 bits wide; however, there is a
widely used defacto standard for reading and writing data wider than 16 bits."
[[source]](https://www.csimn.com/CSI_pages/Modbus101.html) "The first two
'Input' registers and the only 'Holding' register are 16 bit integer registers
and the rest of the input registers are in 32bit floating point format."
[CPAxxxx Digital Panel User Manual]