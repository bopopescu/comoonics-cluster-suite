"""
Thread class for reading from logfiles and storing the data in a dictionary keyed with the time as hash.
The data stored in the dictionary is of type Line.
"""

import sys
from threading import Thread, Event, Lock
from comoonics import ComLog
from comoonics.search.datetime.TimeExpression import DateFormat, GuessedDateFormat

class Line(object):
    def __init__(self, line, linenumber=-1, filename=None, timematch=None):
        self.line=line
        self.linenumber=linenumber
        self.filename=filename
        self.timehash=timematch.timeHash()

    def timeHash(self):
        return self.timehash
    def toString(self, with_filename=False, with_linenumber=False):
        buf=self.line
        if self.linenumber > 0 and with_linenumber:
            buf="%u:%s" %(self.linenumber, buf)
        if self.filename and with_filename:
            buf="%s:%s" %(self.filename, buf)
        return buf

    def __str__(self):
        return self.toString()

class FileReaderThread(Thread):
    def __init__(self, lines, filename, searches=None, _lock=None):
        super(FileReaderThread, self).__init__()
        if not _lock:
            self._lock=Lock()
        else:
            self._lock=_lock
        if filename:
            self.stream=open(filename, "r")
            self.setName(filename)
        else:
            self.stream=sys.stdin
            self.setName("stdin")
        self.logger=ComLog.getLogger("log_file_analyser.rthread(%s)" %filename)
        # copying searches for thread safeness
        self.logger.debug("searches<%s>: %s" %(type(searches), searches))
        import copy
        if not searches:
            self.searches=list()
            self.searches.append(GuessedDateFormat("*"))
        else:
            self.searches=copy.deepcopy(searches)
        
        self.waitevent=Event()
        self.lines=lines
        self._exit=False
        self.lasttimehash=None
        self.readlines=False

    def run(self):
        self.logger.debug("run: Starting thread(searches: %s, stream: %s)." %(self.searches, self.stream))
        _linenumber=1
        __line=None
        for _line in self.stream:
            self.logger.debug("run: Reading line: %s" %_line)
            _found=True
            _timematch=None
            #self.lock()
            if self._exit:
                break
            self.lock()
            self.readlines=True
            if self.searches:
                for _search in self.searches:
                    #logger.debug("searching: %s, line: %s" %(_search, _line))
                    _found=_found and _search.found(_line)
                    if not _found:
                        break
                    #if isinstance(_search, DateFormat):
                    self.logger.debug("Adding search: %s" %_search)
                    if isinstance(_search, DateFormat) or isinstance(_search, GuessedDateFormat):
#                        self.lock()
                        _timematch=_search
            if _found:
                _line=Line(_line, _linenumber, self.getName(), _timematch)
                self.logger.debug("run: adding line for timehash[%s], _timematch: %s: %s" %(_line.timeHash(), _timematch, _line))
                _timehash=_line.timeHash()
                if not self.lines.has_key(_timehash):
                    self.lines[_timehash]=list()
                self.lines[_timehash].append(_line)
                self.lasttimehash=_timehash
            self.release()
            #self.release()
            _linenumber+=1
        self.logger.debug("run: Thread terminated successfully.")
        self.logger.debug("run: linenumber: %u" %(_linenumber))

    def lock(self):
        self._lock.acquire()
        #pass
    def release(self):
        self._lock.release()
        #pass
    def getLines(self):
        self.lock()
        _lines=self.lines
        self.release()
        return _lines
    def getLastTimehash(self):
        self.lock()
        _timehash=self.lasttimehash
        self.release()
        return _timehash
    #def wait(self):
        #self.logger.debug("waiting(clear)...")
    #    self.waitevent.clear()
        #self.logger.debug("waiting...")
    #    self.waitevent.wait()
    def exit(self):
        self._exit=True
        try:
            self.release()
        except:
            pass
    #def cont(self):
        #self.logger.debug("continue..")
    #    self.contuntil()
    #def contuntil(self, timehash="0"):
        #if not self.timematch or (self.timematch and (self.getTimehash() <= timehash or timehash=="0")):
    #    self.timematch=None
    #    self.waitevent.set()
        #self.waitevent.notify()
