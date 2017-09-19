#include "m3fc_config.h"
#include "m3can.h"
#include "m3fc_status.h"
#include "m3flash.h"

#define M3FC_CONFIG_FLASH (0x080e0000)

struct m3fc_config m3fc_config;

static bool m3fc_config_check_profile(void);
static bool m3fc_config_check_pyros(void);
static bool m3fc_config_check_pyro(uint8_t pyro);
static bool m3fc_config_check_accel_cal(void);
static bool m3fc_config_check_radio_freq(void);
static bool m3fc_config_check_crc(void);

static THD_WORKING_AREA(m3fc_config_reporter_thd_wa, 256);
static THD_FUNCTION(m3fc_config_reporter_thd, arg) {
    (void)arg;

    while(true) {
        /* Send current config over CAN every 5s */
        m3can_send_u8(CAN_MSG_ID_M3FC_CFG_PROFILE,
                      m3fc_config.profile.m3fc_position,
                      m3fc_config.profile.accel_axis,
                      m3fc_config.profile.ignition_accel,
                      m3fc_config.profile.burnout_timeout,
                      m3fc_config.profile.apogee_timeout,
                      m3fc_config.profile.main_altitude,
                      m3fc_config.profile.main_timeout,
                      m3fc_config.profile.land_timeout, 8);
        m3can_send_u8(CAN_MSG_ID_M3FC_CFG_PYROS,
                      m3fc_config.pyros.pyro1,
                      m3fc_config.pyros.pyro2,
                      m3fc_config.pyros.pyro3,
                      m3fc_config.pyros.pyro4,
                      m3fc_config.pyros.pyro5,
                      m3fc_config.pyros.pyro6,
                      m3fc_config.pyros.pyro7,
                      m3fc_config.pyros.pyro8, 8);
        m3can_send_f32(CAN_MSG_ID_M3FC_CFG_ACCEL_X,
                       m3fc_config.accel_cal.x_scale,
                       m3fc_config.accel_cal.x_offset, 2);
        m3can_send_f32(CAN_MSG_ID_M3FC_CFG_ACCEL_Y,
                       m3fc_config.accel_cal.y_scale,
                       m3fc_config.accel_cal.y_offset, 2);
        m3can_send_f32(CAN_MSG_ID_M3FC_CFG_ACCEL_Z,
                       m3fc_config.accel_cal.z_scale,
                       m3fc_config.accel_cal.z_offset, 2);
        m3can_send_u32(CAN_MSG_ID_M3FC_CFG_RADIO_FREQ,
                       m3fc_config.radio_freq, 0, 1);
        m3can_send_u32(CAN_MSG_ID_M3FC_CFG_CRC,
                       m3fc_config.crc, 0, 1);

        /* Check the config. Sets an error inside the relevant config check
         * functions, so no need to handle the error case here.
         */
        if(m3fc_config_check()) {
            m3status_set_ok(M3FC_COMPONENT_CFG);
        }

        chThdSleepMilliseconds(5000);
    }
}

bool m3fc_config_load() {
    bool rv = m3flash_read((uint32_t*)M3FC_CONFIG_FLASH,
                           (uint32_t*)&m3fc_config, sizeof(m3fc_config)/4);

    if(!rv) {
        m3status_set_error(M3FC_COMPONENT_FLASH, M3FC_ERROR_FLASH_CRC);
    }

    return rv;
}

void m3fc_config_save() {
    bool rv = m3flash_write((uint32_t*)&m3fc_config,
                            (uint32_t*)M3FC_CONFIG_FLASH,
                            sizeof(m3fc_config)/4);
    if(!rv) {
        m3status_set_error(M3FC_COMPONENT_FLASH, M3FC_ERROR_FLASH_WRITE);
    }
}

void m3fc_config_init() {
    m3status_set_init(M3FC_COMPONENT_CFG);

    if(!m3fc_config_load()) {
        m3status_set_error(M3FC_COMPONENT_CFG, M3FC_ERROR_CFG_READ);
    }

    chThdCreateStatic(m3fc_config_reporter_thd_wa,
                      sizeof(m3fc_config_reporter_thd_wa),
                      NORMALPRIO, m3fc_config_reporter_thd, NULL);
}


static bool m3fc_config_check_profile() {
    bool ok = true;
    ok &= m3fc_config.profile.m3fc_position >= 1;
    ok &= m3fc_config.profile.m3fc_position <= 2;
    ok &= m3fc_config.profile.accel_axis >= 1;
    ok &= m3fc_config.profile.accel_axis <= 6;
    if(!ok) {
        m3status_set_error(M3FC_COMPONENT_CFG, M3FC_ERROR_CFG_CHK_PROFILE);
    }
    return ok;
}

