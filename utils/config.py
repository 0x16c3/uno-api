import configparser, os, secrets

cfgparser = configparser.ConfigParser()

if not os.path.isfile("config.ini"):
    fp = open("config.ini", "w")
    fp.write("[DEFAULT]\n")
    fp.write("; session secret\n")
    fp.write(f"SESSION_SECRET = {secrets.token_hex(nbytes=16)}\n")
    fp.write("; app host\n")
    fp.write(f"APP_HOST = 0.0.0.0\n")
    fp.write("; app port\n")
    fp.write(f"APP_PORT = 8000\n")
    fp.close()

cfgparser.read("config.ini", encoding="utf-8-sig")

