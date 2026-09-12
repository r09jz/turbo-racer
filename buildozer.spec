[app]
title = Turbo Racer
package.name = turboracer
package.domain = com.yourname
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
version = 1.0.0
requirements = python3,pygame
orientation = landscape
fullscreen = 1

[app:android]
android.permissions = VIBRATE
android.api = 31
android.minapi = 24
android.ndk = 25b
android.sdk = 24
android.accept_sdk_license = True
android.archs = arm64-v8a

[buildozer]
log_level = 2
warn_on_root = 1
