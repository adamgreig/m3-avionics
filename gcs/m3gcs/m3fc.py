from .packets import register_packet, register_command
import struct
from math import sqrt


def msg_id(x):
    return x << 5


CAN_ID_M3FC = 1
CAN_MSG_ID_M3FC_STATUS = CAN_ID_M3FC | msg_id(0)
CAN_MSG_ID_M3FC_MISSION_STATE = CAN_ID_M3FC | msg_id(32)
CAN_MSG_ID_M3FC_ACCEL = CAN_ID_M3FC | msg_id(48)
CAN_MSG_ID_M3FC_BARO = CAN_ID_M3FC | msg_id(49)
CAN_MSG_ID_M3FC_SE_T_H = CAN_ID_M3FC | msg_id(50)
CAN_MSG_ID_M3FC_SE_V_A = CAN_ID_M3FC | msg_id(51)
CAN_MSG_ID_M3FC_SE_VAR_H = CAN_ID_M3FC | msg_id(52)
CAN_MSG_ID_M3FC_SE_VAR_V_A = CAN_ID_M3FC | msg_id(53)
CAN_MSG_ID_M3FC_CFG_PROFILE = CAN_ID_M3FC | msg_id(54)
CAN_MSG_ID_M3FC_CFG_PYROS = CAN_ID_M3FC | msg_id(55)
CAN_MSG_ID_M3FC_CFG_ACCEL_CAL_X = CAN_ID_M3FC | msg_id(56)
CAN_MSG_ID_M3FC_CFG_ACCEL_CAL_Y = CAN_ID_M3FC | msg_id(57)
CAN_MSG_ID_M3FC_CFG_ACCEL_CAL_Z = CAN_ID_M3FC | msg_id(58)
CAN_MSG_ID_M3FC_CFG_RADIO_FREQ = CAN_ID_M3FC | msg_id(59)
CAN_MSG_ID_M3FC_CFG_CRC = CAN_ID_M3FC | msg_id(60)
CAN_MSG_ID_M3FC_SET_CFG_PROFILE = CAN_ID_M3FC | msg_id(1)
CAN_MSG_ID_M3FC_SET_CFG_PYROS = CAN_ID_M3FC | msg_id(2)
CAN_MSG_ID_M3FC_LOAD_CFG = CAN_ID_M3FC | msg_id(3)
CAN_MSG_ID_M3FC_SAVE_CFG = CAN_ID_M3FC | msg_id(4)
CAN_MSG_ID_M3FC_MOCK_ENABLE = CAN_ID_M3FC | msg_id(5)
CAN_MSG_ID_M3FC_MOCK_ACCEL = CAN_ID_M3FC | msg_id(6)
CAN_MSG_ID_M3FC_MOCK_BARO = CAN_ID_M3FC | msg_id(7)
CAN_MSG_ID_M3FC_ARM = CAN_ID_M3FC | msg_id(8)
CAN_MSG_ID_M3FC_FIRE = CAN_ID_M3FC | msg_id(9)

components = {
    1: "Mission Control",
    2: "State Estimation",
    3: "Configuration",
    4: "Beeper",
    5: "LEDs",
    6: "Accelerometer",
    7: "Barometer",
    8: "Flash",
    9: "Pyros",
    10: "Mock",
    11: "PSU",
}

component_errors = {
    0: "No Error",
    1: "Flash CRC", 2: "Flash Write",
    3: "Config Read", 8: "Config Check Profile", 9: "Config Check Pyros",
    10: "Accel Bad ID", 11: "Accel Self Test", 12: "Accel Timeout",
    13: "Accel Axis", 14: "SE Pressure", 15: "Pyro Arm", 4: "Pyro Continuity",
    5: "Pyro Supply", 16: "Mock Enabled", 17: "CAN Bad Command",
    18: "Config Check Accel Cal", 19: "Config Check Radio Freq",
    20: "Config Check CRC", 21: "Battleshort",
}

compstatus = {k: {"state": 0, "reason": "Unknown"} for k in components}


