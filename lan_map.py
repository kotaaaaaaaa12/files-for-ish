#!/usr/bin/env python3
“””
LAN Network Map - IPアドレスを中心にネットワーク端末を可視化するやつ
使い方: python3 lan_map.py
ブラウザで http://localhost:8080 を開いてや
“””

import subprocess
import socket
import json
import re
import ipaddress
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from concurrent.futures import ThreadPoolExecutor, as_completed

# MACアドレスからベンダー判定するやつ（主要OUIプレフィックス）

MAC_VENDOR_MAP = {
# Apple
“00:1C:B3”: “Apple”, “00:23:32”: “Apple”, “00:26:B9”: “Apple”,
“28:CF:E9”: “Apple”, “3C:07:54”: “Apple”, “60:F8:1D”: “Apple”,
“68:AB:BC”: “Apple”, “70:EC:E4”: “Apple”, “88:1F:A1”: “Apple”,
“A4:C3:61”: “Apple”, “AC:BC:32”: “Apple”, “B8:53:AC”: “Apple”,
“D8:96:95”: “Apple”, “F0:B4:79”: “Apple”, “F4:37:B7”: “Apple”,
“00:03:93”: “Apple”, “00:0A:27”: “Apple”, “00:0A:95”: “Apple”,
“00:0D:93”: “Apple”, “00:11:24”: “Apple”, “00:14:51”: “Apple”,
“00:16:CB”: “Apple”, “00:17:F2”: “Apple”, “00:19:E3”: “Apple”,
“00:1B:63”: “Apple”, “00:1D:4F”: “Apple”, “00:1E:52”: “Apple”,
“00:1F:5B”: “Apple”, “00:1F:F3”: “Apple”, “00:21:E9”: “Apple”,
“00:22:41”: “Apple”, “00:23:DF”: “Apple”, “00:25:00”: “Apple”,
“00:25:BC”: “Apple”, “00:26:08”: “Apple”, “00:26:4A”: “Apple”,
“00:26:BB”: “Apple”, “00:30:65”: “Apple”, “00:3E:E1”: “Apple”,
“04:0C:CE”: “Apple”, “04:15:52”: “Apple”, “04:1E:64”: “Apple”,
“04:26:65”: “Apple”, “04:54:53”: “Apple”, “04:69:F8”: “Apple”,
“04:D3:CF”: “Apple”, “04:E5:36”: “Apple”, “08:00:07”: “Apple”,
“08:6D:41”: “Apple”, “08:70:45”: “Apple”, “0C:3E:9F”: “Apple”,
“0C:74:C2”: “Apple”, “0C:77:1A”: “Apple”, “10:1C:0C”: “Apple”,
“10:40:F3”: “Apple”, “10:93:E9”: “Apple”, “10:9A:DD”: “Apple”,
“10:DD:B1”: “Apple”, “14:10:9F”: “Apple”, “14:20:5E”: “Apple”,
“14:5A:05”: “Apple”, “14:8F:C6”: “Apple”, “14:99:E2”: “Apple”,
“18:20:32”: “Apple”, “18:34:51”: “Apple”, “18:65:90”: “Apple”,
“18:9E:FC”: “Apple”, “18:AF:61”: “Apple”, “18:E7:F4”: “Apple”,
“1C:1A:C0”: “Apple”, “1C:36:BB”: “Apple”, “1C:5C:F2”: “Apple”,
“1C:AB:A7”: “Apple”, “1C:E6:2B”: “Apple”, “20:78:4A”: “Apple”,
“20:A2:E4”: “Apple”, “20:AB:37”: “Apple”, “20:C9:D0”: “Apple”,
“24:1E:EB”: “Apple”, “24:5B:A7”: “Apple”, “24:A0:74”: “Apple”,
“24:AB:81”: “Apple”, “28:0B:5C”: “Apple”, “28:37:37”: “Apple”,
“28:6A:BA”: “Apple”, “28:A0:2B”: “Apple”, “2C:1F:23”: “Apple”,
“2C:20:0B”: “Apple”, “2C:BE:08”: “Apple”, “2C:F0:EE”: “Apple”,
“30:10:E4”: “Apple”, “30:35:AD”: “Apple”, “30:90:AB”: “Apple”,
“30:F7:C5”: “Apple”, “34:12:98”: “Apple”, “34:15:9E”: “Apple”,
“34:36:3B”: “Apple”, “34:51:C9”: “Apple”, “34:C0:59”: “Apple”,
“38:0F:4A”: “Apple”, “38:48:4C”: “Apple”, “38:53:9C”: “Apple”,
“38:66:F0”: “Apple”, “38:B5:4D”: “Apple”, “3C:15:C2”: “Apple”,
“3C:2E:F9”: “Apple”, “3C:D0:F8”: “Apple”, “40:30:04”: “Apple”,
“40:33:1A”: “Apple”, “40:40:A7”: “Apple”, “40:4D:7F”: “Apple”,
“40:6C:8F”: “Apple”, “40:83:1D”: “Apple”, “40:A6:D9”: “Apple”,
“40:B3:95”: “Apple”, “40:BC:60”: “Apple”, “40:CB:C0”: “Apple”,
“40:D3:2D”: “Apple”, “44:00:10”: “Apple”, “44:2A:60”: “Apple”,
“44:4C:0C”: “Apple”, “44:D8:84”: “Apple”, “48:43:7C”: “Apple”,
“48:60:BC”: “Apple”, “48:74:6E”: “Apple”, “48:A1:95”: “Apple”,
“48:BF:6B”: “Apple”, “48:D7:05”: “Apple”, “4C:32:75”: “Apple”,
“4C:57:CA”: “Apple”, “4C:74:03”: “Apple”, “4C:7C:5F”: “Apple”,
“4C:8D:79”: “Apple”, “50:32:75”: “Apple”, “50:7A:55”: “Apple”,
“50:BC:96”: “Apple”, “50:DE:06”: “Apple”, “50:EA:D6”: “Apple”,
“54:26:96”: “Apple”, “54:33:CB”: “Apple”, “54:4E:90”: “Apple”,
“54:72:4F”: “Apple”, “54:9F:13”: “Apple”, “54:AE:27”: “Apple”,
“54:E4:3A”: “Apple”, “58:1F:AA”: “Apple”, “58:40:4E”: “Apple”,
“58:55:CA”: “Apple”, “58:7F:57”: “Apple”, “58:B0:35”: “Apple”,
“5C:1D:D9”: “Apple”, “5C:59:48”: “Apple”, “5C:95:AE”: “Apple”,
“5C:AD:CF”: “Apple”, “5C:F9:38”: “Apple”, “60:03:08”: “Apple”,
“60:33:4B”: “Apple”, “60:69:44”: “Apple”, “60:92:17”: “Apple”,
“60:C5:47”: “Apple”, “60:D9:C7”: “Apple”, “60:F4:45”: “Apple”,
“60:FA:CD”: “Apple”, “60:FB:42”: “Apple”, “64:20:0C”: “Apple”,
“64:76:BA”: “Apple”, “64:9A:BE”: “Apple”, “64:A3:CB”: “Apple”,
“64:B9:E8”: “Apple”, “64:E6:82”: “Apple”, “68:09:27”: “Apple”,
“68:5B:35”: “Apple”, “68:64:4B”: “Apple”, “68:96:7B”: “Apple”,
“68:9C:70”: “Apple”, “68:A8:6D”: “Apple”, “6C:19:C0”: “Apple”,
“6C:40:08”: “Apple”, “6C:70:9F”: “Apple”, “6C:72:E7”: “Apple”,
“6C:94:F8”: “Apple”, “6C:C2:6B”: “Apple”, “70:11:24”: “Apple”,
“70:14:A6”: “Apple”, “70:3E:AC”: “Apple”, “70:56:81”: “Apple”,
“70:73:CB”: “Apple”, “70:CD:60”: “Apple”, “70:DE:E2”: “Apple”,
“74:1B:B2”: “Apple”, “74:E1:B6”: “Apple”, “74:E2:F5”: “Apple”,
“78:31:C1”: “Apple”, “78:4F:43”: “Apple”, “78:67:D7”: “Apple”,
“78:6C:1C”: “Apple”, “78:7B:8A”: “Apple”, “78:CA:39”: “Apple”,
“78:D7:5F”: “Apple”, “78:FD:94”: “Apple”, “7C:01:91”: “Apple”,
“7C:11:BE”: “Apple”, “7C:50:49”: “Apple”, “7C:6D:62”: “Apple”,
“7C:C3:A1”: “Apple”, “7C:D1:C3”: “Apple”, “7C:FA:DF”: “Apple”,
“80:00:6E”: “Apple”, “80:49:71”: “Apple”, “80:82:23”: “Apple”,
“80:92:9F”: “Apple”, “80:BE:05”: “Apple”, “80:E6:50”: “Apple”,
“84:29:99”: “Apple”, “84:38:35”: “Apple”, “84:3A:4B”: “Apple”,
“84:41:67”: “Apple”, “84:78:8B”: “Apple”, “84:85:06”: “Apple”,
“84:8E:0C”: “Apple”, “84:B1:53”: “Apple”, “84:FC:FE”: “Apple”,
“88:19:08”: “Apple”, “88:53:2E”: “Apple”, “88:63:DF”: “Apple”,
“88:66:5A”: “Apple”, “88:AE:07”: “Apple”, “88:B9:45”: “Apple”,
“88:C6:63”: “Apple”, “88:CB:87”: “Apple”, “88:E9:FE”: “Apple”,
“8C:00:6D”: “Apple”, “8C:29:37”: “Apple”, “8C:2D:AA”: “Apple”,
“8C:58:77”: “Apple”, “8C:7C:92”: “Apple”, “8C:7B:9D”: “Apple”,
“8C:85:90”: “Apple”, “8C:8D:28”: “Apple”, “90:27:E4”: “Apple”,
“90:3C:92”: “Apple”, “90:60:F0”: “Apple”, “90:72:40”: “Apple”,
“90:84:0D”: “Apple”, “90:8D:6C”: “Apple”, “90:B0:ED”: “Apple”,
“90:B2:1F”: “Apple”, “90:B9:31”: “Apple”, “90:C1:C6”: “Apple”,
“90:DD:5D”: “Apple”, “90:FD:61”: “Apple”, “94:BF:2D”: “Apple”,
“94:E9:6A”: “Apple”, “94:F6:65”: “Apple”, “98:01:A7”: “Apple”,
“98:03:D8”: “Apple”, “98:10:E7”: “Apple”, “98:46:0A”: “Apple”,
“98:9E:63”: “Apple”, “98:B8:E3”: “Apple”, “98:D6:BB”: “Apple”,
“98:E0:D9”: “Apple”, “98:F0:AB”: “Apple”, “9C:04:EB”: “Apple”,
“9C:20:7B”: “Apple”, “9C:35:EB”: “Apple”, “9C:4F:DA”: “Apple”,
“9C:84:BF”: “Apple”, “9C:8B:A0”: “Apple”, “9C:F3:87”: “Apple”,
“A0:18:28”: “Apple”, “A0:33:62”: “Apple”, “A0:3B:E3”: “Apple”,
“A0:99:9B”: “Apple”, “A0:D7:95”: “Apple”, “A0:ED:CD”: “Apple”,
“A4:5E:60”: “Apple”, “A4:83:E7”: “Apple”, “A4:B1:97”: “Apple”,
“A4:D1:8C”: “Apple”, “A8:20:66”: “Apple”, “A8:5C:2C”: “Apple”,
“A8:60:B6”: “Apple”, “A8:86:DD”: “Apple”, “A8:8E:24”: “Apple”,
“A8:96:8A”: “Apple”, “A8:FA:D8”: “Apple”, “AC:1F:74”: “Apple”,
“AC:29:3A”: “Apple”, “AC:3C:0B”: “Apple”, “AC:61:EA”: “Apple”,
“AC:7F:3E”: “Apple”, “AC:87:A3”: “Apple”, “AC:E4:B5”: “Apple”,
“B0:34:95”: “Apple”, “B0:65:BD”: “Apple”, “B0:70:2D”: “Apple”,
“B4:18:D1”: “Apple”, “B4:4B:D2”: “Apple”, “B4:8B:19”: “Apple”,
“B4:9C:A3”: “Apple”, “B8:09:8A”: “Apple”, “B8:17:C2”: “Apple”,
“B8:41:A4”: “Apple”, “B8:53:AC”: “Apple”, “B8:5D:0A”: “Apple”,
“B8:5E:7B”: “Apple”, “B8:63:4D”: “Apple”, “B8:78:2E”: “Apple”,
“B8:8D:12”: “Apple”, “B8:C7:5D”: “Apple”, “B8:E8:56”: “Apple”,
“B8:FF:61”: “Apple”, “BC:3B:AF”: “Apple”, “BC:4C:C4”: “Apple”,
“BC:52:B7”: “Apple”, “BC:67:78”: “Apple”, “BC:9F:EF”: “Apple”,
“C0:1A:DA”: “Apple”, “C0:63:94”: “Apple”, “C0:9F:42”: “Apple”,
“C0:A5:3E”: “Apple”, “C0:CE:CD”: “Apple”, “C0:D0:12”: “Apple”,
“C4:2C:03”: “Apple”, “C4:61:8B”: “Apple”, “C4:B3:01”: “Apple”,
“C8:1E:E7”: “Apple”, “C8:2A:14”: “Apple”, “C8:33:4B”: “Apple”,
“C8:6F:1D”: “Apple”, “C8:69:CD”: “Apple”, “C8:85:50”: “Apple”,
“C8:B5:B7”: “Apple”, “C8:BC:C8”: “Apple”, “C8:D0:83”: “Apple”,
“C8:E0:EB”: “Apple”, “C8:F6:50”: “Apple”, “CC:08:8D”: “Apple”,
“CC:20:E8”: “Apple”, “CC:25:EF”: “Apple”, “CC:29:F5”: “Apple”,
“CC:44:63”: “Apple”, “CC:78:5F”: “Apple”, “D0:03:4B”: “Apple”,
“D0:23:DB”: “Apple”, “D0:33:11”: “Apple”, “D0:4F:7E”: “Apple”,
“D0:81:7A”: “Apple”, “D0:A6:37”: “Apple”, “D0:C5:F3”: “Apple”,
“D0:E1:40”: “Apple”, “D4:20:B0”: “Apple”, “D4:61:9D”: “Apple”,
“D4:9A:20”: “Apple”, “D4:DC:CD”: “Apple”, “D4:F4:6F”: “Apple”,
“D8:00:4D”: “Apple”, “D8:1D:72”: “Apple”, “D8:30:62”: “Apple”,
“D8:9E:3F”: “Apple”, “D8:A2:5E”: “Apple”, “D8:BB:2C”: “Apple”,
“DC:0C:5C”: “Apple”, “DC:2B:2A”: “Apple”, “DC:2B:61”: “Apple”,
“DC:37:45”: “Apple”, “DC:9B:9C”: “Apple”, “DC:A4:CA”: “Apple”,
“DC:A9:04”: “Apple”, “E0:66:78”: “Apple”, “E0:B5:5F”: “Apple”,
“E0:C7:67”: “Apple”, “E0:F5:C6”: “Apple”, “E4:25:E7”: “Apple”,
“E4:2B:34”: “Apple”, “E4:98:BB”: “Apple”, “E4:98:D6”: “Apple”,
“E4:9B:D2”: “Apple”, “E4:C6:3D”: “Apple”, “E4:CE:8F”: “Apple”,
“E4:E0:A6”: “Apple”, “E8:04:0B”: “Apple”, “E8:06:88”: “Apple”,
“E8:80:2E”: “Apple”, “E8:B2:AC”: “Apple”, “EC:35:86”: “Apple”,
“EC:85:2F”: “Apple”, “EC:AD:B8”: “Apple”, “F0:24:75”: “Apple”,
“F0:98:9D”: “Apple”, “F0:99:BF”: “Apple”, “F0:B0:E7”: “Apple”,
“F0:C1:F1”: “Apple”, “F0:CB:A1”: “Apple”, “F0:D1:A9”: “Apple”,
“F0:DB:F8”: “Apple”, “F0:DC:E2”: “Apple”, “F0:F6:1C”: “Apple”,
“F4:0F:24”: “Apple”, “F4:1B:A1”: “Apple”, “F4:31:C3”: “Apple”,
“F4:37:B7”: “Apple”, “F4:5C:89”: “Apple”, “F4:F1:5A”: “Apple”,
“F8:27:93”: “Apple”, “F8:2F:A8”: “Apple”, “F8:62:14”: “Apple”,
“F8:FF:C2”: “Apple”, “FC:25:3F”: “Apple”, “FC:2A:9C”: “Apple”,
“FC:E9:98”: “Apple”, “FC:FC:48”: “Apple”,
# Samsung
“00:00:F0”: “Samsung”, “00:07:AB”: “Samsung”, “00:12:47”: “Samsung”,
“00:15:99”: “Samsung”, “00:16:32”: “Samsung”, “00:16:6B”: “Samsung”,
“00:16:DB”: “Samsung”, “00:17:C9”: “Samsung”, “00:17:D5”: “Samsung”,
“00:18:AF”: “Samsung”, “00:1A:8A”: “Samsung”, “00:1B:98”: “Samsung”,
“00:1C:43”: “Samsung”, “00:1D:25”: “Samsung”, “00:1E:7D”: “Samsung”,
“00:1F:CC”: “Samsung”, “00:21:19”: “Samsung”, “00:21:D1”: “Samsung”,
“00:21:D2”: “Samsung”, “00:23:39”: “Samsung”, “00:23:3A”: “Samsung”,
“00:24:54”: “Samsung”, “00:24:91”: “Samsung”, “00:25:38”: “Samsung”,
“00:25:66”: “Samsung”, “00:26:37”: “Samsung”, “08:08:C2”: “Samsung”,
“08:D4:2B”: “Samsung”, “08:FC:88”: “Samsung”, “0C:14:20”: “Samsung”,
“0C:71:5D”: “Samsung”, “10:1D:C0”: “Samsung”, “10:30:47”: “Samsung”,
“10:D3:8A”: “Samsung”, “14:49:E0”: “Samsung”, “14:89:FD”: “Samsung”,
“18:22:7E”: “Samsung”, “18:26:66”: “Samsung”, “18:3A:2D”: “Samsung”,
“18:AF:8F”: “Samsung”, “1C:3A:DE”: “Samsung”, “1C:5A:3E”: “Samsung”,
“1C:66:AA”: “Samsung”, “20:55:31”: “Samsung”, “24:4B:81”: “Samsung”,
“24:92:0E”: “Samsung”, “28:27:BF”: “Samsung”, “28:39:5E”: “Samsung”,
“28:CC:01”: “Samsung”, “2C:AE:2B”: “Samsung”, “30:19:66”: “Samsung”,
“30:96:FB”: “Samsung”, “34:23:87”: “Samsung”, “34:31:11”: “Samsung”,
“34:AA:8B”: “Samsung”, “34:BE:00”: “Samsung”, “38:01:97”: “Samsung”,
“38:AA:3C”: “Samsung”, “3C:5A:37”: “Samsung”, “3C:62:00”: “Samsung”,
“3C:8B:FE”: “Samsung”, “3C:BD:D8”: “Samsung”, “40:0E:85”: “Samsung”,
“44:4E:1A”: “Samsung”, “44:6D:57”: “Samsung”, “44:78:3E”: “Samsung”,
“44:F4:59”: “Samsung”, “48:44:F7”: “Samsung”, “48:5A:3F”: “Samsung”,
“4C:3C:16”: “Samsung”, “4C:66:41”: “Samsung”, “4C:A5:6D”: “Samsung”,
“4C:BC:A5”: “Samsung”, “50:01:BB”: “Samsung”, “50:32:37”: “Samsung”,
“50:85:69”: “Samsung”, “50:A4:C8”: “Samsung”, “50:CC:F8”: “Samsung”,
“50:F0:D3”: “Samsung”, “54:40:AD”: “Samsung”, “54:92:BE”: “Samsung”,
“54:9B:12”: “Samsung”, “58:CB:52”: “Samsung”, “5C:0A:5B”: “Samsung”,
“5C:3C:27”: “Samsung”, “5C:49:7D”: “Samsung”, “5C:51:88”: “Samsung”,
“60:6B:BD”: “Samsung”, “60:A1:0A”: “Samsung”, “60:D0:A9”: “Samsung”,
“64:27:37”: “Samsung”, “64:B3:10”: “Samsung”, “68:27:37”: “Samsung”,
“68:48:98”: “Samsung”, “6C:2F:2C”: “Samsung”, “6C:83:36”: “Samsung”,
“70:F9:27”: “Samsung”, “74:45:8A”: “Samsung”, “74:57:B8”: “Samsung”,
“74:6A:89”: “Samsung”, “78:1F:DB”: “Samsung”, “78:25:AD”: “Samsung”,
“78:40:E4”: “Samsung”, “78:52:1A”: “Samsung”, “78:9E:D0”: “Samsung”,
“78:A8:73”: “Samsung”, “7C:0B:C6”: “Samsung”, “7C:1C:4E”: “Samsung”,
“7C:61:66”: “Samsung”, “7C:64:56”: “Samsung”, “80:65:6D”: “Samsung”,
“80:A5:89”: “Samsung”, “84:25:DB”: “Samsung”, “84:38:35”: “Samsung”,
“84:55:A5”: “Samsung”, “84:98:66”: “Samsung”, “88:32:9B”: “Samsung”,
“88:36:6C”: “Samsung”, “88:9B:39”: “Samsung”, “8C:71:F8”: “Samsung”,
“8C:77:12”: “Samsung”, “90:18:7C”: “Samsung”, “90:C1:15”: “Samsung”,
“94:01:C2”: “Samsung”, “94:35:0A”: “Samsung”, “94:51:03”: “Samsung”,
“98:52:B1”: “Samsung”, “98:8E:79”: “Samsung”, “9C:02:98”: “Samsung”,
“9C:3A:AF”: “Samsung”, “A0:82:1F”: “Samsung”, “A4:07:B6”: “Samsung”,
“A4:EB:D3”: “Samsung”, “A8:06:00”: “Samsung”, “A8:9A:93”: “Samsung”,
“AC:5F:3E”: “Samsung”, “AC:61:75”: “Samsung”, “B0:47:BF”: “Samsung”,
“B0:72:BF”: “Samsung”, “B4:07:F9”: “Samsung”, “B8:5E:7B”: “Samsung”,
“BC:14:85”: “Samsung”, “BC:20:A4”: “Samsung”, “BC:44:86”: “Samsung”,
“BC:72:B1”: “Samsung”, “BC:85:1F”: “Samsung”, “C4:42:02”: “Samsung”,
“C4:88:E5”: “Samsung”, “C8:19:F7”: “Samsung”, “CC:07:AB”: “Samsung”,
“D0:22:BE”: “Samsung”, “D0:59:E4”: “Samsung”, “D4:87:D8”: “Samsung”,
“D8:57:EF”: “Samsung”, “D8:90:E8”: “Samsung”, “DC:71:96”: “Samsung”,
“E0:CB:EE”: “Samsung”, “E4:12:1D”: “Samsung”, “E4:32:CB”: “Samsung”,
“E4:40:E2”: “Samsung”, “E8:50:8B”: “Samsung”, “EC:9B:F3”: “Samsung”,
“F0:08:F1”: “Samsung”, “F0:25:B7”: “Samsung”, “F4:09:D8”: “Samsung”,
“F4:42:8F”: “Samsung”, “F8:77:B8”: “Samsung”, “FC:F1:36”: “Samsung”,
# Google (Pixel, Chromecast, Nest)
“00:1A:11”: “Google”, “3C:5A:B4”: “Google”, “54:60:09”: “Google”,
“6C:AD:F8”: “Google”, “94:EB:2C”: “Google”, “F4:F5:D8”: “Google”,
“1C:F2:9A”: “Google”, “48:D6:D5”: “Google”, “58:CB:52”: “Google”,
“A4:77:58”: “Google”, “D0:0A:38”: “Google”,
# Sony
“00:01:4A”: “Sony”, “00:04:1F”: “Sony”, “00:0A:87”: “Sony”,
“00:13:A9”: “Sony”, “00:1A:80”: “Sony”, “00:1D:0D”: “Sony”,
“00:24:BE”: “Sony”, “28:0D:FC”: “Sony”, “2C:A5:61”: “Sony”,
“30:17:C8”: “Sony”, “40:B0:FA”: “Sony”, “4C:B9:9B”: “Sony”,
“54:A2:93”: “Sony”, “5C:AD:CF”: “Sony”, “60:D8:19”: “Sony”,
“64:6E:69”: “Sony”, “70:26:05”: “Sony”, “70:3E:AC”: “Sony”,
“78:84:3C”: “Sony”, “84:C7:EA”: “Sony”, “90:C1:15”: “Sony”,
“94:CE:2C”: “Sony”, “98:0C:A5”: “Sony”, “A0:E4:53”: “Sony”,
“BC:60:A7”: “Sony”,
# Microsoft / Xbox
“00:02:44”: “Microsoft”, “00:12:5A”: “Microsoft”, “00:15:5D”: “Microsoft”,
“00:17:FA”: “Microsoft”, “00:1D:D8”: “Microsoft”, “00:22:48”: “Microsoft”,
“00:50:F2”: “Microsoft”, “28:18:78”: “Microsoft”, “3C:83:75”: “Microsoft”,
“40:01:7A”: “Microsoft”, “48:0F:CF”: “Microsoft”, “50:1A:C5”: “Microsoft”,
“54:27:1E”: “Microsoft”, “5C:BA:EF”: “Microsoft”, “60:45:BD”: “Microsoft”,
“7C:1E:52”: “Microsoft”, “80:E6:50”: “Microsoft”, “84:30:26”: “Microsoft”,
“98:5F:D3”: “Microsoft”, “AC:1C:52”: “Microsoft”, “B8:CA:3A”: “Microsoft”,
“C4:9D:ED”: “Microsoft”, “DC:4A:3E”: “Microsoft”, “E8:D0:55”: “Microsoft”,
“F4:CE:46”: “Microsoft”,
# Raspberry Pi
“B8:27:EB”: “Raspberry Pi”, “DC:A6:32”: “Raspberry Pi”, “E4:5F:01”: “Raspberry Pi”,
“28:CD:C1”: “Raspberry Pi”,
# Amazon (Echo, Kindle, FireTV)
“00:BB:3A”: “Amazon”, “0C:47:C9”: “Amazon”, “34:D2:70”: “Amazon”,
“38:F7:3D”: “Amazon”, “40:B4:CD”: “Amazon”, “44:65:0D”: “Amazon”,
“50:F5:DA”: “Amazon”, “68:54:FD”: “Amazon”, “74:75:48”: “Amazon”,
“74:C2:46”: “Amazon”, “78:E1:03”: “Amazon”, “84:D6:D0”: “Amazon”,
“88:71:E5”: “Amazon”, “A0:02:DC”: “Amazon”, “A4:08:EA”: “Amazon”,
“AC:63:BE”: “Amazon”, “B4:7C:9C”: “Amazon”, “CC:F7:35”: “Amazon”,
“D0:F8:8C”: “Amazon”, “E4:95:6E”: “Amazon”, “F0:4F:7C”: “Amazon”,
“F0:81:73”: “Amazon”, “FC:A1:83”: “Amazon”,
# Nintendo Switch
“00:09:BF”: “Nintendo”, “00:16:56”: “Nintendo”, “00:17:AB”: “Nintendo”,
“00:19:1D”: “Nintendo”, “00:1A:E9”: “Nintendo”, “00:1B:EA”: “Nintendo”,
“00:1C:BE”: “Nintendo”, “00:1E:35”: “Nintendo”, “00:1F:32”: “Nintendo”,
“00:21:47”: “Nintendo”, “00:22:D7”: “Nintendo”, “00:24:1E”: “Nintendo”,
“00:24:F3”: “Nintendo”, “00:25:A0”: “Nintendo”, “34:AF:2C”: “Nintendo”,
“40:D2:8A”: “Nintendo”, “58:2F:40”: “Nintendo”, “78:A2:A0”: “Nintendo”,
“8C:56:C5”: “Nintendo”, “98:B6:E9”: “Nintendo”, “A4:C0:E1”: “Nintendo”,
“B8:AE:6E”: “Nintendo”, “D8:6B:F7”: “Nintendo”, “E0:E7:51”: “Nintendo”,
# Huawei
“00:18:82”: “Huawei”, “00:1E:10”: “Huawei”, “00:25:9E”: “Huawei”,
“04:75:03”: “Huawei”, “08:7A:4C”: “Huawei”, “0C:37:DC”: “Huawei”,
“10:47:80”: “Huawei”, “10:C6:1F”: “Huawei”, “18:C5:8A”: “Huawei”,
“1C:8E:5C”: “Huawei”, “20:0B:C7”: “Huawei”, “24:69:A5”: “Huawei”,
“24:DA:33”: “Huawei”, “28:3C:E4”: “Huawei”, “2C:AB:00”: “Huawei”,
“2C:CF:2B”: “Huawei”, “30:D1:7E”: “Huawei”, “30:D3:2D”: “Huawei”,
“34:6B:D3”: “Huawei”, “34:A8:4E”: “Huawei”, “38:F8:89”: “Huawei”,
“3C:47:11”: “Huawei”, “40:CB:A8”: “Huawei”, “44:6A:2E”: “Huawei”,
“48:46:FB”: “Huawei”, “48:4D:FE”: “Huawei”, “4C:1F:CC”: “Huawei”,
“50:9F:27”: “Huawei”, “54:51:1B”: “Huawei”, “54:89:98”: “Huawei”,
“58:2A:F7”: “Huawei”, “5C:4C:A9”: “Huawei”, “5C:7D:5E”: “Huawei”,
“60:14:66”: “Huawei”, “60:DE:44”: “Huawei”, “64:3E:8C”: “Huawei”,
“68:89:C1”: “Huawei”, “6C:8D:C1”: “Huawei”, “6C:96:CF”: “Huawei”,
“6C:C7:EC”: “Huawei”, “70:72:3C”: “Huawei”, “70:8A:09”: “Huawei”,
“74:A0:2F”: “Huawei”, “74:DE:2B”: “Huawei”, “78:1D:BA”: “Huawei”,
“7C:A2:3E”: “Huawei”, “80:71:7A”: “Huawei”, “80:B6:86”: “Huawei”,
“84:74:2A”: “Huawei”, “84:AD:58”: “Huawei”, “84:DB:2F”: “Huawei”,
“88:A2:5E”: “Huawei”, “88:CF:98”: “Huawei”, “8C:25:05”: “Huawei”,
“8C:34:FD”: “Huawei”, “90:17:AC”: “Huawei”, “90:67:1C”: “Huawei”,
“94:04:9C”: “Huawei”, “9C:28:EF”: “Huawei”, “9C:B2:B2”: “Huawei”,
“A0:08:6F”: “Huawei”, “A4:99:47”: “Huawei”, “A8:CA:7B”: “Huawei”,
“AC:E2:15”: “Huawei”, “B0:E5:ED”: “Huawei”, “B4:15:13”: “Huawei”,
“BC:76:70”: “Huawei”, “BC:96:80”: “Huawei”, “C4:05:28”: “Huawei”,
“C4:07:2F”: “Huawei”, “C4:F0:81”: “Huawei”, “C8:14:79”: “Huawei”,
“C8:51:95”: “Huawei”, “CC:53:B5”: “Huawei”, “D0:7A:B5”: “Huawei”,
“D4:12:43”: “Huawei”, “D4:20:6D”: “Huawei”, “D4:6A:A8”: “Huawei”,
“D4:6E:5C”: “Huawei”, “D8:49:0B”: “Huawei”, “DC:D2:FC”: “Huawei”,
“E0:19:54”: “Huawei”, “E0:1C:41”: “Huawei”, “E0:24:7F”: “Huawei”,
“E4:68:A3”: “Huawei”, “E8:08:8B”: “Huawei”, “E8:4D:D0”: “Huawei”,
“EC:23:3D”: “Huawei”, “F4:42:8F”: “Huawei”, “F4:4C:7F”: “Huawei”,
“F4:63:1F”: “Huawei”, “F4:9F:F3”: “Huawei”, “F8:01:13”: “Huawei”,
“F8:3D:FF”: “Huawei”, “FC:3F:DB”: “Huawei”, “FC:48:EF”: “Huawei”,
# Xiaomi
“00:9E:C8”: “Xiaomi”, “10:2A:B3”: “Xiaomi”, “14:F6:5A”: “Xiaomi”,
“18:59:36”: “Xiaomi”, “1C:5F:2B”: “Xiaomi”, “28:6C:07”: “Xiaomi”,
“34:80:B3”: “Xiaomi”, “38:A4:ED”: “Xiaomi”, “3C:BD:3E”: “Xiaomi”,
“40:31:3C”: “Xiaomi”, “4C:49:E3”: “Xiaomi”, “50:64:2B”: “Xiaomi”,
“58:44:98”: “Xiaomi”, “5C:E8:EB”: “Xiaomi”, “64:CC:2E”: “Xiaomi”,
“68:DF:DD”: “Xiaomi”, “74:23:44”: “Xiaomi”, “74:51:BA”: “Xiaomi”,
“78:02:F8”: “Xiaomi”, “7C:1D:D9”: “Xiaomi”, “8C:BE:BE”: “Xiaomi”,
“98:FA:E3”: “Xiaomi”, “9C:99:A0”: “Xiaomi”, “A0:86:C6”: “Xiaomi”,
“AC:37:43”: “Xiaomi”, “B0:E2:35”: “Xiaomi”, “C4:0B:CB”: “Xiaomi”,
“C8:14:79”: “Xiaomi”, “D4:97:0B”: “Xiaomi”, “D8:C8:E9”: “Xiaomi”,
“E0:76:D0”: “Xiaomi”, “F0:B4:29”: “Xiaomi”, “FC:64:BA”: “Xiaomi”,
# ASUS
“00:0C:6E”: “ASUS”, “00:1A:92”: “ASUS”, “00:1D:60”: “ASUS”,
“00:1E:8C”: “ASUS”, “00:1F:C6”: “ASUS”, “00:22:15”: “ASUS”,
“00:23:54”: “ASUS”, “00:24:8C”: “ASUS”, “00:26:18”: “ASUS”,
“00:27:19”: “ASUS”, “08:60:6E”: “ASUS”, “08:62:66”: “ASUS”,
“10:BF:48”: “ASUS”, “1C:87:2C”: “ASUS”, “20:CF:30”: “ASUS”,
“2C:56:DC”: “ASUS”, “2C:FD:A1”: “ASUS”, “30:5A:3A”: “ASUS”,
“38:2C:4A”: “ASUS”, “40:16:7E”: “ASUS”, “4C:ED:FB”: “ASUS”,
“50:46:5D”: “ASUS”, “54:04:A6”: “ASUS”, “5C:FF:35”: “ASUS”,
“60:A4:4C”: “ASUS”, “74:D0:2B”: “ASUS”, “78:24:AF”: “ASUS”,
“88:D7:F6”: “ASUS”, “9C:5C:8E”: “ASUS”, “AC:22:0B”: “ASUS”,
“AC:9E:17”: “ASUS”, “B0:6E:BF”: “ASUS”, “BC:AE:C5”: “ASUS”,
“D0:17:C2”: “ASUS”, “D8:50:E6”: “ASUS”, “DC:FE:18”: “ASUS”,
“F0:2F:74”: “ASUS”, “F4:6D:04”: “ASUS”, “FC:AA:14”: “ASUS”,
# TP-Link
“00:27:19”: “TP-Link”, “14:91:82”: “TP-Link”, “18:A6:F7”: “TP-Link”,
“1C:61:B4”: “TP-Link”, “20:F4:1B”: “TP-Link”, “28:6A:B8”: “TP-Link”,
“2C:F0:5D”: “TP-Link”, “30:DE:4B”: “TP-Link”, “34:96:72”: “TP-Link”,
“38:83:45”: “TP-Link”, “40:8D:5C”: “TP-Link”, “48:8D:36”: “TP-Link”,
“50:3E:AA”: “TP-Link”, “54:C4:15”: “TP-Link”, “5C:63:BF”: “TP-Link”,
“60:32:B1”: “TP-Link”, “64:09:80”: “TP-Link”, “64:70:02”: “TP-Link”,
“6C:5A:B0”: “TP-Link”, “74:EA:3A”: “TP-Link”, “78:A1:06”: “TP-Link”,
“7C:8B:CA”: “TP-Link”, “80:35:C1”: “TP-Link”, “84:16:F9”: “TP-Link”,
“88:DC:96”: “TP-Link”, “90:F6:52”: “TP-Link”, “94:D9:B3”: “TP-Link”,
“98:DA:C4”: “TP-Link”, “9C:A6:15”: “TP-Link”, “A0:F3:C1”: “TP-Link”,
“A4:2B:B0”: “TP-Link”, “AC:84:C6”: “TP-Link”, “B0:48:7A”: “TP-Link”,
“B0:BE:76”: “TP-Link”, “B4:B0:24”: “TP-Link”, “C0:25:E9”: “TP-Link”,
“C0:4A:00”: “TP-Link”, “C8:3A:35”: “TP-Link”, “D4:6E:0E”: “TP-Link”,
“D8:5D:4C”: “TP-Link”, “DC:09:4C”: “TP-Link”, “E4:6F:13”: “TP-Link”,
“E8:DE:27”: “TP-Link”, “EC:08:6B”: “TP-Link”, “F0:9F:C2”: “TP-Link”,
“F4:EC:38”: “TP-Link”, “F8:1A:67”: “TP-Link”, “FC:3F:DB”: “TP-Link”,
# Buffalo (バッファロー)
“00:0D:0B”: “Buffalo”, “00:16:01”: “Buffalo”, “00:1D:73”: “Buffalo”,
“00:24:A5”: “Buffalo”, “10:6F:3F”: “Buffalo”, “30:85:A9”: “Buffalo”,
“38:60:77”: “Buffalo”, “3C:97:0E”: “Buffalo”, “A0:D0:DC”: “Buffalo”,
“C8:7E:75”: “Buffalo”, “EC:6C:9F”: “Buffalo”,
# NEC
“00:0B:97”: “NEC”, “00:22:CF”: “NEC”, “08:00:69”: “NEC”,
# Intel (主にPCのWi-Fi)
“00:02:B3”: “Intel”, “00:03:47”: “Intel”, “00:04:23”: “Intel”,
“00:07:E9”: “Intel”, “00:0C:F1”: “Intel”, “00:0E:0C”: “Intel”,
“00:0E:35”: “Intel”, “00:11:11”: “Intel”, “00:12:F0”: “Intel”,
“00:13:02”: “Intel”, “00:13:20”: “Intel”, “00:13:CE”: “Intel”,
“00:13:E8”: “Intel”, “00:15:00”: “Intel”, “00:16:EA”: “Intel”,
“00:16:EB”: “Intel”, “00:18:DE”: “Intel”, “00:19:D1”: “Intel”,
“00:19:D2”: “Intel”, “00:1B:21”: “Intel”, “00:1B:77”: “Intel”,
“00:1C:BF”: “Intel”, “00:1D:E0”: “Intel”, “00:1D:E1”: “Intel”,
“00:1E:64”: “Intel”, “00:1E:65”: “Intel”, “00:1F:3B”: “Intel”,
“00:1F:3C”: “Intel”, “00:21:6A”: “Intel”, “00:21:6B”: “Intel”,
“00:23:14”: “Intel”, “00:23:15”: “Intel”, “00:24:D6”: “Intel”,
“00:24:D7”: “Intel”, “00:26:B9”: “Intel”, “00:26:C6”: “Intel”,
“00:26:C7”: “Intel”, “10:02:B5”: “Intel”, “14:85:7F”: “Intel”,
“18:3D:A2”: “Intel”, “18:66:DA”: “Intel”, “18:8B:9D”: “Intel”,
“1C:75:08”: “Intel”, “20:16:B9”: “Intel”, “24:0A:64”: “Intel”,
“24:77:03”: “Intel”, “28:D2:44”: “Intel”, “2C:44:FD”: “Intel”,
“30:0D:9E”: “Intel”, “34:02:86”: “Intel”, “34:13:E8”: “Intel”,
“38:59:F9”: “Intel”, “3C:A9:F4”: “Intel”, “40:25:C2”: “Intel”,
“44:1C:A8”: “Intel”, “44:85:00”: “Intel”, “48:0F:CF”: “Intel”,
“48:51:B7”: “Intel”, “50:7B:9D”: “Intel”, “54:13:79”: “Intel”,
“54:27:1E”: “Intel”, “58:A8:39”: “Intel”, “5C:F3:70”: “Intel”,
“60:67:20”: “Intel”, “60:D8:19”: “Intel”, “60:F6:77”: “Intel”,
“64:00:6A”: “Intel”, “68:17:29”: “Intel”, “68:5D:43”: “Intel”,
“68:A3:C4”: “Intel”, “6C:40:08”: “Intel”, “74:29:AF”: “Intel”,
“74:E5:0B”: “Intel”, “78:0C:B8”: “Intel”, “78:2B:CB”: “Intel”,
“78:92:9C”: “Intel”, “80:19:34”: “Intel”, “80:86:F2”: “Intel”,
“8C:8D:28”: “Intel”, “90:78:41”: “Intel”, “94:65:9C”: “Intel”,
“9C:4E:36”: “Intel”, “9C:B6:D0”: “Intel”, “A0:36:9F”: “Intel”,
“A0:88:B4”: “Intel”, “A4:02:B9”: “Intel”, “A4:34:D9”: “Intel”,
“A4:4E:31”: “Intel”, “A8:7E:EA”: “Intel”, “AC:7B:A1”: “Intel”,
“B4:96:91”: “Intel”, “B4:B6:76”: “Intel”, “BC:F6:85”: “Intel”,
“C4:8E:8F”: “Intel”, “C8:FF:28”: “Intel”, “CC:98:8B”: “Intel”,
“D0:7E:35”: “Intel”, “D4:3D:7E”: “Intel”, “D4:81:D7”: “Intel”,
“D4:BE:D9”: “Intel”, “D8:0B:CA”: “Intel”, “DC:53:60”: “Intel”,
“E0:06:E6”: “Intel”, “E0:4F:43”: “Intel”, “E0:94:67”: “Intel”,
“E4:54:E8”: “Intel”, “E8:2A:EA”: “Intel”, “EC:08:6B”: “Intel”,
“F0:4D:A2”: “Intel”, “F0:DE:F1”: “Intel”, “F4:8C:50”: “Intel”,
“F8:16:54”: “Intel”, “F8:28:19”: “Intel”,
# Broadcom (主にPCのWi-Fi)
“00:1A:73”: “Broadcom”, “14:48:C1”: “Broadcom”,
# Realtek
“00:01:6C”: “Realtek”, “00:26:2D”: “Realtek”, “00:90:4C”: “Realtek”,
“52:54:00”: “Realtek/QEMU”,
}

