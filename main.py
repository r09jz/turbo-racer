import array
import json
import math
import os
import random
import sys
import traceback
from collections import OrderedDict

import pygame

try:
    os.environ["SDL_VIDEO_CENTERED"] = "1"
    os.environ["SDL_ANDROID_SCREEN_ORIENTATION"] = "landscape"
except Exception:
    pass

FPS = 60
MAX_PIXELS = 800_000

MENU, GARAGE, SETTINGS, PLAYING, PAUSED, GAMEOVER = range(6)

C_GRASS       = (74, 138, 58)
C_GRASS_DARK  = (52, 104, 42)
C_ROAD        = (82, 82, 90)
C_ROAD_DARK   = (62, 62, 70)
C_ROAD_LINE   = (232, 226, 200)
C_EDGE        = (200, 195, 180)
C_STRIPE      = (245, 245, 230)
C_WHITE       = (255, 255, 255)
C_COIN        = (255, 215, 0)
C_COIN_DARK   = (180, 130, 20)
C_COIN_LIGHT  = (255, 245, 160)
C_SHIELD      = (80, 190, 255)
C_NITRO       = (255, 130, 45)
C_MAGNET      = (255, 80, 170)
C_HEART       = (220, 40, 60)
C_HEART_DARK  = (130, 15, 30)
C_HEART_LIGHT = (255, 130, 150)
C_UI_BG       = (24, 20, 32)
C_UI_BORDER   = (232, 220, 190)
C_UI_BORDER_D = (120, 100, 80)
C_UI_SHADOW   = (8, 6, 12)
C_UI_ACCENT   = (255, 200, 80)
C_TEXT        = (240, 235, 220)
C_TEXT_DIM    = (170, 165, 150)

TRAFFIC_COLORS = [
    (60, 120, 200), (230, 170, 50), (140, 60, 180),
    (60, 180, 140), (225, 225, 225), (220, 100, 60),
    (100, 100, 120),
]
SPECIAL_TRAFFIC = [(240, 240, 240), (90, 90, 110), (180, 70, 70)]

CARS = [
    {"id": "starter", "name": "STARTER", "color": (200, 50, 50),
     "accent": (255, 255, 255), "price": 0,
     "spd": 1.00, "acc": 1.00, "hnd": 1.00,
     "stripes": True, "spoiler": False},
    {"id": "bolt", "name": "BLUE BOLT", "color": (60, 130, 220),
     "accent": (255, 255, 255), "price": 500,
     "spd": 1.05, "acc": 1.08, "hnd": 1.02,
     "stripes": True, "spoiler": False},
    {"id": "viper", "name": "VIPER", "color": (60, 180, 90),
     "accent": (255, 220, 60), "price": 1200,
     "spd": 1.10, "acc": 1.10, "hnd": 1.05,
     "stripes": True, "spoiler": True},
    {"id": "phantom", "name": "PHANTOM", "color": (140, 60, 200),
     "accent": (240, 220, 255), "price": 2500,
     "spd": 1.15, "acc": 1.12, "hnd": 1.10,
     "stripes": False, "spoiler": True},
    {"id": "golden", "name": "GOLDEN", "color": (250, 190, 50),
     "accent": (120, 60, 20), "price": 5000,
     "spd": 1.20, "acc": 1.18, "hnd": 1.12,
     "stripes": True, "spoiler": True},
    {"id": "ice", "name": "ICE", "color": (90, 210, 235),
     "accent": (255, 255, 255), "price": 8000,
     "spd": 1.25, "acc": 1.22, "hnd": 1.18,
     "stripes": False, "spoiler": True},
    {"id": "shadow", "name": "SHADOW", "color": (50, 50, 65),
     "accent": (200, 40, 60), "price": 15000,
     "spd": 1.30, "acc": 1.28, "hnd": 1.25,
     "stripes": True, "spoiler": True},
]

CAR_BY_ID = {c["id"]: c for c in CARS}

UPGRADE_DEFS = {
    "engine": {"name": "ENGINE", "desc": "Top speed",
               "max": 5, "prices": [300, 800, 1800, 4000, 8000],
               "bonus_per_level": 0.04},
    "tires":  {"name": "TIRES",  "desc": "Handling",
               "max": 5, "prices": [200, 600, 1400, 3000, 6000],
               "bonus_per_level": 0.05},
    "nitro":  {"name": "NITRO",  "desc": "Boost duration",
               "max": 5, "prices": [400, 1000, 2200, 4800, 9000],
               "bonus_per_level": 0.15},
}


def _get_data_dir():
    try:
        from android.storage import app_storage_path
        return app_storage_path()
    except Exception:
        pass
    try:
        return os.path.dirname(os.path.abspath(__file__))
    except Exception:
        return "."


def _log_paths():
    base = _get_data_dir()
    paths = []
    try:
        paths.append(os.path.join(base, "racer_error.txt"))
    except Exception:
        pass
    try:
        paths.append(os.path.join("/sdcard/", "racer_error.txt"))
    except Exception:
        pass
    return paths


def log_exception(text):
    for p in _log_paths():
        try:
            with open(p, "w") as f:
                f.write(text)
            return
        except Exception:
            continue


def _save_paths():
    base = _get_data_dir()
    out = []
    try:
        out.append(os.path.join(base, "racer_save.json"))
    except Exception:
        pass
    try:
        out.append(os.path.join("/sdcard/", "racer_save.json"))
    except Exception:
        pass
    return out


DEFAULT_SAVE = {
    "hiscore": 0,
    "total_coins": 0,
    "total_distance": 0,
    "owned": ["starter"],
    "selected": "starter",
    "upgrades": {},
    "settings": {
        "sound_on": True,
        "music_on": True,
        "flip_controls": False,
        "high_quality": True,
    },
}


def load_save():
    for p in _save_paths():
        try:
            with open(p, "r") as f:
                data = json.load(f)
            result = dict(DEFAULT_SAVE)
            result.update(data)
            if not isinstance(result.get("owned"), list):
                result["owned"] = ["starter"]
            if result.get("selected") not in CAR_BY_ID:
                result["selected"] = "starter"
            if not isinstance(result.get("upgrades"), dict):
                result["upgrades"] = {}
            if not isinstance(result.get("settings"), dict):
                result["settings"] = dict(DEFAULT_SAVE["settings"])
            else:
                merged = dict(DEFAULT_SAVE["settings"])
                merged.update(result["settings"])
                result["settings"] = merged
            return result
        except Exception:
            continue
    return dict(DEFAULT_SAVE)


def save_save(data):
    for p in _save_paths():
        try:
            with open(p, "w") as f:
                json.dump(data, f)
            return
        except Exception:
            continue


def get_upgrade_level(save, car_id, kind):
    ups = save.get("upgrades", {}).get(car_id, {})
    return int(ups.get(kind, 0))


def get_effective_stats(save, car_id):
    car = CAR_BY_ID.get(car_id, CAR_BY_ID["starter"])
    spd = car["spd"]
    hnd = car["hnd"]
    acc = car["acc"]
    nitro_mult = 1.0
    spd += get_upgrade_level(save, car_id, "engine") * UPGRADE_DEFS["engine"]["bonus_per_level"]
    hnd += get_upgrade_level(save, car_id, "tires")  * UPGRADE_DEFS["tires"]["bonus_per_level"]
    nitro_mult += get_upgrade_level(save, car_id, "nitro") * UPGRADE_DEFS["nitro"]["bonus_per_level"]
    return spd, acc, hnd, nitro_mult


def clamp(v, lo, hi):
    return lo if v < lo else (hi if v > hi else v)


def lerp(a, b, t):
    return a + (b - a) * t


def lerp_color(c1, c2, t):
    t = clamp(t, 0.0, 1.0)
    return (int(lerp(c1[0], c2[0], t)),
            int(lerp(c1[1], c2[1], t)),
            int(lerp(c1[2], c2[2], t)))


def darken(c, amt=0.30):
    return (int(c[0] * (1 - amt)), int(c[1] * (1 - amt)), int(c[2] * (1 - amt)))


def lighten(c, amt=0.30):
    return (int(c[0] + (255 - c[0]) * amt),
            int(c[1] + (255 - c[1]) * amt),
            int(c[2] + (255 - c[2]) * amt))


def quant(c):
    return (c[0] & 0xF8, c[1] & 0xF8, c[2] & 0xF8)


def i4(t):
    return (int(t[0]), int(t[1]), int(t[2]), int(t[3]))


class Sfx:
    def __init__(self):
        self.ok = False
        self.sounds = {}
        self.enabled = True

    def init(self):
        try:
            if not hasattr(pygame, "mixer"):
                return
            info = pygame.mixer.get_init()
            if not info:
                return
            rate, fmt, channels = info
            if fmt != -16:
                return
            self.rate = int(rate)
            self.channels = int(clamp(channels, 1, 2))
            self.sounds["coin"]  = self._tone(940, 0.08, 0.22, "square", 1.6)
            self.sounds["power"] = self._tone(520, 0.24, 0.28, "square", 2.2)
            self.sounds["click"] = self._tone(700, 0.05, 0.15, "square", 1.0)
            self.sounds["crash"] = self._noise(0.45, 0.42)
            self.sounds["hit"]   = self._tone(180, 0.20, 0.30, "square", 0.7)
            self.sounds["buy"]   = self._tone(880, 0.30, 0.24, "square", 1.8)
            self.sounds["upgrade"] = self._tone(660, 0.15, 0.20, "square", 1.9)
            self.sounds["fail"]  = self._tone(220, 0.20, 0.20, "square", 0.6)
            self.ok = True
        except Exception:
            self.ok = False

    def _pack(self, mono):
        try:
            if self.channels == 1:
                return array.array("h", mono).tobytes()
            out = array.array("h", [0] * (2 * len(mono)))
            for i, v in enumerate(mono):
                out[i * 2] = v
                out[i * 2 + 1] = v
            return out.tobytes()
        except Exception:
            return array.array("h", mono).tobytes()

    def _tone(self, freq, dur, vol, shape="square", slide=1.0):
        n = max(1, int(self.rate * dur))
        mono = [0] * n
        phase = 0.0
        two_pi = 2.0 * math.pi
        for i in range(n):
            t = i / float(n)
            phase += two_pi * (freq * (slide ** t)) / self.rate
            s = (1.0 if math.sin(phase) >= 0 else -1.0) if shape == "square" else math.sin(phase)
            env = min(1.0, i / 32.0) * (1.0 - t) ** 1.6
            v = clamp(s * env * vol, -1.0, 1.0)
            mono[i] = int(v * 32767)
        return pygame.mixer.Sound(buffer=self._pack(mono))

    def _noise(self, dur, vol):
        n = max(1, int(self.rate * dur))
        mono = [0] * n
        rnd = random.Random(7)
        prev = 0.0
        for i in range(n):
            t = i / float(n)
            prev = prev * 0.55 + (rnd.random() * 2 - 1) * 0.45
            env = (1.0 - t) ** 2.0
            v = clamp(prev * env * vol, -1.0, 1.0)
            mono[i] = int(v * 32767)
        return pygame.mixer.Sound(buffer=self._pack(mono))

    def play(self, name):
        if not self.ok or not self.enabled:
            return
        snd = self.sounds.get(name)
        if snd is not None:
            try:
                snd.play()
            except Exception:
                pass


class Music:
    def __init__(self):
        self.ok = False
        self.tracks = {}
        self.current = None
        self.music_channel = None
        self.enabled = True
        self.volume = 0.5

    def init(self):
        try:
            info = pygame.mixer.get_init()
            if not info:
                return
            rate, fmt, channels = info
            if fmt != -16:
                return
            self.rate = int(rate)
            self.channels = int(clamp(channels, 1, 2))
            try:
                pygame.mixer.set_reserved(1)
                self.music_channel = pygame.mixer.Channel(0)
            except Exception:
                self.music_channel = None
            self.ok = True
        except Exception:
            self.ok = False

    def _pack(self, mono):
        if self.channels == 1:
            return array.array("h", mono).tobytes()
        out = array.array("h", [0] * (2 * len(mono)))
        for i, v in enumerate(mono):
            out[i * 2] = v
            out[i * 2 + 1] = v
        return out.tobytes()

    def _semitone_to_freq(self, semi):
        return 220.0 * (2.0 ** (semi / 12.0))

    def generate(self, name, melody, bass, bpm, wave="square"):
        if not self.ok:
            return
        try:
            beat_sec = 60.0 / max(1, bpm)
            melody_beats = sum(b for _, b in melody) if melody else 0
            bass_beats = sum(b for _, b in bass) if bass else 0
            total_beats = max(melody_beats, bass_beats, 1)
            n_samples = int(self.rate * beat_sec * total_beats)
            if n_samples <= 0:
                return
            max_samples = int(self.rate * 8)
            if n_samples > max_samples:
                n_samples = max_samples
            mono = [0] * n_samples

            def add_note(start_sample, dur_sec, semi, amp, wtype):
                if semi is None:
                    return
                freq = self._semitone_to_freq(semi)
                samples = int(self.rate * dur_sec)
                end = min(n_samples, start_sample + samples)
                if end <= start_sample:
                    return
                for i in range(start_sample, end):
                    t = (i - start_sample) / max(1, samples)
                    phase = (i - start_sample) * freq / self.rate
                    p = phase % 1.0
                    if wtype == "square":
                        s = 1.0 if p < 0.5 else -1.0
                    elif wtype == "triangle":
                        s = 4.0 * abs(p - 0.5) - 1.0
                    elif wtype == "saw":
                        s = 2.0 * p - 1.0
                    else:
                        s = math.sin(phase * 6.2831853)
                    attack = 0.02
                    release = 0.20
                    if t < attack:
                        env = t / attack
                    elif t > 1.0 - release:
                        env = (1.0 - t) / release
                    else:
                        env = 1.0
                    v = mono[i] + int(s * amp * env * 32767)
                    mono[i] = 32767 if v > 32767 else (-32767 if v < -32767 else v)

            pos = 0
            for semi, beats in (bass or []):
                dur = beats * beat_sec
                add_note(pos, dur, semi, 0.28, "triangle")
                pos += int(self.rate * dur)

            pos = 0
            for semi, beats in (melody or []):
                dur = beats * beat_sec
                add_note(pos, dur, semi, 0.42, wave)
                pos += int(self.rate * dur)

            snd = pygame.mixer.Sound(buffer=self._pack(mono))
            self.tracks[name] = snd
        except Exception:
            pass

    def play(self, name):
        if not self.ok or not self.enabled:
            return
        if self.current == name and self.music_channel and self.music_channel.get_busy():
            return
        snd = self.tracks.get(name)
        if snd is None:
            return
        self.current = name
        try:
            if self.music_channel:
                self.music_channel.stop()
                self.music_channel.set_volume(self.volume)
                self.music_channel.play(snd, loops=-1)
            else:
                snd.play(loops=-1)
        except Exception:
            pass

    def stop(self):
        try:
            if self.music_channel:
                self.music_channel.stop()
        except Exception:
            pass
        self.current = None

    def set_enabled(self, val):
        self.enabled = bool(val)
        if not self.enabled:
            self.stop()
        elif self.current:
            name = self.current
            self.current = None
            self.play(name)


