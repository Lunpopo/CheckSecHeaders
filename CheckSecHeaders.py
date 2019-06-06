#!/usr/bin/env python2
# encoding: utf8
import getopt
import requests
import sys
import re

# 测试的机型为 Windows 7 专业版，测试的 url 为 https://www.baidu.com
# test Custom header with Windows 7 professor for https://www.baidu.com
custom_headers = {
    'User-Agent': 'User-Agent: Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:67.0) Gecko/20100101 Firefox/67.0',
    'Accept': '*/*',
    'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
    'Accept-Encoding': 'gzip, deflate',
    'Cache-Control': 'Cache-Control: no-cache',
    'Pragma': 'no-cache',
    'Connection': 'close'
}

# 服务器端响应应该被设置的安全头如下
# security headers that should be setted up for
security_headers = {
    'X-XSS-Protection': False,
    'X-Frame-Options': False,
    # X-Content-Type标头提供了针对MIME嗅探的对策
    'X-Content-Type-Options': False,
    # https
    'Strict-Transport-Security': False,
    'Content-Security-Policy': False,
}


def banner():
    print """
 .--..           .    .-.         .   .             .
:    |           |   (   )        |   |             |
|    |--. .-. .-.|.-. `-.  .-. .-.|---| .-. .-.  .-.| .-. .--..--.
:    |  |(.-'(   |-.'(   )(.-'(   |   |(.-'(   )(   |(.-' |   `--.
 `--''  `-`--'`-''  `-`-'  `--'`-''   ' `--'`-'`-`-'`-`--''   `--'

[*] Check Security Headers
[*] 这是检查服务端是否设置安全头的小脚本
[*] This is check if server has setted up security headers small script
[*] 我爱中国！
[*] I Love China!
------------------------------------------------------------------------
"""


ENGLISH_BUTTON = False


def english_helper():
    """
    This function aim to show detail English helper for this script

    :return:
    """

    banner()

    print
    print '-h                      Show Help'
    print '--help'
    print
    print '-e                      Show English Help'
    print '--english_help'
    print
    print '-c COOKIES              Set Cookies for URL Headers'
    print '--cookie="COOKIES"'
    print
    print '-d                      disable SSL/TLS certificate'
    print '--disable_ssl_check'
    print
    print '--proxy="PROXY_URL"     Set proxy to request url'
    print '                        for example: --proxy="http://127.0.0.1"'


def usage():
    """
    这是一个使用方法, 包含所有的 options 和说明

    :return: None
    """

    # banner()

    print
    print '-h                      展示此脚本的帮助信息'
    print '--help'
    print
    print '-e                      show English help'
    print '--english_help'
    print
    print '-c COOKIES              设置 cookies 到 headers 中'
    print '--cookie="COOKIES"'
    print
    print '-d                      关闭 SSL/TLS 证书验证'
    print '--disable_ssl'
    print
    print '--proxy="PROXY_URL"     设置一个代理, 例如: http://127.0.0.1'

    sys.exit(0)


def normalization_url(url):
    """
    正常化 url, 把不正规的 url 转换为正常化 url

    :param url: url
    :return: url -> 正常化之后的 url
    """

    search_http = re.compile('^http(s)?://')
    search_result = search_http.search(url)

    if search_result is not None:
        # 说明满足 http(s)://*.* 的格式
        return url
    else:
        # 不满足 http(s)://*.* 的格式
        if 'http' == url[0:4]:
            # 不满足 http(s):// 的格式, 但是开头又有 http, 有可能是输入失误, 例如: http:/www.example.org/path/path_1 这种
            if ':/' == url[4:6] or ':/' == url[5:7]:
                # 输入成了 http:/www.example.org/ 或者 https://www.example.org, 帮忙补齐就行了
                url = "://".join(url.split(':/'))
                return url
            else:
                # 都不属于, 那就直接报错算了
                raise "-u or --url 参数错误, 请在检查一遍"
                sys.exit(1)
        else:
            # 可能忘了输入 http(s) 协议, 帮忙添加
            url = "http://" + url
            return url


