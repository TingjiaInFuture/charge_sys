import sys
import time
from views.user_client import UserClient
from views.admin_client import AdminClient

def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ['user', 'admin']:
        print("使用方法: python run_client.py [user|admin]")
        print("  user  - 启动用户客户端")
        print("  admin - 启动管理员客户端")
        sys.exit(1)
    
    client_type = sys.argv[1]
    max_retries = 3
    retry_delay = 2  # 秒
    
    for attempt in range(max_retries):
        try:
            if client_type == 'user':
                print("正在启动用户客户端...")
                client = UserClient()
            else:
                print("正在启动管理员客户端...")
                client = AdminClient()
            
            print("客户端启动成功！")
            client.mainloop()
            break
            
        except ConnectionRefusedError:
            if attempt < max_retries - 1:
                print(f"连接服务器失败，{retry_delay}秒后重试...")
                time.sleep(retry_delay)
            else:
                print("无法连接到服务器，请确保服务器已启动。")
                sys.exit(1)
        except Exception as e:
            print(f"客户端启动失败：{str(e)}")
            sys.exit(1)

if __name__ == "__main__":
    main() 