class DigitCache:
    def __init__(self):
        self.cache = {}

    def get(self, size, color):
        key = (size, quant(color))
        d = self.cache.get(key)
        if d is None:
            f = pygame.font.Font(None, size)
            digits = []
            for i in range(10):
                img = f.render(str(i), False, color)
                sh = f.render(str(i), False, (0, 0, 0))
                surf = pygame.Surface(
                    (img.get_width() + 2, img.get_height() + 2),
                    pygame.SRCALPHA)
                surf.blit(sh, (1, 1))
                surf.blit(img, (0, 0))
                digits.append(surf)
            d = digits
            self.cache[key] = d
        return d

    def measure(self, text, size, color):
        digits = self.get(size, color)
        total = 0
        h = 0
        for c in text:
            if c.isdigit():
                im = digits[int(c)]
                total += im.get_width() - 2
                if im.get_height() > h:
                    h = im.get_height()
        return total + (2 if total else 0), h

    def draw(self, surf, text, size, color, pos, anchor="topleft"):
        digits = self.get(size, color)
        total_w, h = self.measure(text, size, color)
        x, y = int(pos[0]), int(pos[1])
        if anchor == "midtop":
            x -= total_w // 2
        elif anchor == "center":
            x -= total_w // 2
            y -= h // 2
        elif anchor == "midright":
            x -= total_w
        for c in text:
            if c.isdigit():
                im = digits[int(c)]
                surf.blit(im, (x, y))
                x += im.get_width() - 2
        return total_w


class FontCache:
    MAX_SIZE = 120
    def __init__(self, limit=300):
        self._fonts = {}
        self._cache = OrderedDict()
        self._limit = limit

    def font(self, size):
        size = int(clamp(size, 10, self.MAX_SIZE))
        f = self._fonts.get(size)
        if f is None:
            f = pygame.font.Font(None, size)
            self._fonts[size] = f
        return f

    def render(self, text, size, color, shadow=True, cache=True):
        size = int(clamp(size, 10, self.MAX_SIZE))
        key = (text, size, quant(color), shadow)
        if cache:
            surf = self._cache.get(key)
            if surf is not None:
                self._cache.move_to_end(key)
                return surf
        f = self.font(size)
        img = f.render(text, False, color)
        if shadow:
            try:
                sh = f.render(text, False, (0, 0, 0))
                combined = pygame.Surface(
                    (img.get_width() + 2, img.get_height() + 2),
                    pygame.SRCALPHA)
                combined.blit(sh, (1, 1))
                combined.blit(img, (0, 0))
                img = combined
            except Exception:
                pass
        if cache:
            self._cache[key] = img
            if len(self._cache) > self._limit:
                self._cache.popitem(last=False)
        return img

    def draw(self, surf, text, size, color, pos, anchor="topleft",
             shadow=True, cache=True):
        img = self.render(text, size, color, shadow, cache)
        rect = img.get_rect(**{anchor: (int(pos[0]), int(pos[1]))})
        surf.blit(img, rect)
        return rect