def send_request(url, **kwargs):
    """
    发送请求到 url, 带上 cookies 的 header(如果有), 带上 代理（如果开启了代理）, 然后返回服务器的 response

    :param url: url
    :param kwargs:
        cookie, 如果指定了 -c --cookie 选项
        proxy, 如果指定了 -p --proxy 选项
    :return:
    """

    custom_cookie = kwargs.get('cookie', None)
    # disable_ssl 暂时不用
    # custom_disable_ssl = kwargs.get('disable_ssl', False)
    custom_proxy = kwargs.get('proxy', None)

    # 暂时不要, 因为我没看见报错
    # if custom_disable_ssl:
    #     context = ssl.create_default_context()
    #     context.check_hostname = False
    #     context.verify_mode = ssl.CERT_NONE
    #     context = ssl._create_unverified_context()

    # 如果指定了 -c --cookie, 就添加进 custom_headers 中
    if custom_cookie is not None:
        custom_headers['Cookie'] = custom_cookie

    # 指定了 proxy
    if custom_proxy is not None:
        # socks5 也是写的 http 和 https
        # custom_proxy 的格式应该是 127.0.0.1:8080 这种
        proxies = {
            'http': 'http://' + custom_proxy,
            'https': 'https://' + custom_proxy
        }
    else:
        proxies = None

    try:
        response = requests.get(url, headers=custom_headers, proxies=proxies, timeout=10)
    except requests.exceptions.ConnectionError as e:
        print str(e)
        exit(1)

    return response


def format_color(string, type):
    """
    格式化颜色的

    :param string: 文本
    :param type: 要展示的颜色类型
    :return:
    """

    color = {
        'error': '\033[0;31;31m {} \033[0m',
        'ok': '\033[1;32m {} \033[0m',
        'warning': '\033[4;33m {} \033[0m'
    }

    return color.get(type).format(string)


def display_sec_header(security_headers):
    """
    仅仅只做输出展示

    :param security_headers: 输入安全头字典, dic 类型
    :return: None
    """

    banner()

    _ = 28*'*'
    print "{}{}{}".format(_, "服务器安全头展示", _)
    print

    for sec_header in security_headers:
        if security_headers[sec_header]:
            print "{}: {}".format(sec_header, format_color(security_headers[sec_header], 'ok'))
        else:
            # format_color() 函数返回带有颜色的 string
            print "{}: {}".format(sec_header, format_color("未设置", 'error'))

    print
    print "{}{}{}".format(_, "服务器安全头展示", _)


def main():
    """
    接收所有的命令行参数, 然后根据 options 的参数配置去发送自定义请求

    :return:
    """

    custom_url = None
    custom_port = 80
    custom_cookie = None
    disable_ssl = False
    proxy = None

    try:
        args, opts = getopt.getopt(sys.argv[1:], 'heu:c:d', ['help', 'url=', 'cookie=', 'proxy='])
    except getopt.GetoptError:
        usage()

    for o, a in args:
        if ('-h' or '--help') in o:
            usage()
        elif ('-e' or '--english_help') in o:
            english_helper()
            # 打开全局 English 开关
            ENGLISH_BUTTON = True
        elif ('-u' or '--url') in o:
            # 格式化 url, 格式化函数可以做成一个 格式化 类, 然后不同的格式化方法
            a = normalization_url(a)
            custom_url = a
        elif ('-c' or '--cookie') in o:
            # 想发送自定义cookie, 接收把它加入 custom_headers 中, 最后去发送
            # 这里应该判断获取的 cookie 的格式
            custom_cookie = a
        elif ('-d' or '--disable_ssl') in o:
            disable_ssl = True
        elif '--proxy' in o:
            # 这里应该判断 --proxy 的输入的格式
            proxy = a
        else:
            usage()

    # 发送请求, 获取 响应
    response = send_request(custom_url, cookie=custom_cookie, disable_ssl=disable_ssl, proxy=proxy)

    print

    for sec_header in security_headers:
        if sec_header in response.headers:
            security_headers[sec_header] = response.headers[sec_header]

    # 展示安全头哪些设置了, 哪些没有设置
    display_sec_header(security_headers)


if __name__ == '__main__':
    main()

