import sys
import traceback
from server.charge_server import ChargeServer

def main():
    try:
        print("正在启动充电站服务器...")
        server = ChargeServer()
        print("服务器初始化完成，开始监听连接...")
        server.start()
    except KeyboardInterrupt:
        print("\n服务器正在关闭...")
        sys.exit(0)
    except Exception as e:
        print(f"服务器启动失败：{str(e)}")
        print("详细错误信息：")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 