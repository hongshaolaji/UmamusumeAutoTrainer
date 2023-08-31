import time

import cv2
import uiautomator2 as u2

import bot.conn.os as os
import bot.base.log as logger
import threading

from bot.base.common import ImageMatchMode
from bot.base.point import ClickPoint, ClickPointType
from bot.conn.ctrl import AndroidController
from bot.recog.image_matcher import template_match
from config import CONFIG

log = logger.get_logger(__name__)


class U2AndroidController(AndroidController):
    device_name = CONFIG.bot.auto.adb.device_name

    path = "deps\\adb\\"
    recent_point = None
    recent_operation_time = None
    same_point_operation_interval = 0.3
    u2client = None

    def __init__(self):
        pass

    # init_env 初始化环境
    def init_env(self) -> None:
        self.u2client = u2.connect(CONFIG.bot.auto.adb.device_name)

    # get_screen 获取图片
    def get_screen(self, to_gray=False):
        cur_screen = self.u2client.screenshot(format='opencv')
        if to_gray:
            return cv2.cvtColor(cur_screen, cv2.COLOR_BGR2GRAY)
        return cur_screen

    # ===== ctrl =====

    def click_by_point(self, point: ClickPoint):
        if self.recent_point is not None:
            if self.recent_point == point and time.time() - self.recent_operation_time < self.same_point_operation_interval:
                log.warning("request for a same point too frequently")
                return
        if point.target_type == ClickPointType.CLICK_POINT_TYPE_COORDINATE:
            self.click(point.coordinate.x, point.coordinate.y, name=point.desc)
        elif point.target_type == ClickPointType.CLICK_POINT_TYPE_TEMPLATE:
            cur_screen = self.get_screen(to_gray=True)
            if point.template.image_match_config.match_mode == ImageMatchMode.IMAGE_MATCH_MODE_TEMPLATE_MATCH:
                match_result = template_match(cur_screen, point.template.template_image)
                if match_result.find_match:
                    self.click(match_result.center_point[0], match_result.center_point[1])
        self.recent_point = point
        self.recent_operation_time = time.time()

    def click(self, x, y, name=""):
        if name != "":
            log.debug("click >> " + name)
        _ = self.execute_adb_shell("shell input tap " + str(x) + " " + str(y), True)
        time.sleep(CONFIG.bot.auto.adb.delay)

    def swipe(self, x1=1025, y1=550, x2=1025, y2=550, duration=0.2, name=""):
        if name != "":
            log.debug("swipe >> " + name)
        _ = self.execute_adb_shell("shell input swipe " + str(x1) + " " + str(y1) + " " + str(x2) + " " + str(y2) + " "
                                   + str(duration), True)
        time.sleep(CONFIG.bot.auto.adb.delay)

    # ===== common =====

    # execute_adb_shell 执行adb命令
    def execute_adb_shell(self, cmd, sync):
        cmd = os.run_cmd(self.path + "adb -s " + self.device_name + " " + cmd)
        if sync:
            cmd.communicate()
        else:
            threading.Thread(target=cmd.communicate, args=())
        return cmd

    def start_app(self, name):
        self.u2client.app_start(name)
        log.info("starting app <" + name + ">")

    # get_front_activity 获取前台正在运行的应用
    def get_front_activity(self):

        rsp = self.execute_adb_shell("shell \"dumpsys window windows | grep \"Current\"\"", True).communicate()
        log.debug(str(rsp))
        return str(rsp)

    # get_devices 获取adb连接设备状态
    def get_devices(self):
        p = os.run_cmd(self.path + "adb devices").communicate()
        devices = p[0].decode()
        log.debug(devices)
        return devices

    # connect_to_device 连接至设备
    def connect_to_device(self):
        p = os.run_cmd(self.path + "adb connect " + self.device_name).communicate()
        log.debug(p[0].decode())

    # kill_adb_server 停止adb-server
    def kill_adb_server(self):
        p = os.run_cmd(self.path + "adb kill-server").communicate()
        log.debug(p[0].decode())

    # check_file_exist 判断文件是否存在
    def check_file_exist(self, file_path, file_name):
        rsp = self.execute_adb_shell("shell ls " + file_path, True).communicate()
        file_list = rsp[0].decode()
        log.debug(str("ls file result:" + file_list))
        return file_name in file_list

    # push_file 推送文件
    def push_file(self, src, dst):
        self.execute_adb_shell("push " + src + " " + dst, True)

    # get_device_os_info 获取系统信息
    def get_device_os_info(self):
        rsp = self.execute_adb_shell("shell getprop ro.build.version.sdk", True).communicate()
        os_info = rsp[0].decode().replace('\r', '').replace('\n', '')
        log.debug("device os info: " + os_info)
        return os_info

    # get_device_cpu_info 获取cpu信息
    def get_device_cpu_info(self):
        rsp = self.execute_adb_shell("shell getprop ro.product.cpu.abi", True).communicate()
        cpu_info = rsp[0].decode().replace('\r', '').replace('\n', '')
        log.debug("device cpu info: " + cpu_info)
        return cpu_info

    # destroy 销毁
    def destroy(self):
        pass