def get_local_ip():
“”“自分のIPアドレスを取得するやつ”””
try:
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect((“8.8.8.8”, 80))
ip = s.getsockname()[0]
s.close()
return ip
except:
return “127.0.0.1”

def get_hostname(ip):
“”“ホスト名を取得するやつ”””
try:
return socket.gethostbyaddr(ip)[0]
except:
return “”

def ping_host(ip):
“”“pingで生存確認するやつ”””
try:
result = subprocess.run(
[“ping”, “-c”, “1”, “-W”, “1”, str(ip)],
capture_output=True, timeout=2
)
return result.returncode == 0
except:
return False

def get_arp_table():
“”“ARPテーブルからMAC→IP対応表を取るやつ”””
mac_map = {}
try:
result = subprocess.run([“arp”, “-a”], capture_output=True, text=True, timeout=5)
lines = result.stdout.splitlines()
for line in lines:
# IPv4アドレスとMACアドレスを抽出
ip_match = re.search(r’((\d+.\d+.\d+.\d+))’, line)
mac_match = re.search(r’([0-9a-fA-F]{2}[:-][0-9a-fA-F]{2}[:-][0-9a-fA-F]{2}[:-][0-9a-fA-F]{2}[:-][0-9a-fA-F]{2}[:-][0-9a-fA-F]{2})’, line)
if ip_match and mac_match:
ip = ip_match.group(1)
mac = mac_match.group(1).upper().replace(”-”, “:”)
if mac != “FF:FF:FF:FF:FF:FF” and not mac.startswith(“01:”):
mac_map[ip] = mac
except:
pass
return mac_map

