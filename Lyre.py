import asyncio
import ctypes
import os
import time
from math import trunc
from os import listdir
from typing import List

import mido
import pynput.keyboard

SONGS_PATH = os.path.dirname(os.path.abspath(__file__)) + "\\songs"

class Notes:
    KEYS = [
        (0, pynput.keyboard.KeyCode.from_vk(0x5A)),  # z
        (2, pynput.keyboard.KeyCode.from_vk(0x58)),  # x
        (4, pynput.keyboard.KeyCode.from_vk(0x43)),  # c
        (5, pynput.keyboard.KeyCode.from_vk(0x56)),  # v
        (7, pynput.keyboard.KeyCode.from_vk(0x42)),  # b
        (9, pynput.keyboard.KeyCode.from_vk(0x4E)),  # n
        (11, pynput.keyboard.KeyCode.from_vk(0x4D)),  # m
        (12, pynput.keyboard.KeyCode.from_vk(0x41)),  # a
        (14, pynput.keyboard.KeyCode.from_vk(0x53)),  # s
        (16, pynput.keyboard.KeyCode.from_vk(0x44)),  # d
        (17, pynput.keyboard.KeyCode.from_vk(0x46)),  # f
        (19, pynput.keyboard.KeyCode.from_vk(0x47)),  # g
        (21, pynput.keyboard.KeyCode.from_vk(0x48)),  # h
        (23, pynput.keyboard.KeyCode.from_vk(0x4A)),  # j
        (24, pynput.keyboard.KeyCode.from_vk(0x51)),  # q
        (26, pynput.keyboard.KeyCode.from_vk(0x57)),  # w
        (28, pynput.keyboard.KeyCode.from_vk(0x45)),  # e
        (29, pynput.keyboard.KeyCode.from_vk(0x52)),  # r
        (31, pynput.keyboard.KeyCode.from_vk(0x54)),  # t
        (33, pynput.keyboard.KeyCode.from_vk(0x59)),  # y
        (35, pynput.keyboard.KeyCode.from_vk(0x55)),  # u
    ]

    def __init__(self, note):
        self.map = {}
        for key in self.KEYS:
            self.map[note + key[0]] = key[1]

    def get_key(self, note):
        return self.map.get(note)


