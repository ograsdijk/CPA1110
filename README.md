# CPA1110
 Python interface for a Cryomech CPA1110

The Cryomech CPA1110 compressor supports remote monitoring through serial
(RS232/485), as well as ethernet connections, through the Modbus RTU protocol
(for serial) or ModbusTCP (for ethernet).

## Example
```Python
from cpa1110 import CPA1110, Connection

compressor = CPA1110("192.168.1.10", connection_type = Connection.TCP)

# read the coolant in/out temperatures
temp_in = compressor.CoolantInTemperature
temp_out = compressor.CoolantOutTemperature

# start the compressor
compressor.enable_compressor()

# stop the compressor
compressor.disable_compressor()
```


## Modbus protocol
There are various kinds of registers defined by the Modbus standard, but the
CPA1110 only uses two kinds, namely Input and Holding Registers. The registers
used are the following [CPAxxxx Digital Panel User Manual]:
* 30,001 - Operating State	
* 30,002 - Compressor Running  
* 30,003 - Warning State  
* 30,004 - Errors  
* 30,005 - Alarm State  
* 30,007 - Coolant In Temp  
* 30,009 - Coolant Out Temp  
* 30,011 - Oil Temp  
* 30,013 - Helium Temp  
* 30,015 - Low Pressure  
* 30,017 - Low Pressure Average   
* 30,019 - High Pressure  
* 30,021 - High Pressure Average  
* 30,023 - Delta Pressure Average  
* 30,025 - Motor Current  
* 30,027 - Hours Of Operation  
* 30,029 - Pressure Scale  
* 30,030 - Temp Scale  
* 30,031 - Panel Serial Number  
* 30,032 - Model Major + Minor numbers    
* 30,033 - Software Rev   
* 40,001 - Enable / Disable the compressor  


"Modbus protocol defines a holding register as 16 bits wide; however, there is a
widely used defacto standard for reading and writing data wider than 16 bits."
[[source]](https://www.csimn.com/CSI_pages/Modbus101.html) "The first two
'Input' registers and the only 'Holding' register are 16 bit integer registers
and the rest of the input registers are in 32bit floating point format."
[CPAxxxx Digital Panel User Manual]