@register_packet("m3fc", CAN_MSG_ID_M3FC_STATUS, "Status")
def status(data):
    global compstatus
    # The string must start with 'OK:' 'INIT:' or 'ERROR:' as the web
    # interface watches for these and applies special treatment (colours)
    statuses = {0: "OK", 1: "INIT", 2: "ERROR"}
    overall, comp, comp_state = data[:3]
    if len(data) == 4:
        comp_error = data[3]
    else:
        comp_error = 0

    # Display the state (and error) of the component that sent the message
    string = "{}: ({} {}".format(statuses.get(overall, "Unknown"),
                                 components.get(comp, "Unknown"),
                                 statuses.get(comp_state, "Unknown"))
    if comp_error != 0:
        string += " {})".format(component_errors.get(comp_error, "Unknown"))
    else:
        string += ")"

    # Update our perception of the overall state
    if comp in compstatus:
        compstatus[comp]['state'] = comp_state
        compstatus[comp]['reason'] = component_errors[comp_error]

    # List all components we believe to be in error
    errors = ""
    for k in components:
        if compstatus[k]['state'] == 2:
            errors += "\n{}: {}".format(components[k], compstatus[k]['reason'])
    if errors:
        string += "\nErrors:" + errors
    return string


@register_packet("m3fc", CAN_MSG_ID_M3FC_MISSION_STATE, "Mission State")
def mission_state(data):
    # 5 bytes total. 4 bytes met, 1 byte can_state
    met, can_state = struct.unpack("IB", bytes(data[:5]))
    states = ["Init", "Pad", "Ignition", "Powered Ascent", "Burnout",
              "Free Ascent", "Apogee", "Drogue Descent",
              "Release Main", "Main Descent", "Land", "Landed"]
    return "MET: {: 9.3f} s, State: {}".format(met/1000.0, states[can_state])


@register_packet("m3fc", CAN_MSG_ID_M3FC_MOCK_ACCEL, "Mock Accelerometer")
@register_packet("m3fc", CAN_MSG_ID_M3FC_ACCEL, "Acceleration")
def accel(data):
    # 6 bytes, 3 int16_ts for 3 accelerations
    # 3.9 MSB per milli-g
    factor = 3.9 / 1000.0 * 9.80665
    accel1, accel2, accel3 = struct.unpack("hhh", bytes(data[0:6]))
    accel1, accel2, accel3 = accel1*factor, accel2*factor, accel3*factor
    return "{: 3.1f} m/s/s {: 3.1f} m/s/s {: 3.1f} m/s/s".format(
        accel1, accel2, accel3)


@register_packet("m3fc", CAN_MSG_ID_M3FC_MOCK_BARO, "Mock Barometer")
@register_packet("m3fc", CAN_MSG_ID_M3FC_BARO, "Barometer")
def baro(data):
    # 8 bytes: 4 bytes of temperature in centidegrees celcius,
    # 4 bytes of pressure in Pascals
    temperature, pressure = struct.unpack("ii", bytes(data))
    return "Temperature: {: 4.1f}'C, Pressure: {: 6.0f} Pa".format(
        temperature / 100.0, pressure)


@register_packet("m3fc", CAN_MSG_ID_M3FC_SE_T_H, "State Estimate T,H")
def se_t_h(data):
    # 8 bytes, 2 float32s
    dt, h = struct.unpack("ff", bytes(data))
    return "dt: {: 6.4f} s, altitude: {: 5.0f} m".format(dt, h)


@register_packet("m3fc", CAN_MSG_ID_M3FC_SE_V_A, "State Estimate V,A")
def se_v_a(data):
    v, a = struct.unpack("ff", bytes(data))
    return "velocity: {: 6.1f} m/s, acceleration: {: 5.1f} m/s/s".format(v, a)


@register_packet("m3fc", CAN_MSG_ID_M3FC_SE_VAR_H, "State Estimate var(H)")
def se_var_h(data):
    (var_h,) = struct.unpack("f", bytes(data[0:4]))
    return "SD(altitude): {: 7.3f} m".format(sqrt(var_h))


@register_packet("m3fc", CAN_MSG_ID_M3FC_SE_VAR_V_A,
                 "State Estimate var(V),var(A)")
def se_var_v_var_a(data):
    var_v, var_a = struct.unpack("ff", bytes(data))
    return ("SD(velocity): {: 6.3f} m/s, SD_acceleration: {: 5.3f} m/s/s"
            .format(sqrt(var_v), sqrt(var_a)))


@register_packet("m3fc", CAN_MSG_ID_M3FC_CFG_PROFILE, "Profile config")
@register_packet("m3fc", CAN_MSG_ID_M3FC_SET_CFG_PROFILE, "Set profile config")
def cfg_profile(data):
    position = {1: "dart", 2: "core"}.get(data[0], "unset")
    accel_axis = {1: "X", 2: "-X", 3: "Y", 4: "-Y", 5: "Z", 6: "-Z"}.get(
        data[1], "unset")
    ignition_accel, burnout_timeout, apogee_timeout = data[2:5]
    main_altitude, main_timeout, land_timeout = data[5:8]
    return ("Position: {}, ".format(position) +
            "Accelerometer axis: {}, ".format(accel_axis) +
            "Ignition acceleration: {: 4.1f} m/s/s, ".format(ignition_accel) +
            "Burnout timeout: {: 4.1f} s, ".format(burnout_timeout/10.0) +
            "Apogee timeout: {: 3d} s, ".format(apogee_timeout) +
            "Main altitude: {: 4d} m, ".format(main_altitude*10) +
            "Main timeout: {: 3d} s, ".format(main_timeout) +
            "Land timeout: {: 4d} s".format(land_timeout*10))


