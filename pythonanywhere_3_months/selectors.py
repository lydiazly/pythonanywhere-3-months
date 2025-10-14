# -*- coding: utf-8 -*-
# selectors.py


class LoginIds:
    USERNAME = "id_auth-username"
    PASSWORD = "id_auth-password"
    LOGIN_BUTTON = "id_next"
    LOGIN_ERROR = 'id_login_error'


class Selectors:
    RUN_BUTTON = "input.webapp_extend[type='submit']"
    EXPIRY_DATE_TAG = 'p.webapp_expiry > strong'
    LOGOUT_BUTTON = "button.logout_link[type='submit']"
