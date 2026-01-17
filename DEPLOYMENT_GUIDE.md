# DISC测试应用部署指南

本指南将帮助您将DISC性格测试应用部署到云服务器上，并通过服务器IP地址访问。

## 准备工作

1. 确保您的云服务器已经开通，并且可以通过SSH访问
2. 确保服务器上已安装Python 3.6或更高版本

## 步骤一：在云服务器上安装必要软件

通过SSH连接到您的云服务器，执行以下命令：

```bash
# 更新系统包
sudo apt-get update && sudo apt-get upgrade -y

# 安装Python3、pip和virtualenv
sudo apt-get install python3 python3-pip python3-venv -y

# 安装Nginx作为反向代理
sudo apt-get install nginx -y

# 安装Gunicorn作为WSGI服务器
pip3 install gunicorn
```

## 步骤二：上传项目文件

将项目文件夹上传到云服务器。您可以使用SFTP或scp命令：

```bash
# 在本地计算机上执行
sftp username@your_server_ip
# 或者
scp -r DISCtest username@your_server_ip:/path/to/destination
```

## 步骤三：设置虚拟环境并安装依赖

在云服务器上，导航到项目文件夹并创建虚拟环境：

```bash
cd /path/to/DISCtest

# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 安装项目依赖
pip install -r requirements.txt
pip install gunicorn
```

## 步骤四：配置Gunicorn

创建一个启动脚本，用于运行Gunicorn：

```bash
# 在项目文件夹中创建gunicorn_start.sh文件
nano gunicorn_start.sh
```

将以下内容复制到文件中：

```bash
#!/bin/bash

# 进入项目目录
cd /path/to/DISCtest

# 激活虚拟环境
source venv/bin/activate

# 设置环境变量
export FLASK_APP=app.py
export FLASK_ENV=production
# 请将your_secret_key替换为一个随机字符串
export SECRET_KEY=your_secret_key

# 启动Gunicorn
gunicorn --workers 3 --bind 0.0.0.0:8000 app:app
```

保存文件并添加执行权限：

```bash
chmod +x gunicorn_start.sh
```

## 步骤五：配置Nginx作为反向代理

创建Nginx配置文件：

```bash
sudo nano /etc/nginx/sites-available/disctest
```

将以下内容复制到文件中（替换your_server_ip为您的服务器IP）：

```nginx
server {
    listen 80;
    server_name your_server_ip;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 静态文件配置（如果有的话）
    # location /static {
    #     alias /path/to/DISCtest/static;
    # }
}
```

创建符号链接以启用该站点：

```bash
sudo ln -s /etc/nginx/sites-available/disctest /etc/nginx/sites-enabled
```

测试Nginx配置是否正确：

```bash
sudo nginx -t
```

重启Nginx服务：

```bash
sudo systemctl restart nginx
```

## 步骤六：配置Systemd服务（可选）

为了确保应用在服务器重启后能够自动启动，您可以创建一个Systemd服务文件：

```bash
sudo nano /etc/systemd/system/disctest.service
```

将以下内容复制到文件中（替换相应路径）：

```ini
[Unit]
Description=Gunicorn instance to serve DISC test application
After=network.target

[Service]
User=your_username
Group=www-data
WorkingDirectory=/path/to/DISCtest
Environment="PATH=/path/to/DISCtest/venv/bin"
ExecStart=/path/to/DISCtest/venv/bin/gunicorn --workers 3 --bind 0.0.0.0:8000 app:app

[Install]
WantedBy=multi-user.target
```

启动并启用服务：

```bash
sudo systemctl start disctest
sudo systemctl enable disctest
```

## 步骤七：安全配置

确保服务器防火墙允许HTTP流量：

```bash
sudo ufw allow 'Nginx HTTP'
```

## 步骤八：测试访问

现在，您应该可以通过浏览器访问`http://your_server_ip`来使用DISC测试应用了。

## 注意事项

1. 本应用目前使用内存存储数据，在生产环境中，建议您配置一个数据库（如MySQL或SQLite）来持久化存储用户数据
2. 请确保将app.py中的`app.secret_key`替换为一个强随机字符串，并通过环境变量设置
3. 对于生产环境，建议您配置HTTPS以提高安全性

## 故障排除

如果遇到问题，可以检查以下日志：

- Nginx错误日志：`sudo tail -f /var/log/nginx/error.log`
- Systemd服务日志：`sudo journalctl -u disctest`