@register_packet("m3fc", CAN_MSG_ID_M3FC_CFG_PYROS, "Pyros config")
@register_packet("m3fc", CAN_MSG_ID_M3FC_SET_CFG_PYROS, "Set pyro config")
def cfg_pyros(data):
    use_map = {0x00: "Unused",
               0x10: "Drogue", 0x20: "Main", 0x30: "Dart Separation"}
    use_mask = 0xf0
    type_map = {0: "None", 1: "EMatch", 2: "Talon", 3: "Metron"}
    type_mask = 0x03
    current_map = {0: "None", 0x04: "1A", 0x08: "3A"}
    current_mask = 0x0c
    p1u, p2u, p3u, p4u, p5u, p6u, p7u, p8u = [
        use_map.get(x & use_mask, "Unset") for x in data]
    p1t, p2t, p3t, p4t, p5t, p6t, p7t, p8t = [
        type_map.get(x & type_mask, "Unset") for x in data]
    p1c, p2c, p3c, p4c, p5c, p6c, p7c, p8c = [
        current_map.get(x & current_mask, "Unset") for x in data]

    return ("Pyro1: {}/{}/{}<br>Pyro2: {}/{}/{}<br>Pyro3: {}/{}/{}<br>"
            "Pyro4: {}/{}/{}<br>Pyro5: {}/{}/{}<br>Pyro6: {}/{}/{}<br>"
            "Pyro7: {}/{}/{}<br>Pyro8: {}/{}/{}"
            .format(p1u, p1t, p1c, p2u, p2t, p2c, p3u, p3t, p3c,
                    p4u, p4t, p4c, p5u, p5t, p5c, p6u, p6t, p6c,
                    p7u, p7t, p7c, p8u, p8t, p8c))


@register_packet("m3fc", CAN_MSG_ID_M3FC_CFG_ACCEL_CAL_X, "Accel Cal X")
@register_packet("m3fc", CAN_MSG_ID_M3FC_CFG_ACCEL_CAL_Y, "Accel Cal Y")
@register_packet("m3fc", CAN_MSG_ID_M3FC_CFG_ACCEL_CAL_Z, "Accel Cal Z")
def cfg_accel_cal(data):
    scale, offset = struct.unpack("<ff", bytes(data))
    return "Scale {:.6f}g/LSB, Offset {:.3f}LSB".format(scale, offset)


@register_packet("m3fc", CAN_MSG_ID_M3FC_CFG_RADIO_FREQ, "Radio Freq")
def cfg_radio_freq(data):
    freq = struct.unpack("<I", bytes(data[:4]))[0]
    return "{:.6f} MHz".format(freq/1e6)


@register_packet("m3fc", CAN_MSG_ID_M3FC_CFG_CRC, "Config CRC")
def cfg_crc(data):
    crc = struct.unpack("<I", bytes(data[:4]))[0]
    return hex(crc)


@register_packet("m3fc", CAN_MSG_ID_M3FC_LOAD_CFG, "Load config")
def load_config(data):
    return "Load config from flash"


@register_packet("m3fc", CAN_MSG_ID_M3FC_SAVE_CFG, "Save config")
def save_config(data):
    return "Save config to flash"


@register_packet("m3fc", CAN_MSG_ID_M3FC_MOCK_ENABLE, "Mock Enable")
def mock_enable(data):
    return "Mock Enabled"


@register_packet("m3fc", CAN_MSG_ID_M3FC_ARM, "Arm")
def arm(data):
    return "Armed"


@register_command("m3fc", "Arm", ["Arm"])
def arm_cmd(data):
    return CAN_MSG_ID_M3FC_ARM, []


@register_command("m3fc", "Fire Drogue", ["Fire Drogue"])
@register_command("m3fc", "Fire Main", ["Fire Main"])
@register_command("m3fc", "Fire Dart", ["Fire Dart"])
def fire_cmd(data):
    pyros = {"Fire Drogue": 1, "Fire Main": 2, "Fire Dart": 3}
    return CAN_MSG_ID_M3FC_FIRE, [pyros.get(data, 0)]
