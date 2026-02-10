## Launch an EC2 Instance

1. **Log into AWS Console** - Navigate to the EC2 Dashboard from the Services menu under Compute

2. **Click "Launch Instance"** - Enter a name for your instance (e.g., "my-docker-server")

3. **Choose an AMI** - Select Ubuntu Server 20.04/22.04 LTS

4. **Select Instance Type**- Choose t2.micro or t3.micro for Free Tier eligibility, or select based on your resource needs
​
5. **Configure Key Pair** - Create a new SSH key pair, download the .pem file and save it securely
​
6. **Configure Security Group** - Allow SSH (port 22) for your IP, and add rules for any ports your Docker container will expose (e.g., port 80/443 for web apps)
​
7. **Launch Instance** - Review your configuration and click "Launch Instance"



## Connect to Your EC2 Instance

1. **SSH into your instance using:**
```bash
ssh -i /path/to/your-key.pem ubuntu@your-instance-public-ip
```



2.  **Install Docker on EC2**:
```bash
sudo apt update
sudo apt install docker.io -y
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER
sudo apt install git -y
```

## Clone Your GitHub Repository and Build Docker Image

1. Install Git (if not already installed):
```bash
sudo apt install git -y  # Ubuntu
```

2. Clone your repository:
```bash
git clone https://github.com/omkarbs23/insurance-agent.git
cd insurance-agent
```

3. Add your credentials in the .env file
```bash
nano .env

OPENAI_API_KEY="gl-xxxxxxxxxx"      # Modify this line and add your OpenAI API Key
OPENAI_BASE_URL="https....../v1"    #  Modify this line and add your OpenAI Base URL

CTRL + X
SHIFT + Y
Enter
```

4. Build your Docker image:
```bash
sudo docker build -t insurance-agent-image:latest .
```

5. Check your Docker image:
```bash
sudo docker images insurance-agent-image:latest
```
 
6. Run your Docker image:
```bash
sudo docker run -d -p 80:8501 insurance-agent-image:latest
```

7. Visit your Private IP in any browser