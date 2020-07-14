import sys
print(sys.path)
sys.path.append('/precoco')
print(sys.path)
from precoco.common import UI

if __name__ == '__main__':
    # pass
    UI.run()