def lookup_vendor(mac):
“”“MACアドレスからベンダーを特定するやつ”””
if not mac:
return “不明”
mac_upper = mac.upper()
# 最初の3オクテット (OUI)
prefix = mac_upper[:8]
if prefix in MAC_VENDOR_MAP:
return MAC_VENDOR_MAP[prefix]
return “不明”

def guess_device_type(vendor, hostname, mac):
“”“ベンダーとホスト名からデバイスタイプを推測するやつ”””
hostname_lower = hostname.lower() if hostname else “”
vendor_lower = vendor.lower() if vendor else “”

```
# iPhoneの判定
if vendor == "Apple":
    if any(x in hostname_lower for x in ["iphone", "phone"]):
        return "iPhone", "📱"
    if any(x in hostname_lower for x in ["ipad"]):
        return "iPad", "📟"
    if any(x in hostname_lower for x in ["mac", "mbp", "macbook", "imac", "mini", "studio", "pro"]):
        return "Mac", "💻"
    if any(x in hostname_lower for x in ["appletv", "apple-tv"]):
        return "Apple TV", "📺"
    if any(x in hostname_lower for x in ["watch"]):
        return "Apple Watch", "⌚"
    if any(x in hostname_lower for x in ["airpods"]):
        return "AirPods", "🎧"
    # ホスト名で判断できない場合はApple端末として
    return "Apple Device", "🍎"

# Galaxyの判定
if vendor == "Samsung":
    if any(x in hostname_lower for x in ["galaxy", "sm-", "samsung", "android"]):
        return "Galaxy", "📱"
    if any(x in hostname_lower for x in ["tv", "tizen"]):
        return "Samsung TV", "📺"
    return "Samsung Device", "📱"

# Windowsの判定
if vendor in ["Intel", "Broadcom", "Realtek", "Realtek/QEMU"] or any(x in vendor_lower for x in ["microsoft"]):
    return "Windows PC", "🖥️"
if any(x in hostname_lower for x in ["desktop", "pc-", "-pc", "windows", "win-", "workstation"]):
    return "Windows PC", "🖥️"

# ルーター/AP
if vendor in ["TP-Link", "Buffalo", "ASUS", "NEC"] or any(x in hostname_lower for x in ["router", "gateway", "ap-", "-ap", "access"]):
    return "Router/AP", "📡"

# その他のメーカー
if vendor == "Google":
    if any(x in hostname_lower for x in ["pixel", "google"]):
        return "Google Pixel", "📱"
    if any(x in hostname_lower for x in ["chromecast", "chrome"]):
        return "Chromecast", "📺"
    if any(x in hostname_lower for x in ["nest"]):
        return "Google Nest", "🏠"
    return "Google Device", "📱"

if vendor == "Amazon":
    if any(x in hostname_lower for x in ["echo", "alexa"]):
        return "Amazon Echo", "🔊"
    if any(x in hostname_lower for x in ["fire", "kindle"]):
        return "Amazon Fire", "📱"
    return "Amazon Device", "📦"

if vendor == "Sony":
    if any(x in hostname_lower for x in ["ps4", "ps5", "playstation"]):
        return "PlayStation", "🎮"
    return "Sony Device", "📺"

if vendor == "Nintendo":
    return "Nintendo Switch", "🎮"

if vendor == "Raspberry Pi":
    return "Raspberry Pi", "🍓"

if vendor == "Huawei":
    return "Huawei Device", "📱"

if vendor == "Xiaomi":
    return "Xiaomi Device", "📱"

if vendor == "Microsoft":
    return "Windows/Xbox", "🖥️"

if vendor == "ASUS":
    if any(x in hostname_lower for x in ["router", "rt-", "rog"]):
        return "ASUS Router", "📡"
    return "ASUS PC", "🖥️"

# ホスト名ベースの推測
if any(x in hostname_lower for x in ["android", "phone", "mobile"]):
    return "Android Phone", "📱"
if any(x in hostname_lower for x in ["printer", "print"]):
    return "プリンタ", "🖨️"
if any(x in hostname_lower for x in ["nas", "storage", "diskstation", "readynas"]):
    return "NAS", "💾"
if any(x in hostname_lower for x in ["camera", "cam"]):
    return "カメラ", "📷"
if any(x in hostname_lower for x in ["tv", "bravia", "viera"]):
    return "TV", "📺"
if any(x in hostname_lower for x in ["linux", "ubuntu", "debian", "raspberr"]):
    return "Linux PC", "🐧"

return "不明端末", "❓"
```

