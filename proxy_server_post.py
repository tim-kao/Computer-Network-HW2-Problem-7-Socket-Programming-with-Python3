from socket import *
import sys
import urllib.parse
from datetime import datetime

MAXPENDING = 10
BUF_SIZE = 19200000
server_ip = '127.0.0.1'
port = 8888
messages_okay = ['HTTP/1.0 200 OK\r\n', 'Content-Type:text/html\r\n']
message_404 = 'HTTP/1.1 404 Not Found\r\n'
html_404 = '<html><head></head><body><h1>404 Not Found</h1></body></html>\r\n'

def proxy_server():
    if len(sys.argv) <= 1:
        print('Usage : "python ProxyServer.py server_ip"\n[server_ip : It is the IP Address Of Proxy Server')
        sys.exit(2)
    # Create a server socket, bind it to a port and start listening
    tcpSerSock = socket(AF_INET, SOCK_STREAM)  # params: domain, type protocol, SOCK_STREAM for TCP, SOCK_DGRAM for UDP
    # Fill in start.
    # tcpSerSock.bind((sys.argv[1], port))  # bind to port 8888
    tcpSerSock.bind((sys.argv[1], port))
    tcpSerSock.listen(MAXPENDING)  # sets up the listening socket, backlog = 10
    # Fill in end.
    while True:
        # Start receiving data from the client
        print('Ready to serve...')
        tcpCliSock, addr = tcpSerSock.accept()
        print('Received a connection from:', addr)
        # Fill in start.
        message = tcpCliSock.recv(BUF_SIZE)
        urlobj = message_handler(message)
        if urlobj is None:
            continue
        hostn, filename, request_path = urlobj.netloc, urlobj.netloc, urlobj.path
        if len(urlobj.path) > 1:
            filename += urlobj.path
        fileExist = 'false'
        try:
            # Check whether the file exist in the cache
            f = open(filename, 'r')
            outputdata = f.readlines()  # returns a list containing each line in the file as a list item.
            fileExist = 'true'

            if len(outputdata) > 2 and outputdata[1]:  # Conditional Get 'If-Modified-Since'
                last_data = outputdata[1].split('Date: ')[1].split('GMT')[0]
                # last_access_time = datetime.strptime(last_data, '%a, %d %b %Y %H:%M:%S ')    #Thu, 18 Feb 2021 09:59:14
                # conditional get
                c = socket(AF_INET, SOCK_STREAM)  # TCP
                c.connect((hostn, 80))  # bind to port 80
                request = conditional_get(urlobj, last_data)
                print(request)
                c.send(request.encode())
                buff = c.recv(BUF_SIZE)
                tmpFile = open('./' + 'conditional_get_result', 'wb')
                tmpFile.write(buff)
                tmpFile.close()
                c.close()

            # ProxyServer finds a cache hit and generates a response message
            for message_okay in messages_okay:
                tcpCliSock.send(message_okay.encode())
                print('proxy client response', message_okay)
            # Fill in start.
            # Send data to TCP client socket
            for line in outputdata:
                tcpCliSock.send(line.encode())
            # Fill in end.
            print('Read from cache')
            f.close()
        # Error handling for file not found in cache
        except IOError:
            if fileExist == 'false':
                # Create a socket on the proxy server
                # Fill in start.
                c = socket(AF_INET, SOCK_STREAM)  # TCP
                # Fill in end.
                # hostn = proc_message[4]  # remove prefix 'www.'
                print('Cache is unavailable, request the original server...')
                print('hostn:', hostn)
                try:
                    # Connect to the socket to port 80
                    # Fill in start.
                    c.connect((hostn, 80))  # bind to port 80
                    # Fill in end.
                    # Create a temporary file on this socket and ask port 80 for the file requested by the client
                    # fileobj = c.makefile('rw', None)
                    request = post(urlobj)
                    print('request', request)
                    # Read the response into buffer
                    # Fill in start.
                    c.send(request.encode())
                    buff = c.recv(BUF_SIZE)
                    # Fill in end.
                    # Create a new file in the cache for the requested file.
                    # Also send the response in the buffer to client socket and the corresponding file in the cache
                    # Fill in start.
                    tcpCliSock.send(buff)
                    tmpFile = open('./' + filename, 'wb')
                    tmpFile.write(buff)
                    tmpFile.close()
                    c.close()
                    print('Cache', filename, ' is written!')
                    print('Connection close')
                    # Fill in end.
                except:
                    c.close()
                    print('Illegal request')
            else:
                # HTTP response message for file not found
                # Fill in start.
                tcpCliSock.send(message_404.encode())
                print("404 not found")
                # Fill in end.
        # Close the client and the server sockets
        tcpCliSock.close()
    tcpSerSock.close()
    # Fill in start.
    # Fill in end.


def message_handler(message):
    # Fill in end.
    print('Raw message: ', message)
    # Extract the filename from the given message   www.google.com
    proc_message = message.decode().split()
    print(proc_message)

    if len(proc_message) < 5:
        return None

    if proc_message[4] == 'localhost:' + str(port):
        if 'Referer:' in proc_message:
            index = proc_message.index('Referer:') + 1
            server = proc_message[index].split(str(port) + '/')[1]
            request_path = proc_message[1]
            print('get specific objects on ', server)
            url = server + request_path
        else:
            url = proc_message[1][1:]
        print('Try to access local cache.')
    else:
        url = proc_message[4] + proc_message[1]
        print('Access an original server.')

    if 'http' not in url:
        url = 'http://' + url
    print('url:', url)
    parsed_url = urllib.parse.urlparse(url)
    print('hostn/filename:', parsed_url.netloc, 'request path: ', parsed_url.path, 'query:', parsed_url.query)
    return parsed_url


def get(urlobj):
    request = 'GET '
    if urlobj.path == '':
        request += '/'
    request += urlobj.path + urlobj.query + ' HTTP/1.1\r\n'
    request += 'Host:' + urlobj.netloc + '\r\n\r\n'
    print('GET method', request, request.encode())
    return request


def conditional_get(urlobj, date):
    request = 'GET '
    if urlobj.path == '':
        request += '/'
    request += urlobj.path + urlobj.query + ' HTTP/1.1\r\n'
    request += 'Host:' + urlobj.netloc + '\r\n'
    request += 'If-Modified-Since: ' + date + 'GMT\r\n\r\n'
    print('GET method', request, request.encode())
    return request


def post(urlobj):
    request = 'POST '
    if urlobj.path == '':
        request += '/'
    request += urlobj.path + urlobj.query + ' HTTP/1.1\r\n'
    request += 'Accept: */*\r\n'
    request += 'Host:' + urlobj.netloc + '\r\n'
    request += 'Content-Length: 0\r\n\r\n'
    print('POST method', request, request.encode())
    return request


def check_expire(data):
    expire_time = None
    for datum in data:
        if 'expires=' in datum:
            found = True
            line = datum.split('expires=')[1].split('GMT')[0].split()
            expire_time = line[1] + ' ' + line[2]
            break

    if expire_time is None:
        return True  # must update
    else:
        expire = datetime.strptime(expire_time, '%d-%b-%Y %H:%M:%S')
        now = datetime.utcnow()
        return now > expire



# test get with URL http://localhost:8888/www.google.com
# test post with URL http://localhost:8888/https://ptsv2.com/t/lztm4-1613635628/post
proxy_server()
