from brainboost_data_source_logger_package.BBLogger import BBLogger


config = {}
config['log_debug_mode'] = True

config['log_path'] = 'logs'
config['log_memsize_limit'] = 50*1024*1024
config['log_prefix'] = 'mylogs'
config['log_notification_urls'] = ['https://100.96.1.34:8080/log','https://127.0.0.1:8000/telegram','https://127.0.0.1:8000/slack']


config['log_enable_files_csv'] = True
config['log_enable_files_json'] = True
config['log_enable_terminal_output'] = False
config['log_enable_files'] = True
config['log_enable_database'] = False


config['log_sqlite3_path'] = config['log_path'] + '/' + config['log_prefix'] + '.db'


config['log_delimiter'] = '|'
config['log_columns'] = ['timestampt','type','process_name','source_code_line','message','exec_time']
