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

[buildozer]
log_level = 2
warn_on_root = 1

[app:android.arch]
android.archs = arm64-v8a
