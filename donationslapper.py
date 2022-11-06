# micropython script for the esp8266
# chosen wiring:
# boardmark  L293Dpin    cpu
# d1         en          5
# d3         1a          0
# d5         2a          14

d1 = machine.Pin(5, machine.Pin.OUT)
d3 = machine.Pin(0, machine.Pin.OUT)
d5 = machine.Pin(14, machine.Pin.OUT)


def motor(t, is_forward=True):
    global d1, d3, d5
    if is_forward:
        d3.on()
        d5.off()
    else:
        d3.off()
        d5.on()
    d1.on()

    machine.sleep(round(t * 1000))
    d1.off()


def slap():
    motor(2.0)
    motor(0.5, False)
    d1.off()


slap()
