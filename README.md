# vierzehn.py

Vorweg: Ich halte eigentlich nichts von deutschen Readmes, aber welcher Fremdsprachige sollte sonst die Software benutzen wollen?
Dieser Bot wird wirklich von mir __vierzehn.py__ genannt und retweetet Dinge, die typisch für Vierzehnjährige sind.

## Installation
Zunächst sollte man, wenn notwendig, wheel updaten.
```
pip3 install --upgrade wheel
```

### Bot mit Redis (für Statistiken)
Installiere Redis und richte dort in Datenbank 14 die Keys
- bot:rt
- bot:annoyed
- bot:trigger
- bot:argh

ein.

Dann:
```
pip3 install -r requirements.txt
```

### Bot ohne Redis
Wenn das Redis-Modul für Python nicht installiert ist,
wird auch kein Redis verwendet. Verfickt einfach!
```
pip3 install -r requirements.txt
pip3 uninstall redis
```

## Konfiguration
Benenne config.sample.yaml zu config.yaml um. Der Rest sollte selbsterklärend sein.

## Start
```
python3 runscript.py
```


Viel Spaß
~ Martin