def scan_network(base_ip, subnet_prefix):
“”“ネットワークをスキャンするメイン関数”””
devices = []

```
# まずpingで生存確認（高速化のため並列実行）
network = ipaddress.IPv4Network(f"{subnet_prefix}/24", strict=False)
hosts = list(network.hosts())

alive_ips = []

def check_host(ip):
    if ping_host(str(ip)):
        return str(ip)
    return None

print(f"[*] {subnet_prefix}/24 をスキャン中やで... (最大{len(hosts)}台)")

with ThreadPoolExecutor(max_workers=50) as executor:
    futures = {executor.submit(check_host, ip): ip for ip in hosts}
    for future in as_completed(futures):
        result = future.result()
        if result:
            alive_ips.append(result)
            print(f"  [+] 発見: {result}")

# ARPテーブルを取得
arp_table = get_arp_table()

# 自分自身のIPも追加
if base_ip not in alive_ips:
    alive_ips.append(base_ip)

# 各ホストの詳細情報を収集
for ip in sorted(alive_ips):
    mac = arp_table.get(ip, "")
    hostname = get_hostname(ip)
    vendor = lookup_vendor(mac) if mac else "不明"
    device_type, icon = guess_device_type(vendor, hostname, mac)
    is_self = (ip == base_ip)
    
    devices.append({
        "ip": ip,
        "mac": mac if mac else "取得不可",
        "hostname": hostname if hostname else ip,
        "vendor": vendor,
        "device_type": device_type,
        "icon": icon,
        "is_self": is_self,
        "is_gateway": ip == subnet_prefix.rsplit(".", 1)[0] + ".1"
    })

return devices
```

