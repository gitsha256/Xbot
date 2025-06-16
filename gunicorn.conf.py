loglevel = "debug"
accesslog = "-"
errorlog = "-"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'
timeout = 600
workers = 1
preload_app = True  # Preload app to catch initialization errors
