import vierzehn
import logging

def main():
    logging.basicConfig(level=logging.DEBUG)
    bot = vierzehn.VierzehnBot(config_path='config.yaml')
    bot.run()

if __name__ == '__main__':
    main()