def generate_html(devices, base_ip, scan_time):
“”“スキャン結果からHTMLを生成するやつ”””
devices_json = json.dumps(devices, ensure_ascii=False)

```
html = f"""<!DOCTYPE html>
```

<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>LAN Network Map</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Zen+Kaku+Gothic+New:wght@400;700;900&display=swap');

:root {{
–bg: #0a0e1a;
–bg2: #0d1220;
–panel: #111827;
–accent: #00ff88;
–accent2: #00ccff;
–accent3: #ff6b35;
–text: #e2e8f0;
–muted: #64748b;
–grid: rgba(0,255,136,0.05);
–glow: 0 0 20px rgba(0,255,136,0.4);
–glow2: 0 0 20px rgba(0,204,255,0.4);
}}

- {{ margin: 0; padding: 0; box-sizing: border-box; }}

body {{
background: var(–bg);
color: var(–text);
font-family: ‘Zen Kaku Gothic New’, sans-serif;
min-height: 100vh;
overflow-x: hidden;
}}

/* グリッド背景 */
body::before {{
content: ‘’;
position: fixed;
inset: 0;
background-image:
linear-gradient(var(–grid) 1px, transparent 1px),
linear-gradient(90deg, var(–grid) 1px, transparent 1px);
background-size: 40px 40px;
pointer-events: none;
z-index: 0;
}}