def render_car_sprite(w, h, body_color, accent_color,
                      has_stripes=False, has_spoiler=False):
    w, h = int(w), int(h)
    pad = 6
    surf = pygame.Surface((w + pad * 2, h + pad * 2), pygame.SRCALPHA)
    x, y = pad, pad

    dark      = darken(body_color, 0.40)
    very_dark = darken(body_color, 0.65)
    mid       = body_color
    light     = lighten(body_color, 0.30)
    outline   = (15, 15, 22)

    wheel_w = max(3, int(w * 0.15))
    wheel_h = max(5, int(h * 0.20))
    for wx in (x - 2, x + w - wheel_w + 2):
        for wy in (y + int(h * 0.12), y + int(h * 0.66)):
            pygame.draw.rect(surf, (10, 10, 15),
                             i4((wx - 1, wy - 1, wheel_w + 2, wheel_h + 2)))
            pygame.draw.rect(surf, (40, 40, 52), i4((wx, wy, wheel_w, wheel_h)))
            pygame.draw.rect(surf, (20, 20, 30), i4((wx, wy, wheel_w, 2)))
            pygame.draw.rect(surf, (20, 20, 30), i4((wx, wy + wheel_h - 2, wheel_w, 2)))
            hub_x = wx + wheel_w // 2 - 1
            hub_y = wy + wheel_h // 2 - 2
            pygame.draw.rect(surf, (110, 110, 125), i4((hub_x, hub_y, 2, 4)))

    pygame.draw.rect(surf, outline, i4((x - 1, y - 1, w + 2, h + 2)))
    pygame.draw.rect(surf, mid, i4((x, y, w, h)))

    side_band = max(2, int(w * 0.12))
    pygame.draw.rect(surf, dark, i4((x, y, side_band, h)))
    pygame.draw.rect(surf, dark, i4((x + w - side_band, y, side_band, h)))
    pygame.draw.rect(surf, very_dark, i4((x, y, 1, h)))
    pygame.draw.rect(surf, very_dark, i4((x + w - 1, y, 1, h)))
    pygame.draw.rect(surf, light, i4((x + 1, y + 1, w - 2, 1)))
    pygame.draw.rect(surf, very_dark, i4((x + 1, y + 1, w - 2, 2)))

    ws_y = y + int(h * 0.14)
    ws_h = max(4, int(h * 0.13))
    for i in range(ws_h):
        t = i / max(1, ws_h - 1)
        inset = int(w * (0.22 * (1 - t) + 0.12 * t))
        pygame.draw.rect(surf, (25, 35, 55),
                         i4((x + inset, ws_y + i, w - inset * 2, 1)))
        if i < ws_h // 3:
            pygame.draw.rect(surf, (80, 120, 170),
                             i4((x + inset + 1, ws_y + i,
                                 max(2, (w - inset * 2) // 3), 1)))
    pygame.draw.rect(surf, outline, i4((x + int(w * 0.20), ws_y - 1, w - int(w * 0.40), 1)))
    pygame.draw.rect(surf, outline, i4((x + int(w * 0.11), ws_y + ws_h, w - int(w * 0.22), 1)))

    roof_y = ws_y + ws_h + 1
    roof_h = max(3, int(h * 0.22))
    pygame.draw.rect(surf, dark, i4((x + int(w * 0.10), roof_y,
                                     w - int(w * 0.20), roof_h)))
    pygame.draw.rect(surf, mid, i4((x + int(w * 0.13), roof_y + 1,
                                    w - int(w * 0.26), roof_h - 2)))

    rw_y = roof_y + roof_h + 1
    rw_h = max(2, int(h * 0.09))
    rw_inset = int(w * 0.18)
    pygame.draw.rect(surf, (25, 35, 55),
                     i4((x + rw_inset, rw_y, w - rw_inset * 2, rw_h)))
    pygame.draw.rect(surf, (50, 70, 100),
                     i4((x + rw_inset + 1, rw_y, w - rw_inset * 2 - 2, 1)))

    trunk_y = rw_y + rw_h + 1
    trunk_h = max(2, h - (trunk_y - y) - 3)
    if trunk_h > 0:
        pygame.draw.rect(surf, mid, i4((x + 2, trunk_y, w - 4, trunk_h)))
        pygame.draw.rect(surf, dark, i4((x + 2, trunk_y + trunk_h - 1, w - 4, 1)))

    if has_stripes:
        stripe_w = max(2, int(w * 0.09))
        cx = x + w // 2
        gap = max(1, int(w * 0.03))
        pygame.draw.rect(surf, accent_color,
                         i4((cx - gap - stripe_w, y + 3, stripe_w, h - 6)))
        pygame.draw.rect(surf, accent_color,
                         i4((cx + gap, y + 3, stripe_w, h - 6)))

    hl_w = max(3, int(w * 0.22))
    hl_h = max(2, int(h * 0.035))
    hl_y = y + 2
    pygame.draw.rect(surf, (255, 245, 200), i4((x + 3, hl_y, hl_w, hl_h)))
    pygame.draw.rect(surf, (255, 255, 255), i4((x + 4, hl_y + 1, hl_w - 2, 1)))
    pygame.draw.rect(surf, (255, 245, 200), i4((x + w - hl_w - 3, hl_y, hl_w, hl_h)))
    pygame.draw.rect(surf, (255, 255, 255), i4((x + w - hl_w - 2, hl_y + 1, hl_w - 2, 1)))

    tl_w = max(3, int(w * 0.22))
    tl_h = max(2, int(h * 0.03))
    tl_y = y + h - tl_h - 2
    pygame.draw.rect(surf, (200, 40, 40), i4((x + 3, tl_y, tl_w, tl_h)))
    pygame.draw.rect(surf, (255, 90, 90), i4((x + 4, tl_y, tl_w - 2, 1)))
    pygame.draw.rect(surf, (200, 40, 40), i4((x + w - tl_w - 3, tl_y, tl_w, tl_h)))
    pygame.draw.rect(surf, (255, 90, 90), i4((x + w - tl_w - 2, tl_y, tl_w - 2, 1)))

    mirror_y = ws_y + 1
    pygame.draw.rect(surf, outline, i4((x - 2, mirror_y, 3, 3)))
    pygame.draw.rect(surf, mid,     i4((x - 1, mirror_y + 1, 1, 1)))
    pygame.draw.rect(surf, outline, i4((x + w - 1, mirror_y, 3, 3)))
    pygame.draw.rect(surf, mid,     i4((x + w, mirror_y + 1, 1, 1)))

    if has_spoiler:
        sp_y = y + h - 1
        sp_w = w + 8
        sp_h = 4
        sp_x = x - 4
        pygame.draw.rect(surf, outline, i4((sp_x - 1, sp_y - 1, sp_w + 2, sp_h + 2)))
        pygame.draw.rect(surf, dark,    i4((sp_x, sp_y, sp_w, sp_h)))
        pygame.draw.rect(surf, light,   i4((sp_x, sp_y, sp_w, 1)))
        pygame.draw.rect(surf, outline, i4((x + 3, sp_y - 2, 2, 2)))
        pygame.draw.rect(surf, outline, i4((x + w - 5, sp_y - 2, 2, 2)))

    return surf, pad


def render_heart(size, filled=True):
    size = max(8, int(size))
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    base = C_HEART if filled else C_HEART_DARK
    light = C_HEART_LIGHT if filled else darken(C_HEART_DARK, 0.4)
    scale = max(1, size // 7)
    ox = (size - 7 * scale) // 2
    oy = (size - 6 * scale) // 2

    def px(xx, yy, c):
        pygame.draw.rect(s, c, i4((ox + xx * scale, oy + yy * scale, scale, scale)))

    for yy in range(6):
        for xx in range(7):
            inside = False
            if yy == 0 and xx in (1, 2, 4, 5): inside = True
            elif yy == 1 and xx in (0, 1, 2, 3, 4, 5, 6): inside = True
            elif yy == 2 and xx in (0, 1, 2, 3, 4, 5, 6): inside = True
            elif yy == 3 and xx in (1, 2, 3, 4, 5): inside = True
            elif yy == 4 and xx in (2, 3, 4): inside = True
            elif yy == 5 and xx == 3: inside = True
            if inside:
                px(xx, yy, base)
    px(1, 1, light)
    px(2, 1, light)
    pygame.draw.rect(s, (30, 10, 15), i4((0, 0, size, size)), 1)
    return s


def render_powerup_icon(kind, size):
    size = max(10, int(size))
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    col = {"shield": C_SHIELD, "nitro": C_NITRO, "magnet": C_MAGNET}.get(kind, C_WHITE)
    dark = darken(col, 0.35)
    light = lighten(col, 0.35)
    pygame.draw.rect(s, dark, i4((0, 0, size, size)))
    pygame.draw.rect(s, col, i4((1, 1, size - 2, size - 2)))
    pygame.draw.rect(s, (20, 15, 25), i4((0, 0, size, size)), 2)
    cx, cy = size // 2, size // 2
    u = max(2, size // 8)
    if kind == "shield":
        pts = [(cx, cy - 3*u), (cx + 3*u, cy - 2*u), (cx + 3*u, cy + u),
               (cx, cy + 3*u), (cx - 3*u, cy + u), (cx - 3*u, cy - 2*u)]
        pygame.draw.polygon(s, C_WHITE, pts)
        pygame.draw.polygon(s, light, pts, 2)
    elif kind == "nitro":
        pts = [(cx - u, cy - 3*u), (cx + 2*u, cy - 3*u), (cx, cy - u),
               (cx + 2*u, cy - u), (cx - u, cy + 3*u), (cx, cy),
               (cx - 2*u, cy)]
        pygame.draw.polygon(s, C_WHITE, pts)
    elif kind == "magnet":
        pygame.draw.rect(s, C_WHITE, i4((cx - 3*u, cy - 3*u, 6*u, 2*u)))
        pygame.draw.rect(s, C_WHITE, i4((cx - 3*u, cy - 3*u, 2*u, 5*u)))
        pygame.draw.rect(s, C_WHITE, i4((cx + 1*u, cy - 3*u, 2*u, 5*u)))
        pygame.draw.rect(s, (220, 60, 60), i4((cx - 3*u, cy + 2*u, 2*u, 2*u)))
        pygame.draw.rect(s, (60, 60, 220), i4((cx + 1*u, cy + 2*u, 2*u, 2*u)))
    return s


def render_coin_frames(size):
    r = max(6, int(size))
    frames = []
    for i in range(12):
        t = i / 12.0
        w = max(4, int(abs(math.cos(t * math.tau)) * r))
        pad = 2
        fr = pygame.Surface((r * 2 + pad * 2, r * 2 + pad * 2), pygame.SRCALPHA)
        pygame.draw.rect(fr, (90, 60, 10),
                         i4((pad + (r - w // 2) - 1, pad - 1, w + 2, r * 2 + 2)))
        pygame.draw.rect(fr, C_COIN_DARK, i4((pad + (r - w // 2), pad, w, r * 2)))
        if w > 4:
            pygame.draw.rect(fr, C_COIN, i4((pad + (r - w // 2) + 1, pad + 1, w - 2, r * 2 - 2)))
            pygame.draw.rect(fr, C_COIN_LIGHT,
                             i4((pad + (r - w // 2) + 1, pad + 2, max(1, w // 3), r * 2 - 4)))
        frames.append((fr, pad))
    return frames


def render_prop_sprite(kind, size, tint):
    size = int(size)
    W, H = int(size * 2 + 4), int(size * 3 + 4)
    surf = pygame.Surface((W, H), pygame.SRCALPHA)
    x = int(W * 0.5)
    y = int(size * 2.4)
    s = size
    if kind == "tree":
        pygame.draw.rect(surf, (60, 40, 25), i4((x - s*0.14, y - s*0.10, s*0.28, s*1.10)))
        pygame.draw.rect(surf, (95, 65, 40), i4((x - s*0.10, y - s*0.05, s*0.14, s*1.00)))
        pygame.draw.rect(surf, darken(tint, 0.30), i4((x - s*0.85, y - s*1.10, s*1.70, s*1.05)))
        pygame.draw.rect(surf, tint, i4((x - s*0.70, y - s*1.25, s*1.40, s*0.95)))
        pygame.draw.rect(surf, lighten(tint, 0.25), i4((x - s*0.45, y - s*1.45, s*0.90, s*0.45)))
    elif kind == "bush":
        pygame.draw.rect(surf, darken(tint, 0.20), i4((x - s, y - s*0.65, s*2.0, s*1.20)))
        pygame.draw.rect(surf, tint, i4((x - s*0.85, y - s*0.75, s*1.70, s*1.05)))
        pygame.draw.rect(surf, lighten(tint, 0.20), i4((x - s*0.55, y - s*0.85, s*0.60, s*0.35)))
    elif kind == "rock":
        pygame.draw.rect(surf, (75, 78, 85), i4((x - s, y - s*0.65, s*2.0, s*1.30)))
        pygame.draw.rect(surf, (110, 115, 125), i4((x - s*0.75, y - s*0.70, s*1.50, s*0.90)))
        pygame.draw.rect(surf, (150, 155, 165), i4((x - s*0.50, y - s*0.80, s*0.80, s*0.35)))
    else:
        pygame.draw.rect(surf, (55, 55, 65), i4((x - s*0.06, y - s*2.0, s*0.12, s*2.0)))
        pygame.draw.rect(surf, (255, 230, 130), i4((x - s*0.28, y - s*2.30, s*0.56, s*0.45)))
        pygame.draw.rect(surf, (255, 255, 200), i4((x - s*0.16, y - s*2.22, s*0.32, s*0.30)))
    return surf, 2


class Layout:
    def __init__(self, sw, sh):
        self.sw, self.sh = int(sw), int(sh)
        if self.sw * self.sh <= MAX_PIXELS:
            self.vw, self.vh = self.sw, self.sh
        else:
            f = math.sqrt(MAX_PIXELS / float(self.sw * self.sh))
            self.vw = max(320, int(self.sw * f))
            self.vh = max(480, int(self.sh * f))
        self.scale = min(self.sw / float(self.vw), self.sh / float(self.vh))
        self.dw = int(round(self.vw * self.scale))
        self.dh = int(round(self.vh * self.scale))
        self.ox = (self.sw - self.dw) // 2
        self.oy = (self.sh - self.dh) // 2
        self.direct = (self.ox == 0 and self.oy == 0
                       and self.dw == self.sw and self.dh == self.sh)
        U = float(min(self.vw, self.vh))
        self.unit = U
        self.ks = self.vh / 480.0
        self.lanes = 4
        self.road_w = min(self.vw * 0.62, U * 0.95)
        self.road_left = (self.vw - self.road_w) * 0.5
        self.road_right = self.road_left + self.road_w
        self.lane_w = self.road_w / self.lanes
        self.lane_centers = [self.road_left + self.lane_w * (i + 0.5) for i in range(self.lanes)]
        self.car_w = self.lane_w * 0.56
        self.car_h = self.car_w * 1.85
        self.truck_w = self.lane_w * 0.72
        self.truck_h = self.truck_w * 1.95
        self.player_y = self.vh * 0.62
        m = self.vw * 0.028
        bw = min(self.vw * 0.20, U * 0.24)
        by = self.vh - bw - m * 1.9
        self.btn = {
            "LEFT":  pygame.Rect(int(m), int(by), int(bw), int(bw)),
            "RIGHT": pygame.Rect(int(m * 1.45 + bw), int(by), int(bw), int(bw)),
            "BRAKE": pygame.Rect(int(self.vw - m * 1.45 - bw * 2), int(by), int(bw), int(bw)),
            "GAS":   pygame.Rect(int(self.vw - m - bw), int(by), int(bw), int(bw)),
        }
        pb = U * 0.11
        self.pause_btn = pygame.Rect(int(self.vw - pb - m * 0.8), int(m * 0.9), int(pb), int(pb))
        mw, mh = U * 0.55, U * 0.15
        cx = self.vw * 0.5
        self.menu_btns = {
            "RESUME":  pygame.Rect(int(cx - mw / 2), int(self.vh * 0.52), int(mw), int(mh)),
            "RESTART": pygame.Rect(int(cx - mw / 2), int(self.vh * 0.52 + mh * 1.5), int(mw), int(mh)),
        }
        bw2, bh2 = int(U * 0.55), int(U * 0.115)
        bx2 = int((self.vw - bw2) / 2)
        by2 = int(self.vh * 0.58)
        self.main_btns = {
            "PLAY":    pygame.Rect(bx2, by2, bw2, bh2),
            "GARAGE":  pygame.Rect(bx2, by2 + int(bh2 * 1.30), bw2, bh2),
            "SETTINGS":pygame.Rect(bx2, by2 + int(bh2 * 2.60), bw2, bh2),
            "EXIT":    pygame.Rect(bx2, by2 + int(bh2 * 3.90), bw2, bh2),
        }
        self.garage_back = pygame.Rect(int(U*0.03), int(U*0.03), int(U*0.15), int(U*0.10))
        fs = U / 480.0
        self.fsize = {
            "tiny":  max(12, int(round(18 * fs))),
            "small": max(16, int(round(24 * fs))),
            "med":   max(22, int(round(34 * fs))),
            "big":   max(40, int(round(60 * fs))),
            "huge":  max(56, int(round(84 * fs))),
        }
        self._make_panels()

    def _make_panels(self):
        U = self.unit
        pw, ph = int(U * 0.42), int(U * 0.155)
        self.panel_score = self._make_rpg_panel(pw, ph)
        sw_, sh_ = int(U * 0.44), int(U * 0.050)
        self.panel_speed = self._make_rpg_panel(sw_, sh_)
        lw, lh = int(U * 0.28), int(U * 0.055)
        self.panel_lives = self._make_rpg_panel(lw, lh)
        bw = int(U * 0.28)
        bh = max(8, int(U * 0.018))
        self.pu_bar_w = bw
        self.pu_bar_h = bh
        self.pu_bar_bg = self._make_rpg_panel(bw, bh)
        def full_fill(color):
            s = pygame.Surface((bw - 4, bh - 4))
            s.fill(color)
            return s
        self.pu_fill_shield = full_fill(C_SHIELD)
        self.pu_fill_nitro  = full_fill(C_NITRO)
        self.pu_fill_magnet = full_fill(C_MAGNET)

    def _make_rpg_panel(self, w, h):
        w, h = int(w), int(h)
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(s, C_UI_SHADOW, i4((0, 0, w, h)))
        pygame.draw.rect(s, C_UI_BG, i4((2, 2, w - 4, h - 4)))
        pygame.draw.line(s, (70, 60, 80), (2, 2), (w - 3, 2))
        pygame.draw.line(s, (70, 60, 80), (2, 2), (2, h - 3))
        pygame.draw.rect(s, C_UI_BORDER, i4((1, 1, w - 2, h - 2)), 1)
        pygame.draw.rect(s, C_UI_BORDER_D, i4((3, 3, w - 6, h - 6)), 1)
        return s


def render_wood_button(w, h, text, font, enabled=True, highlighted=False):
    w, h = int(w), int(h)
    surf = pygame.Surface((w + 6, h + 6), pygame.SRCALPHA)
    bx, by = 3, 3
    pygame.draw.rect(surf, (0, 0, 0, 110), i4((bx + 2, by + 3, w, h)))
    if not enabled:
        top_col = (120, 110, 100)
        bot_col = (70, 60, 55)
        border_col = (50, 42, 38)
        edge_col = (90, 82, 75)
        text_col = (150, 145, 140)
        text_shadow = (40, 35, 30)
    elif highlighted:
        top_col = (255, 220, 130)
        bot_col = (220, 160, 60)
        border_col = (100, 60, 20)
        edge_col = (255, 240, 180)
        text_col = (90, 40, 10)
        text_shadow = (255, 245, 200)
    else:
        top_col = (220, 180, 130)
        bot_col = (170, 120, 70)
        border_col = (80, 45, 20)
        edge_col = (255, 230, 190)
        text_col = (70, 35, 10)
        text_shadow = (255, 235, 200)
    pygame.draw.rect(surf, border_col, i4((bx, by, w, h)))
    for yy in range(h - 6):
        t = yy / max(1, h - 7)
        c = lerp_color(top_col, bot_col, t)
        pygame.draw.line(surf, c, (bx + 3, by + 3 + yy), (bx + w - 4, by + 3 + yy))
    corner = max(2, min(6, h // 6))
    for yy in range(corner):
        for xx in range(corner):
            if xx + yy < corner:
                surf.set_at((bx + xx, by + yy), (0, 0, 0, 0))
                surf.set_at((bx + w - 1 - xx, by + yy), (0, 0, 0, 0))
                surf.set_at((bx + xx, by + h - 1 - yy), (0, 0, 0, 0))
                surf.set_at((bx + w - 1 - xx, by + h - 1 - yy), (0, 0, 0, 0))
    pygame.draw.line(surf, edge_col, (bx + 4, by + 3), (bx + w - 5, by + 3))
    pygame.draw.line(surf, darken(bot_col, 0.35), (bx + 4, by + h - 4), (bx + w - 5, by + h - 4))
    pygame.draw.rect(surf, darken(border_col, 0.1), i4((bx + 2, by + 2, w - 4, h - 4)), 1)
    txt_shadow = font.render(text, False, text_shadow)
    txt = font.render(text, False, text_col)
    rect = txt.get_rect(center=(bx + w // 2, by + h // 2))
    surf.blit(txt_shadow, (rect.x + 1, rect.y + 1))
    surf.blit(txt, (rect.x, rect.y))
    if enabled:
        txt_hi = font.render(text, False, (255, 240, 200))
        surf.blit(txt_hi, (rect.x, rect.y - 1))
    return surf


class Sprites:
    def __init__(self, L):
        self.L = L
        self.vehicles = {}
        self.player_rotations = {}
        self.car_sprites = {}
        colors = set(TRAFFIC_COLORS) | set(SPECIAL_TRAFFIC)
        for color in colors:
            self.vehicles[(color, "car")] = render_car_sprite(
                L.car_w, L.car_h, color, (255, 255, 255), False, False)
            self.vehicles[(color, "truck")] = render_car_sprite(
                L.truck_w, L.truck_h, color, (255, 255, 255), False, False)
        for car in CARS:
            sp, pad = render_car_sprite(
                L.car_w, L.car_h, car["color"], car["accent"],
                car["stripes"], car["spoiler"])
            sw = int(L.unit * 0.14)
            sh = int(sw * 1.85)
            sp_small, pad_small = render_car_sprite(
                sw, sh, car["color"], car["accent"],
                car["stripes"], car["spoiler"])
            self.car_sprites[car["id"]] = (sp, pad, sp_small, pad_small, car)
        self.coin_frames = render_coin_frames(max(6, int(L.unit * 0.032)))
        self.coin_r = max(6, int(L.unit * 0.032))
        self.powerup_frames = {}
        for kind in ("shield", "nitro", "magnet"):
            base_size = max(14, int(L.unit * 0.055))
            base = render_powerup_icon(kind, base_size)
            frames = []
            for i in range(12):
                t = i / 12.0
                pulse = 1.0 + 0.10 * math.sin(t * math.tau)
                fw = max(6, int(base.get_width() * pulse))
                fh = max(6, int(base.get_height() * pulse))
                frames.append(pygame.transform.scale(base, (fw, fh)))
            self.powerup_frames[kind] = frames
        heart_sz = max(10, int(L.unit * 0.040))
        self.heart_full = render_heart(heart_sz, True)
        self.heart_empty = render_heart(heart_sz, False)
        self.props = {}
        tints = [(74, 138, 58), (58, 118, 48), (88, 155, 66), (48, 100, 42)]
        for kind in ("tree", "bush", "rock", "lamp"):
            for ti, tint in enumerate(tints):
                size = max(6, int(L.unit * 0.055 * (0.75 + 0.13 * ti)))
                sprite, pad = render_prop_sprite(kind, size, tint)
                self.props[(kind, ti)] = (sprite, pad, size)
        ring_size = max(24, int(max(L.car_w, L.car_h) * 1.35))
        ring = pygame.Surface((ring_size, ring_size), pygame.SRCALPHA)
        pygame.draw.rect(ring, (100, 200, 255), i4((2, 2, ring_size - 4, ring_size - 4)), 3)
        pygame.draw.rect(ring, (200, 240, 255), i4((5, 5, ring_size - 10, ring_size - 10)), 1)
        self.shield_ring = ring
        gs = max(20, int(L.car_w * 3.5))
        glow = pygame.Surface((gs, gs), pygame.SRCALPHA)
        for i in range(5, 0, -1):
            t = i / 5.0
            r = int(gs * 0.5 * t)
            alpha = int(70 * (1.0 - t))
            if r > 0:
                pygame.draw.rect(glow, (255, 150, 60, alpha),
                                 i4((gs // 2 - r, gs // 2 - r, r * 2, r * 2)))
        self.nitro_glow = glow
        ms = max(20, int(L.car_w * 3.0))
        aura = pygame.Surface((ms, ms), pygame.SRCALPHA)
        for r in range(int(ms * 0.5), 0, -2):
            alpha = int(30 * (1.0 - r / (ms * 0.5)))
            if alpha > 0:
                pygame.draw.rect(aura, (255, 80, 170, alpha),
                                 i4((ms // 2 - r, ms // 2 - r, r * 2, r * 2)), 2)
        self.magnet_aura = aura

    def get(self, color, is_truck=False):
        key = (color, "truck" if is_truck else "car")
        s = self.vehicles.get(key)
        if s is None:
            Lc = self.L
            w = Lc.truck_w if is_truck else Lc.car_w
            h = Lc.truck_h if is_truck else Lc.car_h
            s = render_car_sprite(w, h, color, (255, 255, 255), False, False)
            self.vehicles[key] = s
        return s

    def get_player(self, car_id, lean):
        entry = self.car_sprites.get(car_id)
        if entry is None:
            entry = self.car_sprites["starter"]
        spr, pad = entry[0], entry[1]
        if abs(lean) < 0.08:
            return spr, pad, False
        key = (car_id, int(round(-lean * 5.0)))
        cached = self.player_rotations.get(key)
        if cached is None:
            try:
                cached = pygame.transform.rotate(spr, key * 2)
            except Exception:
                cached = spr
            self.player_rotations[key] = cached
        return cached, pad, True


class Particle:
    __slots__ = ("x", "y", "vx", "vy", "life", "max_life", "color", "size", "alive")
    def __init__(self):
        self.x = self.y = 0.0
        self.vx = self.vy = 0.0
        self.life = self.max_life = 0.0
        self.color = (255, 255, 255)
        self.size = 2.0
        self.alive = False


class ParticleSystem:
    def __init__(self, capacity=120):
        self.pool = [Particle() for _ in range(capacity)]
        self.index = 0
        self.capacity = capacity

    def emit(self, x, y, vx, vy, life, color, size):
        p = self.pool[self.index]
        p.x, p.y = x, y
        p.vx, p.vy = vx, vy
        p.life = p.max_life = max(0.01, life)
        p.color = color
        p.size = max(1.0, size)
        p.alive = True
        self.index = (self.index + 1) % self.capacity

    def update(self, dt):
        damp = max(0.0, 1.0 - 2.2 * dt)
        for p in self.pool:
            if not p.alive:
                continue
            p.life -= dt
            if p.life <= 0:
                p.alive = False
                continue
            p.x += p.vx * dt
            p.y += p.vy * dt
            p.vx *= damp
            p.vy *= damp

    def clear(self):
        for p in self.pool:
            p.alive = False

    def draw(self, surf):
        for p in self.pool:
            if not p.alive:
                continue
            t = p.life / p.max_life if p.max_life > 0 else 0
            sz = max(1, int(p.size * t))
            pygame.draw.rect(surf, p.color,
                             i4((int(p.x) - sz, int(p.y) - sz, sz * 2, sz * 2)))


class RoadRenderer:
    def __init__(self, L):
        self.L = L
        self.build()

    def build(self):
        L = self.L
        vw, vh = L.vw, L.vh
        bg = pygame.Surface((vw, vh)).convert()
        bg.fill(C_GRASS)
        pygame.draw.rect(bg, C_ROAD, i4((int(L.road_left), 0, int(L.road_w), vh)))
        for y in range(0, vh, 8):
            pygame.draw.line(bg, C_ROAD_DARK,
                             (int(L.road_left), y), (int(L.road_right), y), 1)
        ew = max(3, int(L.unit * 0.012))
        pygame.draw.rect(bg, C_EDGE, i4((int(L.road_left - ew), 0, ew, vh)))
        pygame.draw.rect(bg, (30, 25, 35), i4((int(L.road_left - ew - 1), 0, 1, vh)))
        pygame.draw.rect(bg, C_EDGE, i4((int(L.road_right), 0, ew, vh)))
        pygame.draw.rect(bg, (30, 25, 35), i4((int(L.road_right + ew), 0, 1, vh)))
        self.static_bg = bg

        self.grass_period = max(4, int(L.unit * 0.50))
        gh = self.grass_period * 2
        left_w = int(L.road_left) + 1
        right_w = vw - int(L.road_right)
        gt_l = pygame.Surface((left_w, gh), pygame.SRCALPHA).convert_alpha()
        gt_r = pygame.Surface((right_w, gh), pygame.SRCALPHA).convert_alpha()
        stripe_h = max(2, self.grass_period // 2)
        for target in (gt_l, gt_r):
            target.fill((0, 0, 0, 0))
            for i in range(2):
                yy = i * self.grass_period
                pygame.draw.rect(target, C_GRASS_DARK, i4((0, yy, target.get_width(), stripe_h)))
                row_y = yy + stripe_h
                for xx in range(0, target.get_width(), 4):
                    target.set_at((xx, row_y), C_GRASS_DARK)
                    target.set_at((xx + 2, row_y + 1), C_GRASS_DARK)
        self.grass_left = gt_l
        self.grass_right = gt_r

        dash, gap = L.unit * 0.100, L.unit * 0.090
        self.dash_period = max(4, int(dash + gap))
        self.dash_h = max(2, int(dash))
        mw = max(2, int(L.unit * 0.013))
        dt_surf = pygame.Surface((mw, self.dash_period * 2), pygame.SRCALPHA).convert_alpha()
        dt_surf.fill((0, 0, 0, 0))
        for i in range(2):
            pygame.draw.rect(dt_surf, C_STRIPE, i4((0, i * self.dash_period, mw, self.dash_h)))
        self.dash_tile = dt_surf
        self.dash_w = mw
        self.lane_x_positions = [
            int(L.road_left + L.lane_w * i - mw * 0.5) for i in range(1, L.lanes)
        ]

    def draw(self, surf, scroll):
        L = self.L
        vh = L.vh
        surf.blit(self.static_bg, (0, 0))
        gp = self.grass_period
        y_off = int(scroll) % gp
        y = y_off - gp
        surf.blit(self.grass_left, (0, y))
        surf.blit(self.grass_left, (0, y + gp))
        if y + 2 * gp < vh:
            surf.blit(self.grass_left, (0, y + 2 * gp))
        right_x = int(L.road_right)
        surf.blit(self.grass_right, (right_x, y))
        surf.blit(self.grass_right, (right_x, y + gp))
        if y + 2 * gp < vh:
            surf.blit(self.grass_right, (right_x, y + 2 * gp))
        dp = self.dash_period
        dy_off = int(scroll) % dp
        y = dy_off - dp
        for lx in self.lane_x_positions:
            surf.blit(self.dash_tile, (lx, y))
            surf.blit(self.dash_tile, (lx, y + dp))
            if y + 2 * dp < vh:
                surf.blit(self.dash_tile, (lx, y + 2 * dp))


class Player:
    def __init__(self, L, car_data, nitro_mult=1.0):
        self.L = L
        self.w = L.car_w
        self.h = L.car_h
        self.x = L.vw * 0.5 - self.w * 0.5
        self.y = L.player_y
        self.speed = 0.0
        self.base_max = 380.0 * L.ks * car_data.get("spd", 1.0)
        self.accel = 240.0 * L.ks * car_data.get("acc", 1.0)
        self.handling = car_data.get("hnd", 1.0)
        self.brake_power = 640.0 * L.ks
        self.friction = 110.0 * L.ks
        self.steer_speed = L.road_w * 0.98 * self.handling
        self.nitro_duration = 4.2 * nitro_mult
        self.lean = 0.0
        self.shield_time = 0.0
        self.nitro_time = 0.0
        self.magnet_time = 0.0
        self.invuln_time = 0.0
        self.bump = 0.0

    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), int(self.w), int(self.h))

    @property
    def hitbox(self):
        r = self.rect
        return r.inflate(-int(r.w * 0.22), -int(r.h * 0.12))

    @property
    def boosting(self):
        return self.nitro_time > 0.0

    def update(self, inputs, dt):
        L = self.L
        if self.shield_time > 0: self.shield_time = max(0.0, self.shield_time - dt)
        if self.nitro_time  > 0: self.nitro_time  = max(0.0, self.nitro_time  - dt)
        if self.magnet_time > 0: self.magnet_time = max(0.0, self.magnet_time - dt)
        if self.invuln_time > 0: self.invuln_time = max(0.0, self.invuln_time - dt)
        self.bump = max(0.0, self.bump - dt * 3.0)
        self.max_speed = self.base_max * (1.55 if self.boosting else 1.0)
        if inputs.get("GAS") or self.boosting:
            self.speed += self.accel * (2.2 if self.boosting else 1.0) * dt
        elif inputs.get("BRAKE"):
            self.speed -= self.brake_power * dt
        else:
            self.speed -= self.friction * dt
        if self.speed > self.max_speed:
            self.speed = max(self.max_speed, self.speed - 540.0 * L.ks * dt)
        if self.speed < 0.0:
            self.speed = 0.0
        self.speed = min(self.speed, self.base_max * 1.8)
        steer = (1.0 if inputs.get("RIGHT") else 0.0) - (1.0 if inputs.get("LEFT") else 0.0)
        grip = 0.45 + 0.55 * min(1.0, self.speed / (180.0 * L.ks))
        self.x += steer * self.steer_speed * grip * dt
        self.lean += (steer - self.lean) * min(1.0, dt * 11.0)
        lo = L.road_left + L.unit * 0.012
        hi = L.road_right - self.w - L.unit * 0.012
        if self.x < lo:
            self.x = lo
            self.speed *= max(0.0, 1.0 - 1.1 * dt)
            self.bump = 1.0
        elif self.x > hi:
            self.x = hi
            self.speed *= max(0.0, 1.0 - 1.1 * dt)
            self.bump = 1.0


class Obstacle:
    __slots__ = ("x", "y", "w", "h", "color", "speed", "is_truck")
    def __init__(self, x, y, w, h, color, speed, is_truck):
        self.x, self.y, self.w, self.h = float(x), float(y), w, h
        self.color = color
        self.speed = speed
        self.is_truck = is_truck
    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), int(self.w), int(self.h))
    @property
    def hitbox(self):
        r = self.rect
        return r.inflate(-int(r.w * 0.20), -int(r.h * 0.10))


class Coin:
    __slots__ = ("x", "y", "r", "spin")
    def __init__(self, x, y, r):
        self.x, self.y, self.r = float(x), float(y), r
        self.spin = random.uniform(0, math.tau)
    @property
    def rect(self):
        return pygame.Rect(int(self.x - self.r), int(self.y - self.r),
                           int(self.r * 2), int(self.r * 2))


class PowerUp:
    __slots__ = ("x", "y", "r", "kind", "spin")
    def __init__(self, x, y, r, kind):
        self.x, self.y, self.r = float(x), float(y), r
        self.kind = kind
        self.spin = random.uniform(0, math.tau)
    @property
    def rect(self):
        return pygame.Rect(int(self.x - self.r), int(self.y - self.r),
                           int(self.r * 2), int(self.r * 2))


class Prop:
    __slots__ = ("x", "y", "sprite", "pad", "size")
    def __init__(self, x, y, sprite, pad, size):
        self.x, self.y = float(x), float(y)
        self.sprite = sprite
        self.pad = pad
        self.size = size


class Game:
    def __init__(self, L, fonts, sprites, sfx, music):
        self.L = L
        self.fonts = fonts
        self.sprites = sprites
        self.sfx = sfx
        self.music = music
        self.save = load_save()
        self.hiscore = self.save.get("hiscore", 0)
        self.total_coins = self.save.get("total_coins", 0)
        self.total_distance = self.save.get("total_distance", 0)
        self.owned = set(self.save.get("owned", ["starter"]))
        self.selected = self.save.get("selected", "starter")
        self.settings = self.save.get("settings", dict(DEFAULT_SAVE["settings"]))
        self._apply_settings()
        self.new_record = False
        self.state = MENU
        self.particles = ParticleSystem(120)
        self.display_score = 0.0
        self.max_lives = 3
        self.menu_time = 0.0
        self.menu_car_offset = 0.0
        self.toast = ""
        self.toast_timer = 0.0
        self.garage_selected_index = 0
        self.reset()

    def _apply_settings(self):
        self.sfx.enabled = bool(self.settings.get("sound_on", True))
        self.music.set_enabled(bool(self.settings.get("music_on", True)))

    def _save_now(self):
        self.save["hiscore"] = self.hiscore
        self.save["total_coins"] = self.total_coins
        self.save["total_distance"] = self.total_distance
        self.save["owned"] = list(self.owned)
        self.save["selected"] = self.selected
        self.save["upgrades"] = self.save.get("upgrades", {})
        self.save["settings"] = dict(self.settings)
        save_save(self.save)

    def reset(self):
        L = self.L
        spd, acc, hnd, nitro_mult = get_effective_stats(self.save, self.selected)
        car_data = {"spd": spd, "acc": acc, "hnd": hnd}
        self.player = Player(L, car_data, nitro_mult)
        self.obstacles = []
        self.coins = []
        self.powerups = []
        self.props = []
        self.scroll = 0.0
        self.distance = 0.0
        self.coin_count = 0
        self.elapsed = 0.0
        self.score = 0
        self.display_score = 0.0
        self.spawn_cd = 1.0
        self.coin_cd = 1.6
        self.power_cd = random.uniform(8.0, 12.0)
        self.shake = 0.0
        self.over_timer = 0.0
        self.flash = 0.0
        self.damage_flash = 0.0
        self.combo = 1
        self.combo_timer = 0.0
        self.lives = self.max_lives
        self.near_miss_bonus = 0
        self.particles.clear()
        self._init_props()

    def start(self):
        self.reset()
        self.new_record = False
        self.state = PLAYING
        self.sfx.play("click")
        self.music.play("race")

    def show_toast(self, msg, duration=1.8):
        self.toast = msg
        self.toast_timer = duration

    @property
    def difficulty(self):
        return min(1.0, self.elapsed / 90.0)

    def _init_props(self):
        L = self.L
        for _ in range(14):
            self.props.append(self._make_prop(random.uniform(-L.vh * 0.6, L.vh)))

    def _make_prop(self, y):
        L = self.L
        side = random.choice((-1, 1))
        kind = random.choice(("tree", "tree", "tree", "bush", "rock", "lamp"))
        ti = random.randrange(4)
        sprite, pad, size = self.sprites.props[(kind, ti)]
        pad_d = size * 1.4 + L.unit * 0.012
        if side < 0:
            lo, hi = pad_d, max(pad_d + 1, L.road_left - pad_d)
        else:
            lo, hi = L.road_right + pad_d, max(L.road_right + pad_d + 1, L.vw - pad_d)
        return Prop(random.uniform(lo, hi), y, sprite, pad, size)

    def _respawn_prop(self, pr):
        L = self.L
        kind = random.choice(("tree", "tree", "tree", "bush", "rock", "lamp"))
        ti = random.randrange(4)
        sprite, pad, size = self.sprites.props[(kind, ti)]
        side = random.choice((-1, 1))
        pad_d = size * 1.4 + L.unit * 0.012
        if side < 0:
            lo, hi = pad_d, max(pad_d + 1, L.road_left - pad_d)
        else:
            lo, hi = L.road_right + pad_d, max(L.road_right + pad_d + 1, L.vw - pad_d)
        pr.x = random.uniform(lo, hi)
        pr.y = -random.uniform(L.unit * 0.4, L.vh * 0.55)
        pr.sprite, pr.pad, pr.size = sprite, pad, size

    def update_menu(self, dt):
        self.menu_time += dt
        self.menu_car_offset += dt * 40.0

    def garage_open(self):
        self.state = GARAGE
        try:
            self.garage_selected_index = [c["id"] for c in CARS].index(self.selected)
        except ValueError:
            self.garage_selected_index = 0
        self.sfx.play("click")

    def garage_next(self, delta=1):
        self.garage_selected_index = (self.garage_selected_index + delta) % len(CARS)
        self.sfx.play("click")

    def garage_buy_or_select(self):
        car = CARS[self.garage_selected_index]
        cid = car["id"]
        if cid in self.owned:
            self.selected = cid
            self._save_now()
            self.show_toast(f"SELECTED: {car['name']}")
            self.sfx.play("click")
        else:
            if self.total_coins >= car["price"]:
                self.total_coins -= car["price"]
                self.owned.add(cid)
                self.selected = cid
                self._save_now()
                self.show_toast(f"BOUGHT: {car['name']}!")
                self.sfx.play("buy")
            else:
                need = car["price"] - self.total_coins
                self.show_toast(f"NEED {need} MORE COINS!")
                self.sfx.play("fail")

    def try_buy_upgrade(self, kind):
        car = CARS[self.garage_selected_index]
        cid = car["id"]
        if cid not in self.owned:
            self.show_toast("BUY THE CAR FIRST!")
            self.sfx.play("fail")
            return
        defn = UPGRADE_DEFS[kind]
        cur_lv = get_upgrade_level(self.save, cid, kind)
        if cur_lv >= defn["max"]:
            self.show_toast("MAX LEVEL REACHED!")
            self.sfx.play("fail")
            return
        price = defn["prices"][cur_lv]
        if self.total_coins < price:
            self.show_toast(f"NEED {price - self.total_coins} MORE!")
            self.sfx.play("fail")
            return
        self.total_coins -= price
        ups = self.save.setdefault("upgrades", {}).setdefault(cid, {})
        ups[kind] = cur_lv + 1
        self._save_now()
        self.show_toast(f"{defn['name']}  ->  LV {cur_lv + 1}!")
        self.sfx.play("upgrade")

    def toggle_setting(self, key):
        if key not in self.settings:
            return
        self.settings[key] = not bool(self.settings[key])
        self._apply_settings()
        self._save_now()
        self.sfx.play("click")

    def reset_data(self):
        self.hiscore = 0
        self.total_coins = 0
        self.total_distance = 0
        self.owned = {"starter"}
        self.selected = "starter"
        self.save["upgrades"] = {}
        self._save_now()
        self.reset()
        self.show_toast("DATA RESET!")

    def update(self, inputs, dt):
        L = self.L
        dt = clamp(dt, 0.0, 0.05)
        self.shake = max(0.0, self.shake - dt * 42.0)
        self.flash = max(0.0, self.flash - dt * 3.2)
        self.damage_flash = max(0.0, self.damage_flash - dt * 2.0)
        if self.toast_timer > 0:
            self.toast_timer = max(0.0, self.toast_timer - dt)
        self.particles.update(dt)

        if self.state in (MENU, GARAGE, SETTINGS):
            self.update_menu(dt)
            return
        if self.state == GAMEOVER:
            self.over_timer += dt
            self.player.speed = max(0.0, self.player.speed - 260.0 * L.ks * dt)
            return
        if self.state != PLAYING:
            return

        self.elapsed += dt
        p = self.player
        p.update(inputs, dt)

        if self.combo_timer > 0:
            self.combo_timer -= dt
            if self.combo_timer <= 0:
                self.combo = 1

        move = p.speed * dt
        self.scroll += move
        self.distance += move
        self.score = (int(self.distance / (10.0 * L.ks))
                      + self.coin_count * 20 * self.combo
                      + self.near_miss_bonus)
        self.display_score += (self.score - self.display_score) * min(1.0, dt * 9.0)

        if p.boosting:
            self._emit_exhaust(dt, 2)
        elif p.speed > 200 * L.ks:
            self._emit_exhaust(dt, 0.4)

        vh = L.vh
        for pr in self.props:
            pr.y += move
            if pr.y - pr.size * 2.4 > vh:
                self._respawn_prop(pr)

        p_speed = p.speed
        for o in self.obstacles[:]:
            o.y += (p_speed - o.speed) * dt
            if o.y > vh + L.unit * 0.5 or o.y < -L.unit * 3.0:
                self.obstacles.remove(o)

        for c in self.coins[:]:
            c.y += move
            c.spin += dt * 5.0
            if c.y > vh + L.unit * 0.1:
                self.coins.remove(c)

        for pu in self.powerups[:]:
            pu.y += move
            pu.spin += dt * 3.0
            if pu.y > vh + L.unit * 0.2:
                self.powerups.remove(pu)

        if p.magnet_time > 0:
            px, py = p.x + p.w * 0.5, p.y + p.h * 0.5
            for c in self.coins:
                dx, dy = px - c.x, py - c.y
                dist = math.hypot(dx, dy)
                if 1 < dist < L.unit * 0.55:
                    c.x += (dx / dist) * 500 * dt
                    c.y += (dy / dist) * 500 * dt

        hit = p.hitbox
        for o in self.obstacles[:]:
            if hit.colliderect(o.hitbox):
                if p.shield_time > 0.0:
                    self.obstacles.remove(o)
                    self._burst(o.x + o.w * 0.5, o.y + o.h * 0.5, (140, 210, 255), 10)
                    self.near_miss_bonus += 15 * self.combo
                    self.sfx.play("click")
                    self.shake = max(self.shake, 5.0)
                elif p.invuln_time > 0.0:
                    pass
                else:
                    self.take_damage(o)
                    if self.state != PLAYING:
                        return
                    if o in self.obstacles:
                        self.obstacles.remove(o)

        for c in self.coins[:]:
            if hit.colliderect(c.rect):
                self.coins.remove(c)
                self.coin_count += 1
                self.combo = min(10, self.combo + 1)
                self.combo_timer = 3.0
                self._burst(c.x, c.y, (255, 220, 110), 6)
                self.sfx.play("coin")

        for pu in self.powerups[:]:
            if hit.colliderect(pu.rect):
                self.powerups.remove(pu)
                if pu.kind == "shield":
                    p.shield_time = 6.5
                    self._burst(pu.x, pu.y, C_SHIELD, 14)
                elif pu.kind == "nitro":
                    p.nitro_time = p.nitro_duration
                    self._burst(pu.x, pu.y, C_NITRO, 14)
                else:
                    p.magnet_time = 7.0
                    self._burst(pu.x, pu.y, C_MAGNET, 14)
                self.flash = 0.85
                self.sfx.play("power")

        self.spawn_cd -= dt
        if self.spawn_cd <= 0.0 and self._can_spawn():
            self.spawn_wave()
            self.spawn_cd = max(0.18, 0.55 - 0.30 * self.difficulty) / L.ks

        self.coin_cd -= dt
        if self.coin_cd <= 0.0:
            self._spawn_coins()
            self.coin_cd = random.uniform(1.4, 3.2) / L.ks

        self.power_cd -= dt
        if self.power_cd <= 0.0:
            self._spawn_powerup()
            self.power_cd = random.uniform(9.0, 15.0)

    def take_damage(self, obstacle):
        p = self.player
        self.lives -= 1
        self.damage_flash = 1.0
        self.shake = 18.0
        self.particles.clear()
        self._burst(p.x + p.w * 0.5, p.y + p.h * 0.5, (255, 200, 80), 18)
        self.sfx.play("hit")
        if self.lives <= 0:
            self.game_over()
            return
        p.x = self.L.vw * 0.5 - p.w * 0.5
        p.y = self.L.player_y
        p.speed *= 0.35
        p.invuln_time = 2.0
        self.combo = 1
        self.combo_timer = 0.0

    def _can_spawn(self):
        limit = self.L.vh * 0.30
        for o in self.obstacles:
            if o.y < limit:
                return False
        return True

    def spawn_wave(self):
        L = self.L
        d = self.difficulty
        max_blocked = min(L.lanes - 1, 1 + int(round(d * 2)))
        n = random.randint(1, max(1, max_blocked))
        lanes = random.sample(range(L.lanes), n)
        wave_speed = random.uniform(70.0, 170.0) * (1.0 - 0.25 * d) * L.ks
        for li in lanes:
            truck = random.random() < 0.18 + 0.10 * d
            if truck:
                w, h = L.truck_w, L.truck_h
                color = random.choice(SPECIAL_TRAFFIC)
            else:
                w, h = L.car_w, L.car_h
                color = random.choice(TRAFFIC_COLORS)
            x = L.lane_centers[li] - w * 0.5
            y = -h - random.uniform(0, L.unit * 0.10)
            self.obstacles.append(Obstacle(x, y, w, h, color, wave_speed, truck))

    def _free_lanes(self):
        L = self.L
        free = []
        for i in range(L.lanes):
            blocked = False
            for o in self.obstacles:
                if o.y < L.vh * 0.45 and \
                   abs((o.x + o.w * 0.5) - L.lane_centers[i]) < L.lane_w * 0.62:
                    blocked = True
                    break
            if not blocked:
                free.append(i)
        return free

    def _spawn_coins(self):
        free = self._free_lanes()
        if not free:
            return
        L = self.L
        li = random.choice(free)
        base_y = -L.unit * 0.10
        spacing = L.unit * 0.115 * L.ks
        for k in range(random.randint(2, 5)):
            self.coins.append(Coin(L.lane_centers[li], base_y - k * spacing,
                                   L.unit * 0.030))

    def _spawn_powerup(self):
        free = self._free_lanes()
        if not free:
            return
        L = self.L
        li = random.choice(free)
        kind = random.choice(("shield", "nitro", "magnet"))
        self.powerups.append(PowerUp(L.lane_centers[li], -L.unit * 0.12,
                                     L.unit * 0.055, kind))

    def _emit_exhaust(self, dt, strength):
        p = self.player
        L = self.L
        count = 1 if strength < 1 else 2
        for _ in range(count):
            if random.random() > 0.55:
                continue
            x = p.x + p.w * 0.5 + random.uniform(-p.w * 0.28, p.w * 0.28)
            y = p.y + p.h
            if not p.boosting:
                col = (150, 200, 255)
            else:
                col = random.choice([(255, 180, 60), (255, 120, 40), (255, 230, 140)])
            self.particles.emit(x, y, random.uniform(-40, 40) * L.ks,
                                random.uniform(90, 260) * L.ks,
                                random.uniform(0.15, 0.40), col,
                                random.uniform(2, 5) * (1.4 if p.boosting else 1.0))

    def _burst(self, x, y, color, n):
        L = self.L
        ks = L.ks
        n = min(n, 40)
        for _ in range(n):
            ang = random.uniform(0, math.tau)
            spd = random.uniform(40, 210) * ks
            self.particles.emit(x, y, math.cos(ang) * spd, math.sin(ang) * spd,
                                random.uniform(0.25, 0.65), color,
                                random.uniform(2, 5))

    def game_over(self):
        self.state = GAMEOVER
        self.over_timer = 0.0
        self.shake = 22.0
        self.flash = 1.0
        self.sfx.play("crash")
        p = self.player
        cx, cy = p.x + p.w * 0.5, p.y + p.h * 0.5
        palette = [(255, 230, 90), (255, 150, 40), (255, 80, 60),
                   (200, 200, 200), (120, 120, 120)]
        L = self.L
        for _ in range(36):
            ang = random.uniform(0, math.tau)
            spd = random.uniform(60, 440) * L.ks
            self.particles.emit(cx, cy, math.cos(ang) * spd, math.sin(ang) * spd,
                                random.uniform(0.4, 1.3), random.choice(palette),
                                random.uniform(3, 7))
        if self.score > self.hiscore:
            self.hiscore = self.score
            self.new_record = True
        self.total_coins += self.coin_count
        self.total_distance += int(self.distance / L.ks)
        self._save_now()


SPEED_LINES = []
_rnd = random.Random(7919)
for _i in range(24):
    SPEED_LINES.append({
        "x": _rnd.random(),
        "spd": 1.0 + _rnd.random() * 0.9,
        "len": 0.09 + 0.10 * _rnd.random(),
        "off": _i * 173,
    })


def draw_speed_lines(surf, L, scroll, intensity):
    if intensity <= 0.08:
        return
    intensity = clamp(intensity, 0.0, 1.0)
    max_lines = len(SPEED_LINES)
    n = min(max_lines, int(max_lines * intensity))
    rl = L.road_left
    rw = L.road_w
    vh = L.vh
    w = max(1, int(L.unit * 0.008))
    shade = int(90 + 50 * intensity)
    col = (shade, shade + 4, shade + 14)
    for i in range(n):
        if i >= max_lines:
            break
        ln = SPEED_LINES[i]
        x = rl + ln["x"] * rw
        length = L.unit * ln["len"]
        total = vh + length
        if total <= 0:
            continue
        y = (scroll * ln["spd"] * 1.7 + ln["off"]) % total - length
        pygame.draw.rect(surf, col, (int(x), int(y), w, int(length)))


def draw_entities(surf, L, game, sprites):
    p = game.player
    pad_coin = sprites.coin_frames[0][1] if sprites.coin_frames else 0
    for c in game.coins:
        if not sprites.coin_frames:
            break
        fr_idx = int(c.spin * len(sprites.coin_frames) / math.tau) % len(sprites.coin_frames)
        fr, _ = sprites.coin_frames[fr_idx]
        surf.blit(fr, (int(c.x - c.r - pad_coin), int(c.y - c.r - pad_coin)))
    for pu in game.powerups:
        frames = sprites.powerup_frames.get(pu.kind)
        if not frames:
            continue
        frame = frames[int(pu.spin * 2) % len(frames)]
        surf.blit(frame, (int(pu.x - frame.get_width() * 0.5),
                          int(pu.y - frame.get_height() * 0.5)))
    for o in game.obstacles:
        sprite, pad = sprites.get(o.color, o.is_truck)
        surf.blit(sprite, (int(o.x - pad), int(o.y - pad)))
    jx = jy = 0
    if game.state == PLAYING and p.speed > 200 * L.ks:
        amp = min(2.0, (p.speed / (380.0 * L.ks)) * 1.5)
        jx = random.uniform(-amp, amp)
        jy = random.uniform(-amp, amp)
    if p.nitro_time > 0.0:
        glow = sprites.nitro_glow
        try:
            glow.set_alpha(int(140 * min(1.0, p.nitro_time / 0.5)))
        except Exception:
            pass
        gw, gh = glow.get_size()
        surf.blit(glow, (int(p.x + p.w * 0.5 - gw * 0.5),
                         int(p.y + p.h * 0.5 - gh * 0.5)))
    if p.magnet_time > 0.0:
        aura = sprites.magnet_aura
        try:
            aura.set_alpha(int(120 * min(1.0, p.magnet_time / 1.0)))
        except Exception:
            pass
        aw, ah = aura.get_size()
        surf.blit(aura, (int(p.x + p.w * 0.5 - aw * 0.5),
                         int(p.y + p.h * 0.5 - ah * 0.5)))
    draw_player = True
    if p.invuln_time > 0 and int(p.invuln_time * 12) % 2 == 0:
        draw_player = False
    if draw_player:
        sprite, pad, rotated = sprites.get_player(game.selected, p.lean)
        px = int(p.x + jx)
        py = int(p.y + jy)
        if rotated:
            surf.blit(sprite, (px + p.w * 0.5 - sprite.get_width() * 0.5,
                               py + p.h * 0.5 - sprite.get_height() * 0.5))
        else:
            surf.blit(sprite, (px - pad, py - pad))
    if p.shield_time > 0.0:
        ring = sprites.shield_ring
        if not (p.shield_time < 1.6 and int(p.shield_time * 10) % 2 == 0):
            alpha = 100 + int(60 * math.sin(pygame.time.get_ticks() / 110.0))
            try:
                ring.set_alpha(clamp(alpha, 40, 220))
            except Exception:
                pass
            rw, rh = ring.get_size()
            surf.blit(ring, (int(p.x + p.w * 0.5 - rw * 0.5),
                             int(p.y + p.h * 0.5 - rh * 0.5)))
    game.particles.draw(surf)


def _draw_bar(surf, L, x, y, w, h, ratio, color):
    pygame.draw.rect(surf, (20, 18, 28), i4((x, y, w, h)))
    pygame.draw.rect(surf, (140, 130, 110), i4((x, y, w, h)), 1)
    inner_w = w - 4
    inner_h = h - 4
    if inner_w > 0 and inner_h > 0:
        fill_w = max(0, int(inner_w * clamp(ratio, 0.0, 1.0)))
        if fill_w > 0:
            pygame.draw.rect(surf, color, i4((x + 2, y + 2, fill_w, inner_h)))


def draw_hud(surf, L, game, fonts, digits, inputs):
    p = game.player
    fs = L.fsize
    m = int(L.unit * 0.020)
    panel = L.panel_score
    px = m
    py = m
    surf.blit(panel, (px, py))
    pw, ph = panel.get_size()
    pad = max(6, int(L.unit * 0.018))
    fonts.draw(surf, "SCORE", fs["tiny"], C_UI_ACCENT,
               (px + pad, py + pad), shadow=False, cache=True)
    digits.draw(surf, str(int(game.display_score)), fs["med"], C_WHITE,
                (px + pad, py + pad + int(fs["tiny"] * 1.15)))
    fonts.draw(surf, "BEST " + str(max(game.hiscore, game.score)),
               fs["tiny"], C_TEXT_DIM,
               (px + pad, py + ph - int(fs["tiny"] * 1.5)),
               shadow=False, cache=True)
    cy_badge = py + ph + m
    icon_r = max(6, int(fs["tiny"] * 0.55))
    pygame.draw.rect(surf, (90, 60, 10), i4((px + 2, cy_badge, icon_r * 2, icon_r * 2)))
    pygame.draw.rect(surf, C_COIN_DARK, i4((px + 3, cy_badge + 1, icon_r * 2 - 2, icon_r * 2 - 2)))
    pygame.draw.rect(surf, C_COIN, i4((px + 4, cy_badge + 2, icon_r * 2 - 4, icon_r * 2 - 4)))
    digits.draw(surf, str(game.coin_count), fs["small"], (255, 225, 140),
                (px + icon_r * 2 + 8, cy_badge + 2))
    if game.combo > 1:
        combo_col = (255, int(max(120, 240 - 20 * game.combo)), 60)
        fonts.draw(surf, f"x{game.combo}", fs["med"], combo_col,
                   (px + icon_r * 2 + 40, cy_badge), shadow=True, cache=True)
    lives_panel = L.panel_lives
    lw, lh = lives_panel.get_size()
    lx = L.vw - lw - m
    ly = m
    surf.blit(lives_panel, (lx, ly))
    heart = L.unit * 0.040
    heart_gap = heart * 1.1
    total_hearts_w = heart_gap * 3
    hx = lx + (lw - total_hearts_w) // 2
    hy = ly + (lh - heart) // 2
    for i in range(game.max_lives):
        img = game.sprites.heart_full if i < game.lives else game.sprites.heart_empty
        surf.blit(img, (int(hx + i * heart_gap), int(hy)))
    spd_panel = L.panel_speed
    spw, sph = spd_panel.get_size()
    spx = (L.vw - spw) // 2
    spy = m
    surf.blit(spd_panel, (spx, spy))
    inner_w = spw - 10
    inner_h = sph - 10
    ix = spx + 5
    iy = spy + 5
    pygame.draw.rect(surf, (30, 26, 38), i4((ix, iy, inner_w, inner_h)))
    ratio = clamp(p.speed / max(1.0, p.base_max * 1.55), 0.0, 1.0)
    if ratio > 0.001:
        fill_w = max(1, int(inner_w * ratio))
        col = lerp_color((80, 220, 120), (255, 90, 60), min(1.0, ratio / 0.85))
        if p.boosting:
            col = (255, 170, 70)
        pygame.draw.rect(surf, col, i4((ix, iy, fill_w, inner_h)))
    for i in range(1, 5):
        tx = ix + int(inner_w * (i / 5.0))
        pygame.draw.line(surf, (0, 0, 0), (tx, iy), (tx, iy + inner_h - 1), 1)
    kmh = int(p.speed / (3.0 * L.ks))
    digits.draw(surf, str(kmh), fs["med"], C_WHITE,
                (L.vw * 0.5, spy + sph + 4), anchor="midtop")
    fonts.draw(surf, "KM/H", fs["tiny"], C_TEXT_DIM,
               (L.vw * 0.5, spy + sph + 4 + int(fs["med"] * 1.1)),
               anchor="midtop", shadow=False, cache=True)
    bar_w = L.pu_bar_w
    bar_h = L.pu_bar_h
    by = py + ph + m + icon_r * 2 + m * 3
    bx = px
    for kind, t, total, fill_col in (
            ("SHIELD", p.shield_time, 6.5, C_SHIELD),
            ("NITRO",  p.nitro_time, p.nitro_duration, C_NITRO),
            ("MAGNET", p.magnet_time, 7.0, C_MAGNET)):
        if t <= 0:
            continue
        _draw_bar(surf, L, bx, by, bar_w, bar_h, t / total, fill_col)
        fonts.draw(surf, kind, fs["tiny"], C_TEXT,
                   (bx + bar_w + 6, by - 1), shadow=True, cache=True)
        by += bar_h + max(4, int(fs["tiny"] * 0.5))
    for key, rect in L.btn.items():
        pressed = inputs.get(key, False)
        bg_col = (95, 95, 120) if not pressed else (150, 210, 255)
        border_col = (200, 195, 180) if not pressed else (255, 255, 255)
        pygame.draw.rect(surf, (25, 25, 35), rect)
        pygame.draw.rect(surf, border_col, rect, 2)
        inset = 4 if not pressed else 6
        r2 = pygame.Rect(rect.x + inset, rect.y + inset,
                         rect.w - inset * 2, rect.h - inset * 2)
        pygame.draw.rect(surf, bg_col, r2)
        cx = rect.x + rect.w // 2
        cy = rect.y + rect.h // 2
        arrow_sz = rect.w // 5
        col = (255, 255, 255) if not pressed else (30, 30, 40)
        if key == "LEFT":
            pygame.draw.polygon(surf, col, [(cx + arrow_sz, cy - arrow_sz),
                                            (cx + arrow_sz, cy + arrow_sz),
                                            (cx - arrow_sz, cy)])
        elif key == "RIGHT":
            pygame.draw.polygon(surf, col, [(cx - arrow_sz, cy - arrow_sz),
                                            (cx - arrow_sz, cy + arrow_sz),
                                            (cx + arrow_sz, cy)])
        elif key == "GAS":
            pygame.draw.polygon(surf, col, [(cx - arrow_sz * 1.2, cy + arrow_sz),
                                            (cx + arrow_sz * 1.2, cy + arrow_sz),
                                            (cx, cy - arrow_sz * 1.1)])
        elif key == "BRAKE":
            pygame.draw.rect(surf, col, i4((cx - arrow_sz, cy - arrow_sz,
                                            arrow_sz * 2, arrow_sz * 2)))
    pb_rect = L.pause_btn
    pygame.draw.rect(surf, (25, 25, 35), pb_rect)
    pygame.draw.rect(surf, (200, 195, 180), pb_rect, 2)
    base_col = (60, 60, 78) if game.state != PAUSED else (110, 180, 240)
    pygame.draw.rect(surf, base_col,
                     i4((pb_rect.x + 4, pb_rect.y + 4, pb_rect.w - 8, pb_rect.h - 8)))
    if game.state == PAUSED:
        cx, cy = pb_rect.center
        sz = pb_rect.w // 4
        pygame.draw.polygon(surf, (255, 255, 255),
                            [(cx - sz, cy - sz), (cx - sz, cy + sz), (cx + sz, cy)])
    else:
        bw = max(3, pb_rect.w // 9)
        cx, cy = pb_rect.center
        pygame.draw.rect(surf, (255, 255, 255),
                         i4((cx - bw - 2, cy - pb_rect.h // 5, bw, pb_rect.h * 2 // 5)))
        pygame.draw.rect(surf, (255, 255, 255),
                         i4((cx + 2, cy - pb_rect.h // 5, bw, pb_rect.h * 2 // 5)))


def build_menu_background(L):
    vw, vh = L.vw, L.vh
    bg = pygame.Surface((vw, vh)).convert()
    bands = 20
    for i in range(bands):
        tt = i / (bands - 1)
        top = (255, 140, 80)
        mid = (255, 90, 130)
        bot = (60, 30, 90)
        if tt < 0.5:
            c = lerp_color(top, mid, tt * 2)
        else:
            c = lerp_color(mid, bot, (tt - 0.5) * 2)
        y0 = int(vh * i / bands)
        y1 = int(vh * (i + 1) / bands) + 1
        pygame.draw.rect(bg, c, i4((0, y0, vw, y1 - y0)))
    sun_cx = int(vw * 0.72)
    sun_cy = int(vh * 0.30)
    sun_r = int(L.unit * 0.12)
    for yy in range(-sun_r, sun_r + 1, 2):
        for xx in range(-sun_r, sun_r + 1, 2):
            if xx * xx + yy * yy <= sun_r * sun_r:
                bg.set_at((sun_cx + xx, sun_cy + yy), (255, 240, 180))
    def draw_mountains(base_y, height, color, step=20, seed=42):
        rnd = random.Random(seed)
        pts = []
        x = -step
        while x < vw + step:
            h = int(height * (0.5 + 0.5 * rnd.random()))
            pts.append((x, base_y - h))
            x += step
        for i in range(len(pts) - 1):
            x0, y0 = pts[i]
            x1, y1 = pts[i + 1]
            pygame.draw.polygon(bg, color,
                                [(x0, y0), (x1, y1), (x1, base_y), (x0, base_y)])
    draw_mountains(int(vh * 0.55), int(L.unit * 0.18), (140, 60, 110), 20, 42)
    draw_mountains(int(vh * 0.62), int(L.unit * 0.14), (90, 40, 80), 20, 7)
    ground_y = int(vh * 0.68)
    pygame.draw.rect(bg, (40, 30, 45), i4((0, ground_y, vw, vh - ground_y)))
    pygame.draw.rect(bg, C_GRASS_DARK, i4((0, ground_y, vw, 6)))
    pygame.draw.rect(bg, C_GRASS, i4((0, ground_y + 6, vw, 4)))
    road_y = ground_y + 14
    road_h = vh - road_y
    pygame.draw.rect(bg, (60, 60, 68), i4((0, road_y, vw, road_h)))
    pygame.draw.rect(bg, C_ROAD_LINE, i4((0, road_y, vw, 3)))
    return bg


def build_garage_background(L):
    vw, vh = L.vw, L.vh
    bg = pygame.Surface((vw, vh)).convert()
    for i in range(20):
        tt = i / 19
        c = lerp_color((40, 30, 60), (20, 15, 35), tt)
        pygame.draw.rect(bg, c, i4((0, int(vh * i / 20), vw, vh // 20 + 1)))
    rnd = random.Random(123)
    for _ in range(60):
        sx = rnd.randint(0, vw)
        sy = rnd.randint(0, int(vh * 0.5))
        bright = 100 + (int(sy * 0.5) % 100)
        bg.set_at((sx, sy), (bright, bright, bright))
    return bg


def build_settings_background(L):
    vw, vh = L.vw, L.vh
    bg = pygame.Surface((vw, vh)).convert()
    for i in range(20):
        tt = i / 19
        c = lerp_color((30, 40, 60), (15, 20, 35), tt)
        pygame.draw.rect(bg, c, i4((0, int(vh * i / 20), vw, vh // 20 + 1)))
    rnd = random.Random(99)
    for _ in range(40):
        sx = rnd.randint(0, vw)
        sy = rnd.randint(0, int(vh * 0.6))
        bright = 90 + (int(sy * 0.4) % 90)
        bg.set_at((sx, sy), (bright, bright, bright))
    return bg


def draw_main_menu(surf, L, game, fonts, digits, sprites, menu_bg):
    fs = L.fsize
    t = game.menu_time
    vw, vh = L.vw, L.vh
    surf.blit(menu_bg, (0, 0))
    ground_y = int(vh * 0.68)
    grass_y = ground_y + 6
    for i in range(14):
        gx = (i * 47 + int(t * 30)) % (vw + 20) - 10
        gy = grass_y + (i % 3) * 2
        pygame.draw.rect(surf, C_GRASS, i4((gx, gy, 2, 3)))
    road_y = ground_y + 14
    road_h = vh - road_y
    dash_off = int(t * 180) % 60
    for i in range(-1, vw // 60 + 2):
        dx = i * 60 - dash_off
        pygame.draw.rect(surf, (240, 240, 220),
                         i4((dx + 10, road_y + road_h // 2 - 2, 30, 4)))
    entry = sprites.car_sprites.get(game.selected)
    if entry:
        big_spr = entry[0]
        scale = 2.0
        bw = int(L.car_w * scale)
        bh = int(L.car_h * scale)
        hero = pygame.transform.scale(big_spr, (bw, bh))
        hx = int(vw * 0.5 - bw * 0.5)
        hy = int(vh * 0.68 - bh * 0.85 + math.sin(t * 3) * 4)
        shadow_w = int(bw * 0.85)
        shadow_surf = pygame.Surface((shadow_w, 10), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf, (0, 0, 0, 120), (0, 0, shadow_w, 10))
        surf.blit(shadow_surf, (int(vw * 0.5 - shadow_w / 2), hy + bh - 6))
        surf.blit(hero, (hx, hy))
    title_y = int(vh * 0.06)
    title_h = int(fs["big"] * 1.6)
    title_w = int(vw * 0.92)
    tx = (vw - title_w) // 2
    plaque = pygame.Surface((title_w, title_h), pygame.SRCALPHA)
    for yy in range(title_h):
        tt = yy / title_h
        c = lerp_color((140, 90, 50), (90, 50, 20), tt)
        pygame.draw.line(plaque, c, (0, yy), (title_w - 1, yy))
    for gy in range(4, title_h, 6):
        pygame.draw.line(plaque, (80, 45, 20), (4, gy), (title_w - 4, gy), 1)
    pygame.draw.rect(plaque, (30, 15, 5), i4((0, 0, title_w, title_h)), 4)
    pygame.draw.rect(plaque, (220, 180, 100), i4((4, 4, title_w - 8, title_h - 8)), 3)
    pygame.draw.rect(plaque, (255, 220, 150), i4((6, 6, title_w - 12, 2)))
    surf.blit(plaque, (tx, title_y))
    pulse = 0.5 + 0.5 * math.sin(t * 2.0)
    title_col = (255, int(220 + 30 * pulse), int(90 + 40 * pulse))
    title_shadow = (60, 30, 10)
    title_img = fonts.font(fs["big"]).render("TURBO RACER", False, title_col)
    title_sh = fonts.font(fs["big"]).render("TURBO RACER", False, title_shadow)
    trect = title_img.get_rect(center=(vw // 2, title_y + title_h // 2))
    surf.blit(title_sh, (trect.x + 3, trect.y + 3))
    surf.blit(title_img, trect)
    sub_y = title_y + title_h + 4
    fonts.draw(surf, "PIXEL EDITION", fs["small"], (255, 200, 100),
               (vw // 2, sub_y), anchor="midtop", shadow=True, cache=True)
    font_btn = fonts.font(fs["med"])
    for key, rect in L.main_btns.items():
        highlighted = (key == "PLAY")
        btn_surf = render_wood_button(rect.w, rect.h, key, font_btn, True, highlighted)
        surf.blit(btn_surf, (rect.x - 3, rect.y - 3))
    coin_sz = int(L.unit * 0.05)
    cx = vw - coin_sz - int(L.unit * 0.02)
    cy = int(L.unit * 0.02)
    pygame.draw.rect(surf, (90, 60, 10), i4((cx, cy, coin_sz, coin_sz)))
    pygame.draw.rect(surf, C_COIN_DARK, i4((cx + 2, cy + 2, coin_sz - 4, coin_sz - 4)))
    pygame.draw.rect(surf, C_COIN, i4((cx + 4, cy + 4, coin_sz - 8, coin_sz - 8)))
    pygame.draw.rect(surf, C_COIN_LIGHT, i4((cx + 6, cy + 6, coin_sz // 4, coin_sz // 3)))
    digits.draw(surf, str(game.total_coins), fs["small"], (255, 225, 140),
                (cx - 6, cy + coin_sz // 2), anchor="midright")
    fonts.draw(surf, f"BEST  {game.hiscore}", fs["med"], (255, 220, 90),
               (vw // 2, vh - int(L.unit * 0.045)), anchor="center",
               shadow=True, cache=True)
    if game.toast_timer > 0:
        toast_w = int(vw * 0.7)
        toast_h = int(fs["med"] * 1.3)
        toast_x = (vw - toast_w) // 2
        toast_y = int(vh * 0.88)
        toast_surf = pygame.Surface((toast_w, toast_h), pygame.SRCALPHA)
        toast_surf.fill((30, 20, 40, 220))
        pygame.draw.rect(toast_surf, (255, 220, 100), (0, 0, toast_w, toast_h), 2)
        surf.blit(toast_surf, (toast_x, toast_y))
        fonts.draw(surf, game.toast, fs["med"], C_WHITE,
                   (vw // 2, toast_y + toast_h // 2), anchor="center",
                   shadow=True, cache=True)


def draw_garage(surf, L, game, fonts, digits, sprites, garage_bg):
    fs = L.fsize
    vw, vh = L.vw, L.vh
    t = game.menu_time
    surf.blit(garage_bg, (0, 0))
    title_h = int(fs["big"] * 1.0)
    pygame.draw.rect(surf, (30, 20, 45), i4((0, 0, vw, title_h + 20)))
    pygame.draw.line(surf, (255, 200, 100), (0, title_h + 19), (vw, title_h + 19), 2)
    fonts.draw(surf, "GARAGE", fs["big"], (255, 210, 90),
               (vw // 2, title_h // 2 + 8), anchor="center",
               shadow=True, cache=True)
    back_rect = L.garage_back
    back_lbl = render_wood_button(back_rect.w, back_rect.h, "< BACK",
                                  fonts.font(fs["small"]), True, False)
    surf.blit(back_lbl, (back_rect.x - 3, back_rect.y - 3))
    coin_sz = int(L.unit * 0.05)
    cx = vw - coin_sz - int(L.unit * 0.02)
    cy = 8
    pygame.draw.rect(surf, (90, 60, 10), i4((cx, cy, coin_sz, coin_sz)))
    pygame.draw.rect(surf, C_COIN_DARK, i4((cx + 2, cy + 2, coin_sz - 4, coin_sz - 4)))
    pygame.draw.rect(surf, C_COIN, i4((cx + 4, cy + 4, coin_sz - 8, coin_sz - 8)))
    digits.draw(surf, str(game.total_coins), fs["small"], (255, 225, 140),
                (cx - 6, cy + coin_sz // 2), anchor="midright")
    car = CARS[game.garage_selected_index]
    cid = car["id"]
    display_y = title_h + 30
    display_h = int(vh * 0.24)
    panel_pad = int(L.unit * 0.02)
    panel_x = panel_pad
    panel_y = display_y
    panel_w = vw - panel_pad * 2
    panel_h = display_h
    pygame.draw.rect(surf, (25, 20, 40), i4((panel_x, panel_y, panel_w, panel_h)))
    pygame.draw.rect(surf, (255, 200, 100), i4((panel_x, panel_y, panel_w, panel_h)), 3)
    pygame.draw.rect(surf, (120, 90, 50), i4((panel_x + 4, panel_y + 4, panel_w - 8, panel_h - 8)), 1)
    entry = sprites.car_sprites.get(cid)
    if entry:
        big_spr = entry[0]
        scale = 1.9
        bw = int(L.car_w * scale)
        bh = int(L.car_h * scale)
        hero = pygame.transform.scale(big_spr, (bw, bh))
        hx = int(vw * 0.5 - bw * 0.5)
        hy = panel_y + (panel_h - bh) // 2 + int(math.sin(t * 2) * 3)
        surf.blit(hero, (hx, hy))
    name_y = panel_y + panel_h - int(fs["small"] * 2.2)
    fonts.draw(surf, car["name"], fs["med"], C_WHITE,
               (vw // 2, name_y), anchor="center", shadow=True, cache=True)
    if cid in game.owned:
        if cid == game.selected:
            status, col = "SELECTED", (120, 255, 120)
        else:
            status, col = "OWNED", (200, 220, 255)
    else:
        status, col = f"{car['price']} COINS", (255, 220, 100)
    fonts.draw(surf, status, fs["small"], col,
               (vw // 2, name_y + int(fs["med"] * 1.1)), anchor="center",
               shadow=True, cache=True)
    arrow_size = int(L.unit * 0.09)
    arrow_y = panel_y + panel_h // 2 - arrow_size // 2
    left_x = panel_x + int(L.unit * 0.02)
    left_rect = pygame.Rect(left_x, arrow_y, arrow_size, arrow_size)
    pygame.draw.rect(surf, (60, 40, 80), left_rect)
    pygame.draw.rect(surf, (255, 200, 100), left_rect, 2)
    pygame.draw.polygon(surf, (255, 240, 200),
                        [(left_x + arrow_size - 8, arrow_y + 6),
                         (left_x + arrow_size - 8, arrow_y + arrow_size - 6),
                         (left_x + 8, arrow_y + arrow_size // 2)])
    right_x = panel_x + panel_w - arrow_size - int(L.unit * 0.02)
    right_rect = pygame.Rect(right_x, arrow_y, arrow_size, arrow_size)
    pygame.draw.rect(surf, (60, 40, 80), right_rect)
    pygame.draw.rect(surf, (255, 200, 100), right_rect, 2)
    pygame.draw.polygon(surf, (255, 240, 200),
                        [(right_x + 8, arrow_y + 6),
                         (right_x + 8, arrow_y + arrow_size - 6),
                         (right_x + arrow_size - 8, arrow_y + arrow_size // 2)])
    stats_y = panel_y + panel_h + int(L.unit * 0.010)
    eff_spd, eff_acc, eff_hnd, _ = get_effective_stats(game.save, cid)
    stat_labels = [("SPD", eff_spd), ("ACC", eff_acc), ("HND", eff_hnd)]
    stat_w = int(panel_w * 0.72)
    stat_x = panel_x + (panel_w - stat_w) // 2
    bar_h = max(7, int(L.unit * 0.014))
    for i, (label, val) in enumerate(stat_labels):
        y = stats_y + i * (bar_h + int(fs["tiny"] * 1.15))
        fonts.draw(surf, label, fs["tiny"], C_TEXT,
                   (stat_x, y), shadow=True, cache=True)
        bar_x = stat_x + int(panel_w * 0.28)
        bar_w = stat_w - int(panel_w * 0.28)
        pygame.draw.rect(surf, (20, 15, 30), i4((bar_x, y + 2, bar_w, bar_h)))
        pygame.draw.rect(surf, (200, 180, 140), i4((bar_x, y + 2, bar_w, bar_h)), 1)
        ratio = clamp((val - 0.9) / 0.6, 0.05, 1.0)
        fill_w = int((bar_w - 4) * ratio)
        col_bar = (255, 100 + int(120 * (1 - ratio)), 60) if ratio > 0.6 else (120, 220, 120)
        pygame.draw.rect(surf, col_bar,
                         i4((bar_x + 2, y + 4, max(2, fill_w), bar_h - 4)))
    upg_y = stats_y + 3 * (bar_h + int(fs["tiny"] * 1.15)) + int(L.unit * 0.006)
    fonts.draw(surf, "UPGRADES", fs["small"], C_UI_ACCENT,
               (vw // 2, upg_y), anchor="midtop", shadow=True, cache=True)
    upg_y += int(fs["small"] * 1.25)
    upg_row_h = int(L.unit * 0.070)
    upg_row_gap = int(L.unit * 0.006)
    upg_x = panel_x + int(L.unit * 0.02)
    upg_w = panel_w - int(L.unit * 0.04)
    upgrade_rects = {}
    for kind in ("engine", "tires", "nitro"):
        defn = UPGRADE_DEFS[kind]
        lv = get_upgrade_level(game.save, cid, kind)
        maxed = lv >= defn["max"]
        row_rect = pygame.Rect(upg_x, upg_y, upg_w, upg_row_h)
        row_bg = (60, 45, 25) if maxed else (30, 25, 45)
        pygame.draw.rect(surf, row_bg, row_rect)
        pygame.draw.rect(surf, (140, 120, 90), row_rect, 2)
        fonts.draw(surf, defn["name"], fs["small"], C_WHITE,
                   (row_rect.x + 8, row_rect.y + 3), shadow=True, cache=True)
        pip_sz = max(6, int(L.unit * 0.016))
        pip_x = row_rect.x + 8
        pip_y = row_rect.y + row_rect.h - pip_sz - 5
        for i in range(defn["max"]):
            px_r = pygame.Rect(pip_x + i * (pip_sz + 3), pip_y, pip_sz, pip_sz)
            if i < lv:
                pygame.draw.rect(surf, (120, 255, 120), px_r)
                pygame.draw.rect(surf, (60, 180, 60), px_r, 1)
            else:
                pygame.draw.rect(surf, (45, 45, 60), px_r)
                pygame.draw.rect(surf, (90, 90, 110), px_r, 1)
        if maxed:
            price_txt = "MAX"
            price_col = (255, 200, 100)
        elif cid not in game.owned:
            price_txt = "LOCKED"
            price_col = (160, 160, 170)
        else:
            price_txt = f"{defn['prices'][lv]}"
            price_col = (255, 220, 100) if game.total_coins >= defn["prices"][lv] else (200, 100, 100)
        fonts.draw(surf, price_txt, fs["small"], price_col,
                   (row_rect.right - 10, row_rect.centery),
                   anchor="midright", shadow=True, cache=True)
        upgrade_rects[kind] = row_rect
        upg_y += upg_row_h + upg_row_gap
    action_w = int(vw * 0.55)
    action_h = int(L.unit * 0.11)
    action_x = (vw - action_w) // 2
    action_y = vh - action_h - int(L.unit * 0.025)
    if cid in game.owned:
        if cid == game.selected:
            action_label = "SELECTED"
            action_enabled = False
        else:
            action_label = "SELECT"
            action_enabled = True
    else:
        if game.total_coins >= car["price"]:
            action_label = "BUY"
            action_enabled = True
        else:
            action_label = "NEED COINS"
            action_enabled = False
    btn_surf = render_wood_button(action_w, action_h, action_label,
                                  fonts.font(fs["med"]),
                                  action_enabled, action_enabled)
    surf.blit(btn_surf, (action_x - 3, action_y - 3))
    L._garage_left_rect = left_rect
    L._garage_right_rect = right_rect
    L._garage_action_rect = pygame.Rect(action_x, action_y, action_w, action_h)
    L._garage_upgrade_rects = upgrade_rects
    if game.toast_timer > 0:
        toast_w = int(vw * 0.7)
        toast_h = int(fs["med"] * 1.3)
        toast_x = (vw - toast_w) // 2
        toast_y = int(vh * 0.50)
        toast_surf = pygame.Surface((toast_w, toast_h), pygame.SRCALPHA)
        toast_surf.fill((30, 20, 40, 230))
        pygame.draw.rect(toast_surf, (255, 220, 100), (0, 0, toast_w, toast_h), 2)
        surf.blit(toast_surf, (toast_x, toast_y))
        fonts.draw(surf, game.toast, fs["med"], C_WHITE,
                   (vw // 2, toast_y + toast_h // 2), anchor="center",
                   shadow=True, cache=True)


def draw_settings(surf, L, game, fonts, digits, settings_bg):
    fs = L.fsize
    vw, vh = L.vw, L.vh
    surf.blit(settings_bg, (0, 0))
    title_h = int(fs["big"] * 1.0)
    pygame.draw.rect(surf, (20, 25, 45), i4((0, 0, vw, title_h + 20)))
    pygame.draw.line(surf, (150, 200, 255), (0, title_h + 19), (vw, title_h + 19), 2)
    fonts.draw(surf, "SETTINGS", fs["big"], (180, 220, 255),
               (vw // 2, title_h // 2 + 8), anchor="center",
               shadow=True, cache=True)
    back_rect = L.garage_back
    back_lbl = render_wood_button(back_rect.w, back_rect.h, "< BACK",
                                  fonts.font(fs["small"]), True, False)
    surf.blit(back_lbl, (back_rect.x - 3, back_rect.y - 3))
    setting_defs = [
        ("sound_on",    "SOUND"),
        ("music_on",    "MUSIC"),
        ("flip_controls", "FLIP CONTROLS"),
        ("high_quality", "HIGH QUALITY"),
    ]
    row_h = int(L.unit * 0.09)
    row_gap = int(L.unit * 0.010)
    y = title_h + 30
    row_x = int(vw * 0.08)
    row_w = int(vw * 0.84)
    setting_rects = {}
    for key, label in setting_defs:
        row_rect = pygame.Rect(row_x, y, row_w, row_h)
        pygame.draw.rect(surf, (30, 35, 55), row_rect)
        pygame.draw.rect(surf, (150, 200, 255), row_rect, 2)
        fonts.draw(surf, label, fs["med"], C_WHITE,
                   (row_rect.x + 14, row_rect.centery),
                   anchor="midleft", shadow=True, cache=True)
        val = bool(game.settings.get(key, False))
        val_txt = "ON" if val else "OFF"
        val_col = (120, 255, 120) if val else (200, 100, 100)
        fonts.draw(surf, val_txt, fs["med"], val_col,
                   (row_rect.right - 14, row_rect.centery),
                   anchor="midright", shadow=True, cache=True)
        setting_rects[key] = row_rect
        y += row_h + row_gap
    stats_y = y + int(L.unit * 0.015)
    stats_h = int(L.unit * 0.26)
    stats_rect = pygame.Rect(row_x, stats_y, row_w, stats_h)
    pygame.draw.rect(surf, (20, 25, 45), stats_rect)
    pygame.draw.rect(surf, (255, 200, 100), stats_rect, 2)
    fonts.draw(surf, "STATISTICS", fs["small"], C_UI_ACCENT,
               (stats_rect.centerx, stats_rect.y + 6), anchor="midtop",
               shadow=True, cache=True)
    stat_lines = [
        f"BEST SCORE: {game.hiscore}",
        f"TOTAL COINS: {game.total_coins}",
        f"DISTANCE: {game.total_distance} km",
        f"CARS OWNED: {len(game.owned)} / {len(CARS)}",
    ]
    ly = stats_rect.y + int(fs["small"] * 1.5)
    for line in stat_lines:
        fonts.draw(surf, line, fs["small"], C_TEXT,
                   (stats_rect.x + 12, ly), shadow=True, cache=True)
        ly += int(fs["small"] * 1.25)
    reset_y = vh - int(L.unit * 0.14)
    reset_w = int(vw * 0.55)
    reset_x = (vw - reset_w) // 2
    reset_h = int(L.unit * 0.09)
    reset_surf = render_wood_button(reset_w, reset_h, "RESET DATA",
                                     fonts.font(fs["med"]), True, False)
    surf.blit(reset_surf, (reset_x - 3, reset_y - 3))
    pygame.draw.rect(surf, (255, 80, 80),
                     pygame.Rect(reset_x, reset_y, reset_w, reset_h), 2)
    L._settings_rects = setting_rects
    L._settings_reset_rect = pygame.Rect(reset_x, reset_y, reset_w, reset_h)
    if game.toast_timer > 0:
        toast_w = int(vw * 0.7)
        toast_h = int(fs["med"] * 1.3)
        toast_x = (vw - toast_w) // 2
        toast_y = int(vh * 0.80)
        toast_surf = pygame.Surface((toast_w, toast_h), pygame.SRCALPHA)
        toast_surf.fill((30, 20, 40, 230))
        pygame.draw.rect(toast_surf, (255, 220, 100), (0, 0, toast_w, toast_h), 2)
        surf.blit(toast_surf, (toast_x, toast_y))
        fonts.draw(surf, game.toast, fs["med"], C_WHITE,
                   (vw // 2, toast_y + toast_h // 2), anchor="center",
                   shadow=True, cache=True)


def draw_paused(surf, L, game, fonts, overlay):
    fs = L.fsize
    surf.blit(overlay, (0, 0))
    cx = L.vw * 0.5
    banner_w = int(L.vw * 0.6)
    banner_h = int(fs["big"] * 1.3)
    bx = (L.vw - banner_w) // 2
    by = int(L.vh * 0.28)
    pygame.draw.rect(surf, (20, 15, 30), i4((bx, by, banner_w, banner_h)))
    pygame.draw.rect(surf, C_UI_BORDER, i4((bx, by, banner_w, banner_h)), 3)
    fonts.draw(surf, "PAUSED", fs["big"], C_WHITE,
               (cx, by + banner_h // 2), anchor="center", shadow=True, cache=True)
    for key, rect in L.menu_btns.items():
        btn = render_wood_button(rect.w, rect.h, key, fonts.font(fs["med"]), True, key == "RESUME")
        surf.blit(btn, (rect.x - 3, rect.y - 3))


def draw_gameover(surf, L, game, fonts, digits, overlay):
    fs = L.fsize
    surf.blit(overlay, (0, 0))
    cx = L.vw * 0.5
    banner_w = int(L.vw * 0.75)
    banner_h = int(fs["big"] * 1.3)
    bx = (L.vw - banner_w) // 2
    by = int(L.vh * 0.12)
    pygame.draw.rect(surf, (30, 15, 20), i4((bx, by, banner_w, banner_h)))
    pygame.draw.rect(surf, C_UI_BORDER, i4((bx, by, banner_w, banner_h)), 3)
    fonts.draw(surf, "CRASHED!", fs["big"], (255, 200, 200),
               (cx, by + banner_h // 2), anchor="center", shadow=True, cache=True)
    sc_w = int(L.vw * 0.60)
    sc_h = int(fs["huge"] * 1.5)
    sc_x = (L.vw - sc_w) // 2
    sc_y = int(L.vh * 0.35)
    pygame.draw.rect(surf, (20, 15, 30), i4((sc_x, sc_y, sc_w, sc_h)))
    pygame.draw.rect(surf, C_UI_BORDER, i4((sc_x, sc_y, sc_w, sc_h)), 3)
    fonts.draw(surf, "SCORE", fs["small"], C_UI_ACCENT,
               (cx, sc_y + int(fs["small"] * 0.9)), anchor="center",
               shadow=False, cache=True)
    digits.draw(surf, str(int(game.display_score)), fs["huge"], C_WHITE,
                (cx, sc_y + sc_h // 2 + int(fs["small"] * 0.5)), anchor="center")
    coins_y = sc_y + sc_h + int(L.unit * 0.02)
    coin_sz = int(L.unit * 0.045)
    coin_x = cx - int(L.unit * 0.10)
    pygame.draw.rect(surf, C_COIN_DARK, i4((coin_x, coins_y, coin_sz, coin_sz)))
    pygame.draw.rect(surf, C_COIN, i4((coin_x + 2, coins_y + 2, coin_sz - 4, coin_sz - 4)))
    fonts.draw(surf, f"+{game.coin_count}", fs["med"], (255, 225, 140),
               (coin_x + coin_sz + 8, coins_y + coin_sz // 2),
               anchor="midleft", shadow=True, cache=True)
    if game.new_record:
        pulse = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() / 200.0)
        col = (255, int(190 + 60 * pulse), 60)
        fonts.draw(surf, "NEW RECORD!", fs["med"], col,
                   (cx, L.vh * 0.68), anchor="center", shadow=True, cache=True)
    else:
        fonts.draw(surf, "BEST  " + str(game.hiscore), fs["small"],
                   C_TEXT_DIM, (cx, L.vh * 0.68), anchor="center",
                   shadow=True, cache=True)
    if game.over_timer > 0.6:
        p2 = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() / 320.0)
        col = (int(200 + 55 * p2), int(230 + 25 * p2), 255)
        fonts.draw(surf, "TAP  TO  CONTINUE", fs["med"], col,
                   (cx, L.vh * 0.88), anchor="center",
                   shadow=True, cache=True)


def main():
    try:
        pygame.mixer.pre_init(44100, -16, 2, 512)
    except Exception:
        pass

    pygame.init()

    try:
        pygame.mouse.set_visible(False)
    except Exception:
        pass

    try:
        info = pygame.display.Info()
        sw, sh = info.current_w, info.current_h
    except Exception:
        sw, sh = 800, 480

    try:
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        sw, sh = screen.get_size()
    except Exception:
        screen = pygame.display.set_mode((sw, sh))

    pygame.display.set_caption("Turbo Racer - Pixel Edition")

    L = Layout(sw, sh)
    virtual = pygame.Surface((L.vw, L.vh)).convert()
    fonts = FontCache()
    digits = DigitCache()
    sprites = Sprites(L)
    sfx = Sfx()
    sfx.init()
    music = Music()
    music.init()

    if music.ok:
        try:
            menu_melody = [
                (0, 1), (4, 1), (7, 1), (4, 1),
                (0, 1), (4, 1), (7, 1), (12, 1),
                (5, 1), (9, 1), (12, 1), (9, 1),
                (5, 1), (9, 1), (12, 1), (7, 1),
            ]
            menu_bass = [
                (0, 2), (-5, 2),
                (0, 2), (-5, 2),
                (5, 2), (0, 2),
                (5, 2), (-5, 2),
            ]
            music.generate("menu", menu_melody, menu_bass, 100, "square")

            race_melody = [
                (7, 1), (7, 0.5), (9, 0.5), (7, 1), (5, 1), (4, 1),
                (7, 1), (7, 0.5), (9, 0.5), (7, 1), (12, 1),
                (7, 1), (7, 0.5), (9, 0.5), (7, 1), (5, 1), (4, 1),
                (7, 1), (12, 1), (7, 1), (0, 1),
            ]
            race_bass = [
                (0, 2), (0, 2), (5, 2), (5, 2),
                (7, 2), (7, 2), (5, 2), (0, 2),
            ]
            music.generate("race", race_melody, race_bass, 150, "square")
        except Exception:
            pass

    menu_bg = build_menu_background(L)
    garage_bg = build_garage_background(L)
    settings_bg = build_settings_background(L)
    road_renderer = RoadRenderer(L)

    game = Game(L, fonts, sprites, sfx, music)

    overlay_dark = pygame.Surface((L.vw, L.vh), pygame.SRCALPHA)
    overlay_dark.fill((10, 8, 20, 210))
    overlay_red = pygame.Surface((L.vw, L.vh), pygame.SRCALPHA)
    overlay_red.fill((120, 12, 20, 180))
    flash_surf = pygame.Surface((L.vw, L.vh))
    flash_surf.fill((255, 255, 255))
    damage_surf = pygame.Surface((L.vw, L.vh))
    damage_surf.fill((255, 40, 40))

    clock = pygame.time.Clock()
    touch_owner = {}
    frame = 0
    inputs = {k: False for k in L.btn}

    def to_virtual(sx, sy):
        return ((sx - L.ox) / L.scale, (sy - L.oy) / L.scale)

    def hit(vx, vy):
        for key, rect in L.btn.items():
            if rect.collidepoint(vx, vy):
                return key
        if L.pause_btn.collidepoint(vx, vy) and game.state in (PLAYING, PAUSED):
            return "PAUSE"
        if game.state == PAUSED:
            for key, rect in L.menu_btns.items():
                if rect.collidepoint(vx, vy):
                    return key
        if game.state == MENU:
            for key, rect in L.main_btns.items():
                if rect.collidepoint(vx, vy):
                    return "MENU_" + key
        if game.state == GARAGE:
            if hasattr(L, "_garage_left_rect") and L._garage_left_rect.collidepoint(vx, vy):
                return "GARAGE_LEFT"
            if hasattr(L, "_garage_right_rect") and L._garage_right_rect.collidepoint(vx, vy):
                return "GARAGE_RIGHT"
            if hasattr(L, "_garage_action_rect") and L._garage_action_rect.collidepoint(vx, vy):
                return "GARAGE_ACTION"
            if hasattr(L, "_garage_upgrade_rects"):
                for kind, r in L._garage_upgrade_rects.items():
                    if r.collidepoint(vx, vy):
                        return "GARAGE_UPG_" + kind
            if L.garage_back.collidepoint(vx, vy):
                return "GARAGE_BACK"
        if game.state == SETTINGS:
            if L.garage_back.collidepoint(vx, vy):
                return "SETTINGS_BACK"
            if hasattr(L, "_settings_rects"):
                for key, r in L._settings_rects.items():
                    if r.collidepoint(vx, vy):
                        return "SETTING_" + key
            if hasattr(L, "_settings_reset_rect") and L._settings_reset_rect.collidepoint(vx, vy):
                return "SETTINGS_RESET"
        return None

    def on_press(vpos):
        if game.state == MENU:
            for key, rect in L.main_btns.items():
                if rect.collidepoint(vpos):
                    if key == "PLAY":
                        game.start()
                    elif key == "GARAGE":
                        game.garage_open()
                    elif key == "SETTINGS":
                        game.state = SETTINGS
                        game.sfx.play("click")
                    elif key == "EXIT":
                        pygame.event.post(pygame.event.Event(pygame.QUIT))
                    return
        elif game.state == GARAGE:
            if hasattr(L, "_garage_left_rect") and L._garage_left_rect.collidepoint(vpos):
                game.garage_next(-1)
            elif hasattr(L, "_garage_right_rect") and L._garage_right_rect.collidepoint(vpos):
                game.garage_next(1)
            elif hasattr(L, "_garage_action_rect") and L._garage_action_rect.collidepoint(vpos):
                game.garage_buy_or_select()
            elif hasattr(L, "_garage_upgrade_rects"):
                for kind, r in L._garage_upgrade_rects.items():
                    if r.collidepoint(vpos):
                        game.try_buy_upgrade(kind)
                        return
            elif L.garage_back.collidepoint(vpos):
                game.state = MENU
                game.sfx.play("click")
        elif game.state == SETTINGS:
            if L.garage_back.collidepoint(vpos):
                game.state = MENU
                game.sfx.play("click")
            elif hasattr(L, "_settings_rects"):
                for key, r in L._settings_rects.items():
                    if r.collidepoint(vpos):
                        game.toggle_setting(key)
                        return
            if hasattr(L, "_settings_reset_rect") and L._settings_reset_rect.collidepoint(vpos):
                game.reset_data()
        elif game.state == GAMEOVER:
            if game.over_timer > 0.6:
                game.start()
        elif game.state == PLAYING:
            if L.pause_btn.collidepoint(vpos):
                game.state = PAUSED
        elif game.state == PAUSED:
            if L.menu_btns["RESUME"].collidepoint(vpos) or L.pause_btn.collidepoint(vpos):
                game.state = PLAYING
            elif L.menu_btns["RESTART"].collidepoint(vpos):
                game.start()

    if music.ok:
        music.play("menu")

    running = True
    while running:
        dt = min(clock.tick(FPS) / 1000.0, 0.05)
        frame += 1

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.FINGERDOWN:
                vpos = to_virtual(event.x * sw, event.y * sh)
                touch_owner[("f", event.finger_id)] = hit(*vpos)
                on_press(vpos)
            elif event.type == pygame.FINGERMOTION:
                key = ("f", event.finger_id)
                if key in touch_owner:
                    touch_owner[key] = hit(*to_virtual(event.x * sw, event.y * sh))
            elif event.type == pygame.FINGERUP:
                touch_owner.pop(("f", event.finger_id), None)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                vpos = to_virtual(event.pos[0], event.pos[1])
                touch_owner[("m", event.button)] = hit(*vpos)
                on_press(vpos)
            elif event.type == pygame.MOUSEBUTTONUP:
                touch_owner.pop(("m", event.button), None)
            elif event.type == pygame.MOUSEMOTION:
                if ("m", 1) in touch_owner and \
                   not any(k[0] == "f" for k in touch_owner):
                    touch_owner[("m", 1)] = hit(*to_virtual(event.pos[0], event.pos[1]))
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if game.state == PLAYING:
                        game.state = PAUSED
                    elif game.state == PAUSED:
                        game.state = PLAYING
                    elif game.state in (GARAGE, SETTINGS):
                        game.state = MENU
                    elif game.state == MENU:
                        running = False
                    else:
                        game.state = MENU
                elif event.key == pygame.K_p and game.state == PLAYING:
                    game.state = PAUSED
                elif event.key in (pygame.K_SPACE, pygame.K_RETURN):
                    if game.state in (MENU, GAMEOVER):
                        game.start()
                elif game.state == GARAGE:
                    if event.key == pygame.K_LEFT:
                        game.garage_next(-1)
                    elif event.key == pygame.K_RIGHT:
                        game.garage_next(1)
                    elif event.key == pygame.K_RETURN:
                        game.garage_buy_or_select()
                elif game.state == SETTINGS:
                    if event.key == pygame.K_r:
                        game.reset_data()

        for k in inputs:
            inputs[k] = False
        for v in touch_owner.values():
            if v in inputs:
                if game.settings.get("flip_controls", False):
                    if v == "LEFT":
                        inputs["RIGHT"] = True
                    elif v == "RIGHT":
                        inputs["LEFT"] = True
                    else:
                        inputs[v] = True
                else:
                    inputs[v] = True

        try:
            if music.ok and game.settings.get("music_on", True):
                if game.state in (MENU, GARAGE, SETTINGS):
                    music.play("menu")
                elif game.state in (PLAYING, PAUSED, GAMEOVER):
                    music.play("race")
        except Exception:
            pass

        try:
            game.update(inputs, dt)
        except Exception:
            log_exception(traceback.format_exc())

        try:
            if game.state == MENU:
                draw_main_menu(virtual, L, game, fonts, digits, sprites, menu_bg)
            elif game.state == GARAGE:
                draw_garage(virtual, L, game, fonts, digits, sprites, garage_bg)
            elif game.state == SETTINGS:
                draw_settings(virtual, L, game, fonts, digits, settings_bg)
            else:
                road_renderer.draw(virtual, game.scroll)
                vh = L.vh
                for pr in game.props:
                    py = pr.y
                    if py - pr.size * 2 > vh or py + pr.size * 3 < 0:
                        continue
                    virtual.blit(pr.sprite, (int(pr.x - pr.pad), int(py - pr.pad)))
                speed_intensity = min(1.0, max(
                    0.0, (game.player.speed / (380.0 * L.ks)) - 0.55) * 2.4)
                draw_speed_lines(virtual, L, game.scroll, speed_intensity)
                draw_entities(virtual, L, game, sprites)
                draw_hud(virtual, L, game, fonts, digits, inputs)
                if game.state == PAUSED:
                    draw_paused(virtual, L, game, fonts, overlay_dark)
                elif game.state == GAMEOVER:
                    draw_gameover(virtual, L, game, fonts, digits, overlay_red)
                if game.flash > 0.01:
                    flash_surf.set_alpha(int(70 * game.flash))
                    virtual.blit(flash_surf, (0, 0))
                if game.damage_flash > 0.01:
                    damage_surf.set_alpha(int(90 * game.damage_flash))
                    virtual.blit(damage_surf, (0, 0))

            if L.direct:
                screen.blit(virtual, (0, 0))
            else:
                scaled = pygame.transform.scale(virtual, (L.dw, L.dh))
                sx = sy = 0
                if game.shake > 0.2:
                    sx = int(random.uniform(-game.shake, game.shake))
                    sy = int(random.uniform(-game.shake, game.shake))
                screen.fill((0, 0, 0))
                screen.blit(scaled, (L.ox + sx, L.oy + sy))
        except Exception:
            log_exception(traceback.format_exc())
            try:
                screen.fill((20, 20, 30))
            except Exception:
                pass

        pygame.display.flip()

    try:
        game._save_now()
    except Exception:
        pass
    try:
        music.stop()
    except Exception:
        pass
    pygame.quit()


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except BaseException:
        log_exception(traceback.format_exc())
        try:
            pygame.quit()
        except Exception:
            pass
        sys.exit(1)
