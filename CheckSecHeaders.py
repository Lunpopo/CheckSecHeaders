#!/usr/bin/env python2
# encoding: utf8
from argparse import ArgumentParser
from argparse import SUPPRESS
import requests
import sys
import re
from termcolor import colored
import subprocess

# test Custom header with Windows 7 professor for https://www.baidu.com
custom_headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:67.0) Gecko/20100101 Firefox/67.0',
    'Accept': '*/*',
    'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
    'Accept-Encoding': 'gzip, deflate',
    'Cache-Control': 'Cache-Control: no-cache',
    'Pragma': 'no-cache',
    'Connection': 'close'
}

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
    print colored("""
 .--..           .    .-.         .   .             .
:    |           |   (   )        |   |             |
|    |--. .-. .-.|.-. `-.  .-. .-.|---| .-. .-.  .-.| .-. .--..--.
:    |  |(.-'(   |-.'(   )(.-'(   |   |(.-'(   )(   |(.-' |   `--.
 `--''  `-`--'`-''  `-`-'  `--'`-''   ' `--'`-'`-`-'`-`--''   `--'
    """, 'cyan')


def argument_parse():
    parse = ArgumentParser(description='Detecting server-end whether has setted security header',
                           add_help=False)

    helper = parse.add_argument_group('Help')
    helper.add_argument('-h', '--help', action='help', default=SUPPRESS, help="Show this help message and exit")

    mandatory = parse.add_argument_group('Mandatory Arguments')
    mandatory.add_argument('-u', '--url', dest='target_url', metavar='URL', help="Scan target URL")

    optional_argument = parse.add_argument_group('Optional Arguments')
    optional_argument.add_argument('-c', '--cookie', dest='cookies', metavar='COOKIES',
                                   help="Set cookies for URL headers, for example: "
                                        "--cookies='PS=1560911095; BR_RPN=123253;'")
    optional_argument.add_argument('-d', '--disable_ssl_check', dest='disable_ssl', action='store_true',
                                   help="disable SSL/TLS certificate")
    optional_argument.add_argument('--proxy', dest='target_proxy', metavar="PROXY_URL",
                                   help="Set proxy to request url for example: --proxy='http://127.0.0.1'")

    opts = parse.parse_args()
    return opts


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
    custom_proxy = kwargs.get('proxy', None)

    # disable_ssl 暂时不用
    # custom_disable_ssl = kwargs.get('disable_ssl', False)
    # 暂时不要, 因为我没看见报错
    # if custom_disable_ssl:
    #     context = ssl.create_default_context()
    #     context.check_hostname = False
    #     context.verify_mode = ssl.CERT_NONE
    #     context = ssl._create_unverified_context()

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


def format_color(string, format_type):
    """
    格式化颜色的

    :param string: 文本
    :param format_type: 要展示的颜色类型
    :return:
    """
    if format_type == 'ok':
        return colored(string, 'green')
    elif format_type == 'error':
        return colored(string, 'red')
    elif format_type == 'warning':
        return colored(string, 'yellow')
    else:
        return colored(string, 'red')


def display_sec_header(sec_headers):
    """
    仅仅只做输出展示

    :param sec_headers: 输入安全头字典, dic 类型
    :return: None
    """

    _ = 28*'*'
    print "{}{}{}".format(_, "服务器安全头展示", _)
    print

    for sec_header in sec_headers:
        if security_headers[sec_header]:
            print "{}: {}".format(sec_header, format_color(security_headers[sec_header], 'ok'))
        else:
            # format_color() 函数返回带有颜色的 string
            print "{}: {}".format(sec_header, format_color("未设置", 'error'))

    print
    print "{}{}{}".format(_, "服务器安全头展示", _)

    return None


def main():
    """
    接收所有的命令行参数, 然后根据 options 的参数配置去发送自定义请求

    :return: None
    """
    disable_ssl = False
    proxy = None

    if not len(sys.argv[1:]):
        popen = subprocess.Popen('python {} -h'.format(sys.argv[0]), shell=True, stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, code = popen.communicate()
        print output
    else:
        banner()

        opts = argument_parse()
        if opts.cookies:
            # 想发送自定义cookie, 接收把它加入 custom_headers
            custom_headers['Cookie'] = opts.cookies

        if opts.disable_ssl:
            disable_ssl = True

        if opts.target_proxy:
            # 这里应该判断 --proxy 的输入的格式
            proxy = opts.target_proxy

        if opts.target_url:
            normal_url = normalization_url(opts.target_url)
            # 发送请求, 获取 响应
            response = send_request(normal_url, disable_ssl=disable_ssl, proxy=proxy)

        for sec_header in security_headers:
            if sec_header in response.headers:
                security_headers[sec_header] = response.headers[sec_header]

        # 展示安全头哪些设置了, 哪些没有设置
        display_sec_header(security_headers)

        return None


if __name__ == '__main__':
    main()
