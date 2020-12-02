#!/usr/bin/env python3
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import sys
import time
import datetime
import RPi.GPIO as GPIO
import threading
import config


class ServoService:
    SERVO_PIN = 26
    CENTER = 7.25

    def __init__(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.SERVO_PIN, GPIO.OUT)
        self.servo = GPIO.PWM(self.SERVO_PIN, 50)
        self.servo.start(0)
        self.servo.ChangeDutyCycle(self.CENTER)
        time.sleep(0.5)

    def start(self):
        a = 1.5
        s = 0.03
        diff = 5
        while True:
            # self.servo.ChangeDutyCycle(self.CENTER + a)
            # time.sleep(60*2/bpm - 0.1)
            # self.servo.ChangeDutyCycle(self.CENTER - a)
            # time.sleep(60*2/bpm - 0.1)
            for degree in range(-90, 91, diff):
                dc = 2.5 + (12.0 - 2.5) / 180 * (degree + 90)
                self.servo.ChangeDutyCycle(dc)
                time.sleep(s)
            for degree in range(91, -90, -diff):
                dc = 2.5 + (12.0 - 2.5) / 180 * (degree + 90)
                self.servo.ChangeDutyCycle(dc)
                time.sleep(s)


class MoterService:
    MOTORPIN1 = 27
    MOTORPIN2 = 22

    def __init__(self):
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.MOTORPIN1, GPIO.OUT)
        GPIO.setup(self.MOTORPIN2, GPIO.OUT)

        # PWM/100Hzに設定
        self.ML1 = GPIO.PWM(self.MOTORPIN1, 100)
        self.ML2 = GPIO.PWM(self.MOTORPIN2, 100)
        # 初期化
        self.ML1.start(0)
        self.ML2.start(0)

    def start(self):
        while True:
            self.ML1.ChangeDutyCycle(10)
            self.ML2.ChangeDutyCycle(0)
            time.sleep(3)

            self.ML1.ChangeDutyCycle(0)
            self.ML2.ChangeDutyCycle(0)
            time.sleep(3)


class LedService:
    # ポート番号の定義
    Full_red_pin = 11
    Full_blue_pin = 12
    Full_green_pin = 13

    red_pin = 17

    def __init__(self):
        # GPIOの設定
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.Full_red_pin, GPIO.OUT)
        GPIO.setup(self.Full_blue_pin, GPIO.OUT)
        GPIO.setup(self.Full_green_pin, GPIO.OUT)

        GPIO.setup(self.red_pin, GPIO.OUT)

        full_red_led = GPIO.PWM(self.Full_red_pin, 100)
        full_blue_led = GPIO.PWM(self.Full_blue_pin, 100)
        full_green_led = GPIO.PWM(self.Full_green_pin, 100)

        self.full_color_led = (full_red_led, full_blue_led, full_green_led)

        for led in self.full_color_led:
            led.start(0)

    def switch_red_led(self, is_turnon):
        if is_turnon:
            GPIO.output(self.red_pin, GPIO.HIGH)
        else:
            GPIO.output(self.red_pin, GPIO.LOW)

    def blinking_led(self):
        while True:
            self.switch_red_led(True)
            time.sleep(0.5)
            self.switch_red_led(False)
            time.sleep(0.5)

    def bpm_lighting(self):
        while True:
            if is_playing:
                self.switch_red_led(True)
                time.sleep(0.1)
                self.switch_red_led(False)
                time.sleep(60 / bpm - 0.1)
            else:
                self.switch_red_led(False)
                time.sleep(0.1)

    def rainbow(self):
        while True:
            for led in self.full_color_led:
                for dc in range(0, 100, 5):
                    led.ChangeDutyCycle(dc)
                    time.sleep(0.05)
            for led in self.full_color_led[::-1]:
                for dc in range(100, 0, -5):
                    led.ChangeDutyCycle(dc)
                    time.sleep(0.05)

    # 終了時にはこれを呼び出す
    def cleanup(self):
        GPIO.cleanup()


class Client:
    def __init__(self):
        self.song_name = "xxx"
        self.artist_name = "xxx"
        self.is_playing = False
        self.progress_ms = 0
        self.duration_ms = 0
        self.bpm = 120

        # set scope
        self.scope = "user-read-currently-playing"

        auth_manager = SpotifyOAuth(
            config.CLIENT_ID,
            config.CLIENT_SECRET,
            config.REDIRECT_URI,
            scope=self.scope,
            username=config.USERNAME,
        )
        self.sp = spotipy.Spotify(auth_manager=auth_manager)

    def get_currently_playing(self):
        return self.sp.currently_playing("JP")

    def fetch_worker(self):
        while True:
            result = self.sp.currently_playing("JP")
            if result == None:
                continue
            if (
                self.song_name != result["item"]["name"]
                or self.is_playing != result["is_playing"]
            ):
                features = self.get_audio_features(result["item"]["id"])
                self.bpm = features[0]["tempo"]
                self.is_playing = result["is_playing"]
                self.update()

            self.song_name = result["item"]["name"]
            self.artist_name = result["item"]["album"]["artists"][0]["name"]
            self.progress_ms = result["progress_ms"]
            self.duration_ms = result["item"]["duration_ms"]

            time.sleep(SLEEP_TIME)

    def update(self):
        global bpm
        global is_playing
        print("updated!")
        bpm = self.bpm
        is_playing = self.is_playing

    def get_audio_features(self, id):
        return self.sp.audio_features(id)

    def print_info(self):
        print(datetime.datetime.now())
        print(self.song_name, "by", self.artist_name)
        print("state: ", "playing" if self.is_playing else "paused")
        print(self.progress_ms, "/", self.duration_ms, "ms")
        print("tempo:", self.bpm)
        print()

    def print_worker(self):
        while True:
            self.print_info()
            time.sleep(SLEEP_TIME)


if __name__ == "__main__":
    SLEEP_TIME = 1

    is_playing = False
    bpm = 120

    client = Client()
    ledService = LedService()
    # moterService = MoterService()
    # servoService = ServoService()

    # データの取得とプリントはスレッドへ
    t1 = threading.Thread(target=client.fetch_worker)
    # t2 = threading.Thread(target=client.print_worker)
    t3 = threading.Thread(target=ledService.bpm_lighting)
    # t3 = threading.Thread(target=ledService.blinking_led)
    t4 = threading.Thread(target=ledService.rainbow)
    # t5 = threading.Thread(target=moterService.start)
    # t6 = threading.Thread(target=servoService.start)

    # デーモンにする
    # メインスレッドが終了したときに自動で止まってくれます

    threads = [t1, t3, t4]
    for thread in threads:
        thread.setDaemon(True)
        thread.start()

    try:
        while True:
            pass
    except KeyboardInterrupt:
        # ctrl+c でcleanupして終了
        ledService.cleanup()
        print("interrupted!")
        sys.exit()
