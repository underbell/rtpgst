import sys;
import time;
import logging
logging.basicConfig(format='%(asctime)s %(message)s', level=logging.DEBUG);
sys.path.append('/home/ioseph/python');
import psycopg2;

Connections = {};

class DaemonConnection:
    def __init__(self,dsn, autocommit, application_name = None, session_name = None):
        self.dsn = dsn;
        self.autocommit = autocommit;
        if (application_name != None):
            self.application_name = application_name;
	else:
            self.application_name = "";
        if (session_name != None):
            self.session_name = session_name;
	else:
            self.session_name = "";

    def connect(self):
        is_connected = False;
        while not is_connected:
            try:
                self.connection = psycopg2.connect(self.dsn);
                self.connection.autocommit = self.autocommit;
		if (self.application_name != ""):
		    cur = self.connection.cursor();
		    cur.execute("set application_name = '%s'" % self.application_name);
		    cur.close();
                is_connected = True;
		Connections[self.connection.dsn] = self;
            except Exception, e:
                logging.error("%s: %s: %s" % (self.dsn, e.__class__.__name__, e));
                time.sleep(1.0);
    def close(self):
#        logging.info("%s: closing db" % (self.session_name));
        self.connection.close();

    def reconnect(self):
        self.close();
        self.connect();

    def cursor(self):
        return self.connection.cursor(cursor_factory=LoggingCursor);

    def poll(self):
        try:
            self.connection.poll();
        except Exception,e:
            raise OperationalError;
	self.notifies = self.connection.notifies;




class NoDataError(psycopg2.ProgrammingError):
    pass;

class DBResetError:
    def __init__(self,dsn):
        Connections[dsn].reconnect();
    pass;

class DBQueryError:
    pass;

class OperationalError:
    pass;


class LoggingCursor(psycopg2.extensions.cursor):
    def execute(self, sql, args=None):
        try:
            current_commit = self.connection.autocommit;
            psycopg2.extensions.cursor.execute(self, sql, args);
            self.is_require_reconnect = False;
        except Exception, exc:
            logging.error("%s: %s: %s" % (self.connection.dsn, exc.__class__.__name__, exc));
            try:
            	self.connection.reset();
            	self.connection.autocommit = current_commit;
            except Exception, exc:
                DBResetError(self.connection.dsn);
    def fetchall(self):
        try:
            rs = psycopg2.extensions.cursor.fetchall(self);
            if rs is None:
                NoDataError();
            return rs;
        except Exception, exc:
            logging.error("%s: %s: %s" % (self.connection.dsn, exc.__class__.__name__, exc));
    def fetchone(self):
        try:
            rs = psycopg2.extensions.cursor.fetchone(self);
            if rs is None:
                NoDataError();
            return rs;
        except Exception, exc:
            logging.error("%s: %s: %s" % (self.connection.dsn, exc.__class__.__name__, exc));