.header {{
position: relative;
z-index: 10;
padding: 20px 30px;
border-bottom: 1px solid rgba(0,255,136,0.2);
display: flex;
align-items: center;
justify-content: space-between;
background: rgba(10,14,26,0.9);
backdrop-filter: blur(10px);
}}

.logo {{
font-family: ‘Share Tech Mono’, monospace;
font-size: 22px;
color: var(–accent);
text-shadow: var(–glow);
letter-spacing: 4px;
text-transform: uppercase;
}}

.logo span {{
color: var(–accent2);
text-shadow: var(–glow2);
}}

.stats-bar {{
display: flex;
gap: 30px;
font-family: ‘Share Tech Mono’, monospace;
font-size: 13px;
}}

.stat {{
text-align: center;
}}

.stat-num {{
font-size: 24px;
font-weight: 900;
color: var(–accent);
text-shadow: var(–glow);
display: block;
}}

.stat-label {{
color: var(–muted);
font-size: 10px;
letter-spacing: 2px;
text-transform: uppercase;
}}

.scan-info {{
font-family: ‘Share Tech Mono’, monospace;
font-size: 12px;
color: var(–muted);
text-align: right;
}}

.scan-info span {{
color: var(–accent);
}}

.main {{
position: relative;
z-index: 1;
display: flex;
gap: 0;
height: calc(100vh - 80px);
}}

/* ネットワークマップ */
.map-area {{
flex: 1;
position: relative;
overflow: hidden;
}}

#networkCanvas {{
width: 100%;
height: 100%;
}}

/* デバイス一覧 */
.device-list {{
width: 320px;
background: rgba(13,18,32,0.95);
border-left: 1px solid rgba(0,255,136,0.15);
overflow-y: auto;
padding: 16px;
}}

.device-list::-webkit-scrollbar {{
width: 4px;
}}

.device-list::-webkit-scrollbar-track {{
background: var(–bg);
}}

.device-list::-webkit-scrollbar-thumb {{
background: var(–accent);
border-radius: 2px;
}}

.list-header {{
font-family: ‘Share Tech Mono’, monospace;
font-size: 11px;
color: var(–accent);
letter-spacing: 3px;
text-transform: uppercase;
margin-bottom: 12px;
padding-bottom: 8px;
border-bottom: 1px solid rgba(0,255,136,0.2);
}}

.device-card {{
background: rgba(17,24,39,0.8);
border: 1px solid rgba(0,255,136,0.1);
border-radius: 8px;
padding: 12px;
margin-bottom: 8px;
cursor: pointer;
transition: all 0.2s;
position: relative;
overflow: hidden;
}}

.device-card::before {{
content: ‘’;
position: absolute;
top: 0; left: 0;
width: 3px; height: 100%;
background: var(–accent);
opacity: 0;
transition: opacity 0.2s;
}}

.device-card:hover, .device-card.active {{
border-color: rgba(0,255,136,0.4);
background: rgba(0,255,136,0.05);
transform: translateX(4px);
box-shadow: var(–glow);
}}

.device-card:hover::before, .device-card.active::before {{
opacity: 1;
}}

.device-card.is-self {{
border-color: rgba(0,204,255,0.4);
}}

.device-card.is-self::before {{
background: var(–accent2);
opacity: 1;
}}

.device-card.is-gateway {{
border-color: rgba(255,107,53,0.4);
}}