static bool m3fc_config_check_pyro(uint8_t pyro) {
    uint8_t usage = pyro & M3FC_CONFIG_PYRO_USAGE_MASK;
    uint8_t current = pyro & M3FC_CONFIG_PYRO_CURRENT_MASK;
    uint8_t type = pyro & M3FC_CONFIG_PYRO_TYPE_MASK;

    /* Check usage is one of the valid options. */
    if(usage != M3FC_CONFIG_PYRO_USAGE_NONE     &&
       usage != M3FC_CONFIG_PYRO_USAGE_DROGUE   &&
       usage != M3FC_CONFIG_PYRO_USAGE_MAIN     &&
       usage != M3FC_CONFIG_PYRO_USAGE_DARTSEP)
    {
        return false;
    }

    /* Check current is one of the valid options. */
    if(current != M3FC_CONFIG_PYRO_CURRENT_NONE &&
       current != M3FC_CONFIG_PYRO_CURRENT_1A   &&
       current != M3FC_CONFIG_PYRO_CURRENT_3A)
    {
        return false;
    }

    /* All possible bit patterns are valid options for type. */

    /* If usage is not NONE, check current and type are not either. */
    if(usage != M3FC_CONFIG_PYRO_USAGE_NONE &&
       (current == M3FC_CONFIG_PYRO_CURRENT_NONE ||
        type == M3FC_CONFIG_PYRO_TYPE_NONE))
    {
        return false;
    }

    /* If usage is NONE, check current and type are too. */
    if(usage == M3FC_CONFIG_PYRO_USAGE_NONE &&
       (current != M3FC_CONFIG_PYRO_CURRENT_NONE ||
        type != M3FC_CONFIG_PYRO_TYPE_NONE))
    {
        return false;
    }

    return true;
}


static bool m3fc_config_check_pyros() {
    if(m3fc_config_check_pyro(m3fc_config.pyros.pyro1) &&
       m3fc_config_check_pyro(m3fc_config.pyros.pyro2) &&
       m3fc_config_check_pyro(m3fc_config.pyros.pyro3) &&
       m3fc_config_check_pyro(m3fc_config.pyros.pyro4) &&
       m3fc_config_check_pyro(m3fc_config.pyros.pyro5) &&
       m3fc_config_check_pyro(m3fc_config.pyros.pyro6) &&
       m3fc_config_check_pyro(m3fc_config.pyros.pyro7) &&
       m3fc_config_check_pyro(m3fc_config.pyros.pyro8))
    {
        return true;
    } else {
        m3status_set_error(M3FC_COMPONENT_CFG, M3FC_ERROR_CFG_CHK_PYROS);
        return false;
    }
}

static bool m3fc_config_check_accel_cal(void)
{
    bool ok = true;
    ok &= m3fc_config.accel_cal.x_scale > 0.0035f;
    ok &= m3fc_config.accel_cal.x_scale < 0.0043f;
    ok &= m3fc_config.accel_cal.y_scale > 0.0035f;
    ok &= m3fc_config.accel_cal.y_scale < 0.0043f;
    ok &= m3fc_config.accel_cal.z_scale > 0.0035f;
    ok &= m3fc_config.accel_cal.z_scale < 0.0043f;
    ok &= m3fc_config.accel_cal.x_offset > -40.0f;
    ok &= m3fc_config.accel_cal.x_offset <  40.0f;
    ok &= m3fc_config.accel_cal.y_offset > -40.0f;
    ok &= m3fc_config.accel_cal.y_offset <  40.0f;
    ok &= m3fc_config.accel_cal.z_offset > -64.0f;
    ok &= m3fc_config.accel_cal.z_offset <  64.0f;
    if(!ok) {
        m3status_set_error(M3FC_COMPONENT_CFG, M3FC_ERROR_CFG_CHK_ACCEL_CAL);
    }
    return ok;
}

static bool m3fc_config_check_radio_freq(void)
{
    bool ok = true;
    ok &= m3fc_config.radio_freq > 868000000;
    ok &= m3fc_config.radio_freq < 870000000;
    if(!ok) {
        m3status_set_error(M3FC_COMPONENT_CFG, M3FC_ERROR_CFG_CHK_RADIO_FREQ);
    }
    return ok;
}

static bool m3fc_config_check_crc(void)
{
    uint32_t crc;
    uint32_t *src = (uint32_t*)&m3fc_config;

    /* Subtract one so we don't compute over the stored checksum */
    size_t n = (sizeof(struct m3fc_config) / 4) - 1;

    RCC->AHB1ENR |= RCC_AHB1ENR_CRCEN;
    CRC->CR |= CRC_CR_RESET;
    for(size_t i=0; i<n; i++) {
        CRC->DR = src[i];
    }
    crc = CRC->DR;
    RCC->AHB1ENR &= ~RCC_AHB1ENR_CRCEN;

    bool ok = crc == m3fc_config.crc;

    if(!ok) {
        m3status_set_error(M3FC_COMPONENT_CFG, M3FC_ERROR_CFG_CHK_CRC);
    }

    return ok;
}

