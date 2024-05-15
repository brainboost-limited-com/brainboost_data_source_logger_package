from inspect import currentframe, getframeinfo, stack
import sys
import time
from datetime import datetime
from urllib.parse import uses_params
import requests
import os

from com_goldenthinker_trade_config.Config import Config



class Logger:
        
    _p_name = None
    
    @classmethod
    def get_process_name(cls):
        return Logger._p_name
    
    @classmethod
    def set_process_name(cls,name):
        cls._p_name = name
    
    @classmethod
    def enable_storage(cls):
        return False
        
    @classmethod
    def fordward_log(cls,server):
        pass

    @classmethod
    def enabled(cls):
        return True

    @classmethod
    def terminal_output_enabled(cls):
        return False
    
    @classmethod
    def csv_enabled(cls):
        return True

    @classmethod
    def database(cls):
        from com_goldenthinker_trade_database.MongoConnector import MongoConnector
        return MongoConnector.get_instance()

    
    _last_time = None
    _delta = None
    
    
    @classmethod
    def log(cls, trade_log,telegram=False,public=False,trace=False,external=True):
        if external==True:
            r = requests.get(Config.get('base_url_1_5'),{'trade_log':trade_log,'telegram':telegram,'public':public,'trace':trace})
        else:
            def if_later_than_12am_set_new_default_access_permission_for_new_log_file():
                now = datetime.now()
                tomorrow12am = now.replace(hour=23, minute=59, second=59, microsecond=0)
                if now > tomorrow12am:
                    from com_goldenthinker_trade_utils.Utils import Utils
                    Utils.execute('chmod 777 logs/*')
            
            
            if Logger.enabled:
                if Logger._last_time is None: 
                    Logger._last_time = datetime.now()
                    time.sleep(0.01)
                Logger._delta = datetime.now() - Logger._last_time
                Logger._last_time = datetime.now()
                current_date = Logger._last_time.strftime("%Y_%m_%d")
                caller = getframeinfo(stack()[1][0])
                if cls.get_process_name()==None:
                    cls.set_process_name('initializing_logger')
                if trace==False:
                    current_log_line = str(hash(str(cls.get_process_name()[0:15]) + str(datetime.now())))[1:] + "," + str(cls.get_process_name()) + "," + str(datetime.now()) + "," + "%s:%d" % (caller.filename.split("/")[-1], caller.lineno) + "," +  str(trade_log) + "," + str(Logger._delta) + "\n"
                else:
                    try:
                        exc_type, exc_obj, exc_tb = sys.exc_info()
                        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                        my_trace = exc_type, fname, exc_tb.tb_lineno
                        current_log_line = str(hash(str(cls.get_process_name()[0:15]) + str(datetime.now())))[1:] + "," + str(cls.get_process_name()) + "," + str(datetime.now()) + "," + "%s:%d" % (caller.filename.split("/")[-1], caller.lineno) + "," +  str(trade_log) + "," + str(my_trace) + "," + str(Logger._delta) + "\n"
                    except:
                        pass
                
                if Logger.database()!=None:
                    if_later_than_12am_set_new_default_access_permission_for_new_log_file()
                    Logger.database().insert_logline(current_log_line)               
                if Logger.csv_enabled:
                    if cls.enable_storage()==False:
                        cls.logfile_path = "d:\\cryptologs\\trader_log-" + current_date + ".csv"
                    else:
                        cls.logfile_path = "d:\\cryptologs\\trader_log-" + current_date + ".csv"
                    if_later_than_12am_set_new_default_access_permission_for_new_log_file()
                    with open(cls.logfile_path, "a+", encoding="utf-8") as log_file:
                        log_file.write(current_log_line)   
                if telegram==True:
                    if public==False:
                        try:
                            requests.get(url = 'http://0.0.0.0:8080/send_telegram_notification', params={'message':current_log_line})
                        except:
                            Logger.log(current_log_line)
                    else:
                        if public==True:
                            try:
                                requests.get(url = 'http://0.0.0.0:8080/send_telegram_notification', params={'message':current_log_line,'public':'True'})
                            except:
                                Logger.log(current_log_line)
                    #cls._telegram_notifier.send_message(message=current_log_line)
                #if Logger.terminal_output_enabled:
                #    print(current_log_line)
        