class Player:
    class Song:
        def __init__(self, file: str):
            self.file = file
            self.name = os.path.basename(file)[:-4]

    def __init__(self):
        pynput.keyboard.Listener(on_press=self.on_press).start()

        self.songs = list()
        self.current_range = 1
        self.load_songs()

        self.now_playing = None

        self.event_loop = asyncio.get_event_loop()
        self.event_loop.run_forever()

    def load_songs(self):
        self.songs = list()

        if not os.path.exists(SONGS_PATH):
            print(" ")
            print("Папка с музыкой не найдена.")
            print(f"Создайте папку \"songs\" рядом с программой ( она должна иметь путь {SONGS_PATH} )...")
            print(f"...и поместите внутрь midi файлы ( с расширение mid ), чтобы начать работу с программой.")
            print(" ")
            print("Вы можете загрузить музыку после создания папки, нажав русскую Ё.")
            print(" ")
            return

        print(" ")
        print("Формат списка: [Ряд-Номер] Название.")
        for file in listdir(SONGS_PATH):
            if not file.endswith(".mid"):
                continue

            self.songs.append(self.Song(SONGS_PATH + "\\" + file))

            r = trunc(len(self.songs) / 9)
            n = trunc(len(self.songs) % 9)
            print(f"[{r if n == 0 else r + 1}-{9 if n == 0 else n}] {self.songs[-1].name}")

        print(" ")
        print(f"Загружено {len(self.songs)} песен из папки.")
        print(" ")
        print("Чтобы запустить необходимую песню:")
        print("1. Переключитесь на необходимый ряд при помощи ← или →.")
        print("2. Нажмите кнопку, соответствующую номеру песни.")
        print(" ")
        print("Пробел - досрочная остановка песни.")
        print("Ё - перезагрузка музыки из папки.")
        print(" ")

    async def play(self, song: Song):
        keyboard = pynput.keyboard.Controller()

        if not os.path.isfile(song.file):
            print(" ")
            print(f"Файл \"{song.file}\" не найден.")
            print(" ")
            return

        print(" ")
        print(f"Подбираются ноты для лиры из файла {song.name}.")
        mid = mido.MidiFile(song.file)
        note_key_map = self.auto_root_key_map(mid, [], [], 48, 84, True)

        print(" ")
        print(f"Запускается проигрывание музыки {song.name}.")
        last_clock = time.time()
        for msg in mid:
            if self.now_playing is None:
                return

            elif msg.time > 0:
                await asyncio.sleep(msg.time - (time.time() - last_clock))
                last_clock += msg.time

            if msg.type == "note_on":
                if key := note_key_map.get_key(msg.note):
                    keyboard.press(key)
                    await asyncio.sleep(0.01)
                    keyboard.release(key)

        print(f"Завершено проигрывание {self.now_playing.name}.")
        print(" ")
        self.now_playing = None

    def on_press(self, key):
        if self.now_playing is not None:
            if key == pynput.keyboard.Key.space:
                print(f"Завершено проигрывание {self.now_playing.name}.")
                print(" ")
                self.now_playing = None
            return

        if str(key) == "'`'":
            self.load_songs()
            return

        if key == pynput.keyboard.Key.left:
            self.current_range = 1 if self.current_range == 1 else self.current_range - 1
            print(" ")
            print(f"Текущий ряд для воспроизведения: { self.current_range }.")
            print(" ")
            return

        if key == pynput.keyboard.Key.right:
            r = trunc(len(self.songs) / 9)
            n = trunc(len(self.songs) % 9)
            r = r if n == 0 else r + 1
            self.current_range = r if self.current_range + 1 > r else self.current_range + 1
            print(" ")
            print(f"Текущий ряд для воспроизведения: { self.current_range }.")
            print(" ")
            return

        if self.now_playing is None:
            if str(key).replace("'", "").isdigit():
                i = (9 * (0 if self.current_range == 1 else self.current_range - 1)) + int(str(key).replace("'", "")) - 1

                if i >= len(self.songs):
                    return

                self.now_playing = self.songs[i]
                self.event_loop.call_soon_threadsafe(
                    lambda: self.event_loop.create_task(
                        self.play(self.now_playing)
                    )
                )

    @staticmethod
    def auto_root_key_map(mid: mido.midifiles.midifiles.MidiFile, channels: List[int], tracks: List[int], lowest: int,
                          highest: int, use_count: bool):
        note_count = {}
        for i, track in enumerate(mid.tracks):
            if len(tracks) == 0 or i in tracks:
                for msg in track:
                    if msg.type == "note_on" and (len(channels) == 0 or msg.channel in channels):
                        if msg.note not in note_count:
                            note_count[msg.note] = 1
                        else:
                            note_count[msg.note] += 1

        if not note_count:
            print("Подходящих нот в файле не найдено.")
            return Notes(0)

        notes = sorted(note_count.keys())
        best_key_map = None
        best_hits = -1
        total = 0
        for cur_root in range(max(notes[0] - 24, 0), min(notes[-1] + 25, 128)):
            cur_key_map = Notes(cur_root)
            cur_note_hits = 0
            cur_total = 0
            for note, count in note_count.items():
                if lowest <= note < highest:
                    if cur_key_map.get_key(note):
                        cur_note_hits += count if use_count else 1
                    cur_total += count if use_count else 1

            if cur_note_hits > best_hits:
                best_hits = cur_note_hits
                total = cur_total
                best_key_map = cur_key_map

        print(f"Идеально подобраны {best_hits}/{total} нот ( {trunc(best_hits / total * 100)}% ).")
        return best_key_map

if __name__ == "__main__":
    print(" \n=====================================================\n" +
          " \n" +
          "             2Xr                     .rX2\n" +
          "             X999i.                 s993X\n" +
          "             593399s              s99999S \n" +
          "             ;9X99399r          r993933hr\n" +
          "              G,:&6S99393;    ;X9399S:,G.\n" +
          "              XS,,,i932S.    .S239i,,,iX\n" +
          "              ;G,.,...          .,.,,,hr\n" +
          "               99,                  ,3h\n" +
          "               2X                    X2\n" +
          "               :                      :\n" +
          "                 Проигрыватель \"Лира\"\n" +
          "                    Версия: 1.0.0\n" +
          " \n" +
          "                   by NyashMyash99\n" +
          "              https://vk.com/nyashmyash99\n" +
          " \n" +
          "=====================================================\n" +
          " ")

    try:
        if ctypes.windll.shell32.IsUserAnAdmin():
            Player()
        else:
            print(" ")
            print("Программа работает исключительно с правами Администратора.")
            print("К сожалению, без этого она не сможет нажимать кнопки клавиатуры :<")
            print("Перезапустите программу, но уже от имени Администратора.")
            print(" ")
    finally:
        input("Нажмите любую кнопку, чтобы выйти.")