.device-card.is-gateway::before {{
background: var(–accent3);
opacity: 1;
}}

.card-top {{
display: flex;
align-items: center;
gap: 10px;
margin-bottom: 8px;
}}

.device-icon {{
font-size: 24px;
line-height: 1;
}}

.device-name {{
flex: 1;
min-width: 0;
}}

.device-type {{
font-weight: 700;
font-size: 14px;
color: var(–text);
white-space: nowrap;
overflow: hidden;
text-overflow: ellipsis;
}}

.device-vendor {{
font-size: 11px;
color: var(–muted);
font-family: ‘Share Tech Mono’, monospace;
}}

.badge {{
font-family: ‘Share Tech Mono’, monospace;
font-size: 9px;
padding: 2px 6px;
border-radius: 3px;
letter-spacing: 1px;
text-transform: uppercase;
}}

.badge-self {{
background: rgba(0,204,255,0.2);
color: var(–accent2);
border: 1px solid rgba(0,204,255,0.3);
}}

.badge-gw {{
background: rgba(255,107,53,0.2);
color: var(–accent3);
border: 1px solid rgba(255,107,53,0.3);
}}

.device-meta {{
display: grid;
grid-template-columns: 1fr 1fr;
gap: 4px;
}}

.meta-item {{
font-family: ‘Share Tech Mono’, monospace;
font-size: 10px;
color: var(–muted);
overflow: hidden;
text-overflow: ellipsis;
white-space: nowrap;
}}

.meta-item span {{
color: var(–accent);
}}

/* ツールチップ */
.tooltip {{
position: fixed;
background: rgba(10,14,26,0.95);
border: 1px solid var(–accent);
border-radius: 8px;
padding: 12px 16px;
font-family: ‘Share Tech Mono’, monospace;
font-size: 12px;
color: var(–text);
pointer-events: none;
z-index: 1000;
min-width: 220px;
box-shadow: var(–glow);
display: none;
}}

.tooltip-title {{
font-size: 16px;
margin-bottom: 8px;
color: var(–accent);
}}

.tooltip-row {{
display: flex;
justify-content: space-between;
gap: 12px;
margin-bottom: 4px;
color: var(–muted);
}}

.tooltip-row span:last-child {{
color: var(–text);
text-align: right;
}}

/* スキャンボタン */
.rescan-btn {{
position: fixed;
bottom: 24px;
right: 24px;
z-index: 100;
background: var(–accent);
color: var(–bg);
border: none;
padding: 12px 24px;
border-radius: 6px;
font-family: ‘Share Tech Mono’, monospace;
font-size: 13px;
font-weight: 700;
letter-spacing: 2px;
cursor: pointer;
text-transform: uppercase;
transition: all 0.2s;
box-shadow: var(–glow);
}}

.rescan-btn:hover {{
background: var(–accent2);
box-shadow: var(–glow2);
transform: translateY(-2px);
}}

.rescan-btn:active {{
transform: translateY(0);
}}

/* ローディング */
.loading-overlay {{
position: fixed;
inset: 0;
background: rgba(10,14,26,0.9);
z-index: 500;
display: flex;
flex-direction: column;
align-items: center;
justify-content: center;
font-family: ‘Share Tech Mono’, monospace;
}}

.loading-text {{
font-size: 20px;
color: var(–accent);
text-shadow: var(–glow);
letter-spacing: 4px;
margin-bottom: 20px;
animation: pulse 1s ease-in-out infinite;
}}

@keyframes pulse {{
0%, 100% {{ opacity: 1; }}
50% {{ opacity: 0.4; }}
}}

.loading-bar {{
width: 300px;
height: 4px;
background: rgba(0,255,136,0.2);
border-radius: 2px;
overflow: hidden;
}}

.loading-bar-inner {{
height: 100%;
background: var(–accent);
border-radius: 2px;
animation: loading 2s ease-in-out infinite;
box-shadow: var(–glow);
}}

@keyframes loading {{
0% {{ width: 0; }}
50% {{ width: 70%; }}
100% {{ width: 100%; }}
}}

.ping-dot {{
width: 8px;
height: 8px;
border-radius: 50%;
background: var(–accent);
display: inline-block;
margin-right: 6px;
animation: ping 1.5s ease-in-out infinite;
box-shadow: var(–glow);
}}

@keyframes ping {{
0%, 100% {{ transform: scale(1); opacity: 1; }}
50% {{ transform: scale(1.8); opacity: 0.5; }}
}}
</style>

</head>
<body>

<div class="header">
  <div class="logo">LAN<span>MAP</span> <span style="font-size:14px;opacity:0.6">SCANNER</span></div>
  <div class="stats-bar">
    <div class="stat">
      <span class="stat-num" id="totalCount">0</span>
      <span class="stat-label">Devices</span>
    </div>
    <div class="stat">
      <span class="stat-num" id="typeCount">0</span>
      <span class="stat-label">Types</span>
    </div>
  </div>
  <div class="scan-info">
    <div>HOST: <span>{base_ip}</span></div>
    <div>SCAN: <span>{scan_time}</span></div>
    <div>STATUS: <span style="color:var(--accent)">● ONLINE</span></div>
  </div>
</div>

<div class="main">
  <div class="map-area">
    <canvas id="networkCanvas"></canvas>
  </div>

  <div class="device-list">
    <div class="list-header"><span class="ping-dot"></span>ACTIVE DEVICES</div>
    <div id="deviceCards"></div>
  </div>
</div>

<div class="tooltip" id="tooltip"></div>

<button class="rescan-btn" onclick="window.location.reload()">⟳ RE-SCAN</button>

<script>
const DEVICES = {devices_json};
const BASE_IP = "{base_ip}";

// 統計更新
document.getElementById('totalCount').textContent = DEVICES.length;
const types = new Set(DEVICES.map(d => d.device_type));
document.getElementById('typeCount').textContent = types.size;

// デバイスカードを生成
const cardsEl = document.getElementById('deviceCards');
DEVICES.forEach((d, i) => {{
  const card = document.createElement('div');
  card.className = 'device-card' + (d.is_self ? ' is-self' : '') + (d.is_gateway ? ' is-gateway' : '');
  card.dataset.index = i;
  
  let badges = '';
  if (d.is_self) badges += '<span class="badge badge-self">YOU</span>';
  if (d.is_gateway) badges += '<span class="badge badge-gw">GW</span>';
  
  card.innerHTML = `
    <div class="card-top">
      <div class="device-icon">${{d.icon}}</div>
      <div class="device-name">
        <div class="device-type">${{d.device_type}}</div>
        <div class="device-vendor">${{d.vendor}}</div>
      </div>
      ${{badges}}
    </div>
    <div class="device-meta">
      <div class="meta-item">IP: <span>${{d.ip}}</span></div>
      <div class="meta-item">HOST: <span>${{d.hostname || '-'}}</span></div>
      <div class="meta-item" style="grid-column:1/-1">MAC: <span>${{d.mac}}</span></div>
    </div>
  `;
  
  card.addEventListener('click', () => {{
    document.querySelectorAll('.device-card').forEach(c => c.classList.remove('active'));
    card.classList.add('active');
    highlightNode(i);
  }});
  
  cardsEl.appendChild(card);
}});

// Canvas ネットワークマップ
const canvas = document.getElementById('networkCanvas');
const ctx = canvas.getContext('2d');
let nodes = [];
let highlighted = -1;

function resize() {{
  canvas.width = canvas.offsetWidth;
  canvas.height = canvas.offsetHeight;
  computeLayout();
  draw();
}}

function computeLayout() {{
  const cx = canvas.width / 2;
  const cy = canvas.height / 2;
  const count = DEVICES.length;
  
  nodes = DEVICES.map((d, i) => {{
    let x, y;
    
    if (d.is_self) {{
      x = cx;
      y = cy;
    }} else {{
      // 同心円配置: ゲートウェイは内側、他は外側
      const isInner = d.is_gateway;
      const innerR = Math.min(canvas.width, canvas.height) * 0.22;
      const outerR = Math.min(canvas.width, canvas.height) * 0.38;
      
      const otherDevices = DEVICES.filter(dd => !dd.is_self);
      const idx = otherDevices.indexOf(d);
      const total = otherDevices.length;
      
      const angle = (idx / total) * Math.PI * 2 - Math.PI / 2;
      const r = d.is_gateway ? innerR : outerR + (i % 3) * 20;
      
      x = cx + Math.cos(angle) * r;
      y = cy + Math.sin(angle) * r;
    }}
    
    return {{ ...d, x, y, vx: 0, vy: 0, radius: d.is_self ? 36 : (d.is_gateway ? 28 : 22) }};
  }});
}}

function drawLine(x1, y1, x2, y2, color, width, dash) {{
  ctx.beginPath();
  ctx.strokeStyle = color;
  ctx.lineWidth = width;
  if (dash) ctx.setLineDash(dash);
  else ctx.setLineDash([]);
  ctx.moveTo(x1, y1);
  ctx.lineTo(x2, y2);
  ctx.stroke();
  ctx.setLineDash([]);
}}

