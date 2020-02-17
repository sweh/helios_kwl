from helios_com import COM

com = COM('10.0.1.64')
try:
    fanLevel = com.read_fan_stage()
    outTemp, suppTemp, exhaustTemp, extractTemp = com.read_temp()
    exhaustHumid = com.read_humidity()
finally:
    com.exit()

print(f"Lüfterstufe: {fanLevel}")
print(f"Außenluft: {outTemp} °C")
print(f"Zuluft: {suppTemp} °C")
print(f"Abluft: {extractTemp} °C / {exhaustHumid} %")
print(f"Fortluft: {exhaustTemp} °C")
