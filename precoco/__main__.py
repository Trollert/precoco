import sys
print(sys.path)
sys.path.append('/precoco')
print(sys.path)
import precoco.startUI as start

if __name__ == '__main__':
    # pass
    start.run()