function drawNode(node, idx) {{
  const isHL = highlighted === idx;
  const r = node.radius;
  const pulseR = r + 8 + Math.sin(Date.now() / 600 + idx) * 4;
  
  // パルスリング（アニメーション）
  if (node.is_self || isHL) {{
    ctx.beginPath();
    ctx.arc(node.x, node.y, pulseR, 0, Math.PI * 2);
    ctx.strokeStyle = node.is_self ? 'rgba(0,204,255,0.3)' : 'rgba(0,255,136,0.3)';
    ctx.lineWidth = 2;
    ctx.stroke();
  }}
  
  // 外枠
  ctx.beginPath();
  ctx.arc(node.x, node.y, r + 3, 0, Math.PI * 2);
  let borderColor;
  if (node.is_self) borderColor = '#00ccff';
  else if (node.is_gateway) borderColor = '#ff6b35';
  else if (isHL) borderColor = '#00ff88';
  else borderColor = 'rgba(0,255,136,0.3)';
  ctx.strokeStyle = borderColor;
  ctx.lineWidth = isHL ? 2.5 : 1.5;
  ctx.stroke();
  
  // 背景
  const grad = ctx.createRadialGradient(node.x - r*0.3, node.y - r*0.3, 0, node.x, node.y, r);
  if (node.is_self) {{
    grad.addColorStop(0, 'rgba(0,150,255,0.6)');
    grad.addColorStop(1, 'rgba(0,60,120,0.9)');
  }} else if (node.is_gateway) {{
    grad.addColorStop(0, 'rgba(255,120,60,0.5)');
    grad.addColorStop(1, 'rgba(80,30,0,0.9)');
  }} else {{
    grad.addColorStop(0, 'rgba(0,80,50,0.6)');
    grad.addColorStop(1, 'rgba(10,20,30,0.9)');
  }}
  
  ctx.beginPath();
  ctx.arc(node.x, node.y, r, 0, Math.PI * 2);
  ctx.fillStyle = grad;
  ctx.fill();
  
  // アイコン
  ctx.font = `${{r * 0.8}}px serif`;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(node.icon, node.x, node.y - 2);
  
  // IPアドレス
  const label = node.ip;
  ctx.font = `bold 10px 'Share Tech Mono', monospace`;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'top';
  
  // ラベル背景
  const lw = ctx.measureText(label).width + 8;
  ctx.fillStyle = 'rgba(10,14,26,0.85)';
  ctx.fillRect(node.x - lw/2, node.y + r + 4, lw, 14);
  
  ctx.fillStyle = node.is_self ? '#00ccff' : (node.is_gateway ? '#ff6b35' : '#00ff88');
  ctx.fillText(label, node.x, node.y + r + 6);
  
  // デバイスタイプ
  const dlabel = node.device_type;
  ctx.font = `10px 'Zen Kaku Gothic New', sans-serif`;
  ctx.fillStyle = 'rgba(200,220,255,0.7)';
  ctx.fillText(dlabel, node.x, node.y + r + 22);
}}

function draw() {{
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  
  if (nodes.length === 0) return;
  
  const selfNode = nodes.find(n => n.is_self);
  const gwNode = nodes.find(n => n.is_gateway);
  
  // 接続線を描画
  nodes.forEach((node, i) => {{
    if (node.is_self) return;
    
    // 自分→全端末の接続線
    if (selfNode) {{
      const isHL = highlighted === i;
      const alpha = isHL ? 0.6 : 0.2;
      
      // アニメーション用オフセット
      const t = (Date.now() / 1500 + i * 0.2) % 1;
      const px = selfNode.x + (node.x - selfNode.x) * t;
      const py = selfNode.y + (node.y - selfNode.y) * t;
      
      drawLine(selfNode.x, selfNode.y, node.x, node.y,
        node.is_gateway ? `rgba(255,107,53,${{alpha}})` : `rgba(0,255,136,${{alpha}})`,
        isHL ? 2 : 1, null);
      
      // 流れるパケットアニメーション
      ctx.beginPath();
      ctx.arc(px, py, 3, 0, Math.PI * 2);
      ctx.fillStyle = node.is_gateway ? 'rgba(255,107,53,0.8)' : 'rgba(0,255,136,0.8)';
      ctx.fill();
    }}
  }});
  
  // ノードを描画（自分以外）
  nodes.forEach((node, i) => {{
    if (!node.is_self) drawNode(node, i);
  }});
  
  // 自分を最後（最前面）に描画
  if (selfNode) {{
    const selfIdx = nodes.indexOf(selfNode);
    drawNode(selfNode, selfIdx);
  }}
}}

function animate() {{
  draw();
  requestAnimationFrame(animate);
}}

// ツールチップ
const tooltip = document.getElementById('tooltip');
canvas.addEventListener('mousemove', (e) => {{
  const rect = canvas.getBoundingClientRect();
  const mx = e.clientX - rect.left;
  const my = e.clientY - rect.top;
  
  let found = false;
  nodes.forEach((node, i) => {{
    const dx = mx - node.x;
    const dy = my - node.y;
    if (Math.sqrt(dx*dx + dy*dy) < node.radius + 5) {{
      tooltip.style.display = 'block';
      tooltip.style.left = (e.clientX + 15) + 'px';
      tooltip.style.top = (e.clientY - 10) + 'px';
      tooltip.innerHTML = `
        <div class="tooltip-title">${{node.icon}} ${{node.device_type}}</div>
        <div class="tooltip-row"><span>IP</span><span>${{node.ip}}</span></div>
        <div class="tooltip-row"><span>MAC</span><span>${{node.mac}}</span></div>
        <div class="tooltip-row"><span>HOST</span><span>${{node.hostname || '不明'}}</span></div>
        <div class="tooltip-row"><span>VENDOR</span><span>${{node.vendor}}</span></div>
        ${{node.is_self ? '<div style="color:var(--accent2);margin-top:4px">◆ このデバイス</div>' : ''}}
        ${{node.is_gateway ? '<div style="color:var(--accent3);margin-top:4px">◆ ゲートウェイ</div>' : ''}}
      `;
      found = true;
    }}
  }});
  
  if (!found) tooltip.style.display = 'none';
}});

canvas.addEventListener('mouseleave', () => {{
  tooltip.style.display = 'none';
}});

canvas.addEventListener('click', (e) => {{
  const rect = canvas.getBoundingClientRect();
  const mx = e.clientX - rect.left;
  const my = e.clientY - rect.top;
  
  nodes.forEach((node, i) => {{
    const dx = mx - node.x;
    const dy = my - node.y;
    if (Math.sqrt(dx*dx + dy*dy) < node.radius + 5) {{
      highlighted = highlighted === i ? -1 : i;
      
      // 対応するカードをハイライト
      document.querySelectorAll('.device-card').forEach(c => c.classList.remove('active'));
      if (highlighted >= 0) {{
        const card = document.querySelector(`[data-index="${{i}}"]`);
        if (card) {{
          card.classList.add('active');
          card.scrollIntoView({{ behavior: 'smooth', block: 'nearest' }});
        }}
      }}
    }}
  }});
}});

function highlightNode(idx) {{
  highlighted = idx;
  // キャンバス上の該当ノードにスクロール（視覚的にフォーカス）
  draw();
}}

window.addEventListener('resize', resize);
resize();
animate();
</script>

</body>
</html>"""
    return html

class LANMapHandler(BaseHTTPRequestHandler):
“”“HTTPハンドラ”””
devices = []
base_ip = “”
scan_time = “”

```
def do_GET(self):
    if self.path == "/" or self.path == "/index.html":
        html = generate_html(self.devices, self.base_ip, self.scan_time)
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))
    elif self.path == "/api/devices":
        data = json.dumps(self.devices, ensure_ascii=False)
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(data.encode("utf-8"))
    else:
        self.send_response(404)
        self.end_headers()

def log_message(self, format, *args):
    pass  # ログを静かにするやつ
```

def main():
print(”=” * 50)
print(”  LAN NETWORK MAP SCANNER”)
print(”  なんJネットワーク探索ツール やで”)
print(”=” * 50)

```
base_ip = get_local_ip()
subnet_prefix = ".".join(base_ip.split(".")[:3]) + ".0"

print(f"\n[*] 自分のIP: {base_ip}")
print(f"[*] スキャン対象: {subnet_prefix}/24")
print(f"[*] スキャン開始するで、ちょっと待ってや...\n")

scan_start = time.time()
devices = scan_network(base_ip, subnet_prefix)
scan_elapsed = time.time() - scan_start
scan_time_str = time.strftime("%Y-%m-%d %H:%M:%S")

print(f"\n[+] スキャン完了！ {len(devices)}台の端末見つかったで ({scan_elapsed:.1f}秒)")
print(f"\n発見した端末一覧:")
for d in devices:
    badge = " [YOU]" if d["is_self"] else (" [GW]" if d["is_gateway"] else "")
    print(f"  {d['icon']} {d['ip']:15s} {d['device_type']:20s} {d['vendor']:15s} {d['mac']}{badge}")

# HTTPサーバーを起動
LANMapHandler.devices = devices
LANMapHandler.base_ip = base_ip
LANMapHandler.scan_time = scan_time_str

port = 8080
server = HTTPServer(("0.0.0.0", port), LANMapHandler)

print(f"\n[*] HTTPサーバー起動したで！")
print(f"[*] ブラウザで http://localhost:{port} を開いてや！")
print(f"[*] 終了するときは Ctrl+C やで\n")

try:
    server.serve_forever()
except KeyboardInterrupt:
    print("\n[*] 終了するで。おつかれさんやった！")
    server.shutdown()
```

if **name** == “**main**”:
main()
