import importlib
module = importlib.import_module('fbs_runtime._frozen')
module.BUILD_SETTINGS = {'app_name': 'ATEM Streamer', 'author': 'Youssef Asaad', 'version': '1.0.0', 'environment': 'local'}