bool m3fc_config_check() {
    bool ok = true;
    ok &= m3fc_config_check_profile();
    ok &= m3fc_config_check_pyros();
    ok &= m3fc_config_check_accel_cal();
    ok &= m3fc_config_check_radio_freq();
    ok &= m3fc_config_check_crc();
    return ok;
}

void m3fc_config_handle_set_profile(uint8_t* data, uint8_t datalen) {
    if(datalen != 8) {
        m3status_set_error(M3FC_COMPONENT_CFG, M3FC_ERROR_CAN_BAD_COMMAND);
        return;
    }

    m3fc_config.profile.m3fc_position   = data[0];
    m3fc_config.profile.accel_axis      = data[1];
    m3fc_config.profile.ignition_accel  = data[2];
    m3fc_config.profile.burnout_timeout = data[3];
    m3fc_config.profile.apogee_timeout  = data[4];
    m3fc_config.profile.main_altitude   = data[5];
    m3fc_config.profile.main_timeout    = data[6];
    m3fc_config.profile.land_timeout    = data[7];
    m3fc_config_check();
}

void m3fc_config_handle_set_pyros(uint8_t* data, uint8_t datalen) {
    if(datalen != 8) {
        m3status_set_error(M3FC_COMPONENT_CFG, M3FC_ERROR_CAN_BAD_COMMAND);
        return;
    }

    m3fc_config.pyros.pyro1     = data[0];
    m3fc_config.pyros.pyro2     = data[1];
    m3fc_config.pyros.pyro3     = data[2];
    m3fc_config.pyros.pyro4     = data[3];
    m3fc_config.pyros.pyro5     = data[4];
    m3fc_config.pyros.pyro6     = data[5];
    m3fc_config.pyros.pyro7     = data[6];
    m3fc_config.pyros.pyro8     = data[7];
    m3fc_config_check();
}

void m3fc_config_handle_set_accel_cal_x(uint8_t* data, uint8_t datalen) {
    if(datalen != 8) {
        m3status_set_error(M3FC_COMPONENT_CFG, M3FC_ERROR_CAN_BAD_COMMAND);
        return;
    }

    float *fdata = (float*)data;
    m3fc_config.accel_cal.x_scale  = fdata[0];
    m3fc_config.accel_cal.x_offset = fdata[1];
}

void m3fc_config_handle_set_accel_cal_y(uint8_t* data, uint8_t datalen) {
    if(datalen != 8) {
        m3status_set_error(M3FC_COMPONENT_CFG, M3FC_ERROR_CAN_BAD_COMMAND);
        return;
    }

    float *fdata = (float*)data;
    m3fc_config.accel_cal.y_scale  = fdata[0];
    m3fc_config.accel_cal.y_offset = fdata[1];
}

void m3fc_config_handle_set_accel_cal_z(uint8_t* data, uint8_t datalen) {
    if(datalen != 8) {
        m3status_set_error(M3FC_COMPONENT_CFG, M3FC_ERROR_CAN_BAD_COMMAND);
        return;
    }

    float *fdata = (float*)data;
    m3fc_config.accel_cal.z_scale  = fdata[0];
    m3fc_config.accel_cal.z_offset = fdata[1];
}

void m3fc_config_handle_set_radio_freq(uint8_t* data, uint8_t datalen) {
    if(datalen != 4) {
        m3status_set_error(M3FC_COMPONENT_CFG, M3FC_ERROR_CAN_BAD_COMMAND);
        return;
    }

    uint32_t *u32data = (uint32_t*)data;
    m3fc_config.radio_freq = u32data[0];
}

void m3fc_config_handle_set_crc(uint8_t* data, uint8_t datalen) {
    if(datalen != 4) {
        m3status_set_error(M3FC_COMPONENT_CFG, M3FC_ERROR_CAN_BAD_COMMAND);
        return;
    }

    uint32_t *u32data = (uint32_t*)data;
    m3fc_config.crc = u32data[0];
}

void m3fc_config_handle_load(uint8_t* data, uint8_t datalen) {
    (void)data;
    (void)datalen;
    m3fc_config_load();
    m3fc_config_check();
}

void m3fc_config_handle_save(uint8_t* data, uint8_t datalen) {
    (void)data;
    (void)datalen;
    m3fc_config_save();
    m3fc_config_load();
    m3fc_config_check();
}
